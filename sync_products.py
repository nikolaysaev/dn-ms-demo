#!/usr/bin/env python3
"""Sync the demo product database into the CartAssist dashboard.

Reads the large local product export (``json/ProductsDetailsExport.json``) and
converts each record into the dashboard ``POST /v1/sync`` payload shape, then
uploads it in batches.

Field mapping (see TECHNICAL_PARTS_CHATBOT_PLAYBOOK.md §24.13–24.14):

    Id          -> external_id
    Name        -> name        (truncated to 320 chars)
    Description -> description  (truncated to 2500 chars)
    CategoryId  -> categories
    Appliances  -> compatibility   (capped at 80 rows per product)

The store **secret** key authenticates the request and is read from ``--key`` or
the ``DN_DEMO_SECRET_KEY`` environment variable. It must never be committed or
placed in any frontend code.

Examples:
    export DN_DEMO_SECRET_KEY='...secret...'
    python3 sync_products.py --limit 3 --batch-size 3        # smoke test
    python3 sync_products.py --batch-size 10                 # full sync
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_INPUT = "json/ProductsDetailsExport.json"
DEFAULT_API_BASE = "https://dashboard.cartassist.shop"
NAME_LIMIT = 320
DESCRIPTION_LIMIT = 2500
APPLIANCE_LIMIT = 80


def _truncate(value: object, limit: int) -> str:
    text = str(value or "").strip()
    return text[:limit]


def normalize_appliances(rows: object, limit: int = APPLIANCE_LIMIT) -> list[dict]:
    """Convert source ``Appliances`` rows into dashboard compatibility rows.

    Capped at ``limit`` rows so products with thousands of compatible models do
    not produce an oversized sync payload (playbook §24.14)."""
    out: list[dict] = []
    if not isinstance(rows, list):
        return out
    for row in rows:
        if not isinstance(row, dict):
            continue
        brand = str(row.get("Brand") or row.get("brand") or "").strip()
        code = str(row.get("Code") or row.get("code") or "").strip()
        serial = str(row.get("SerialNumber") or row.get("serialNumber") or "").strip()
        if not (brand or code or serial):
            continue
        out.append({"brand": brand, "code": code, "serialNumber": serial})
        if len(out) >= limit:
            break
    return out


def build_product(item: dict) -> dict | None:
    external_id = item.get("Id") or item.get("id") or item.get("product_id")
    if external_id in (None, ""):
        return None
    try:
        int(external_id)
    except (TypeError, ValueError):
        return None

    category_id = item.get("CategoryId") or item.get("category_id")
    categories = [str(category_id)] if category_id not in (None, "") else []

    return {
        "external_id": str(external_id),
        "name": _truncate(item.get("Name") or item.get("name"), NAME_LIMIT),
        "description": _truncate(item.get("Description") or item.get("description"), DESCRIPTION_LIMIT),
        "categories": categories,
        "compatibility": normalize_appliances(item.get("Appliances") or item.get("appliances")),
    }


def post_batch(api_base: str, key: str, products: list[dict], full_sync: bool, total: int, timeout: float) -> dict:
    url = api_base.rstrip("/") + "/v1/sync"
    body = json.dumps(
        {"products": products, "full_sync": full_sync, "total_count": total},
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8") or "{}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", default=DEFAULT_INPUT, help=f"source product export (default: {DEFAULT_INPUT})")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE, help=f"dashboard base URL (default: {DEFAULT_API_BASE})")
    parser.add_argument("--key", default=os.environ.get("DN_DEMO_SECRET_KEY", ""), help="store secret key (or env DN_DEMO_SECRET_KEY)")
    parser.add_argument("--limit", type=int, default=0, help="only sync the first N products (0 = all)")
    parser.add_argument("--batch-size", type=int, default=10, help="products per request (default: 10)")
    parser.add_argument("--timeout", type=float, default=120.0, help="per-request timeout in seconds")
    args = parser.parse_args(argv)

    if not args.key:
        print("Missing store secret key. Pass --key or set DN_DEMO_SECRET_KEY.", file=sys.stderr)
        return 2

    src = Path(args.input)
    if not src.exists():
        print(f"Input file not found: {src}", file=sys.stderr)
        return 2

    with src.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        print("Expected the product export to be a JSON array.", file=sys.stderr)
        return 2

    products = [p for p in (build_product(item) for item in data if isinstance(item, dict)) if p]
    if args.limit > 0:
        products = products[: args.limit]

    total = len(products)
    if total == 0:
        print("No valid products to sync.")
        return 0

    synced = 0
    for start in range(0, total, args.batch_size):
        batch = products[start : start + args.batch_size]
        full_sync = start == 0  # first batch resets the collection
        try:
            result = post_batch(args.api_base, args.key, batch, full_sync, total, args.timeout)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:500]
            print(f"\nHTTP {exc.code} on batch starting at {start}: {detail}", file=sys.stderr)
            return 1
        except urllib.error.URLError as exc:
            print(f"\nNetwork error on batch starting at {start}: {exc}", file=sys.stderr)
            return 1
        synced += int(result.get("synced", len(batch)))
        print(f"  synced {min(start + len(batch), total)}/{total} (last response: {result.get('message', 'ok')})")

    print(f"Done. Synced {synced}/{total} products.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
