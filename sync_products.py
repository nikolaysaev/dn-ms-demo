#!/usr/bin/env python3
"""Sync the demo product database into the CartAssist dashboard.

Reads the large local product export (``json/ProductsDetailsExport.json``) and
uploads it in two phases:

1. ``POST /v1/sync`` — product catalog (embedding + Qdrant + SQL code terms),
   WITHOUT inline appliance rows so payloads stay small.
2. ``POST /v1/sync/compatibility`` — the FULL appliance-fitment data, streamed
   in row batches that never split one product across requests (the dashboard
   replaces fitment per product, so a split product would erase its own rows).

The full export carries ~2.08M fitment rows (a single product can fit 45k+
appliance models). The dashboard stores every row in SQL (``product_fitment``)
and keeps only a capped legacy view in Qdrant.

Field mapping (see TECHNICAL_PARTS_CHATBOT_PLAYBOOK.md §24.13–24.14):

    Id          -> external_id
    Name        -> name        (truncated to 320 chars)
    Description -> description  (truncated to 2500 chars)
    CategoryId  -> categories
    Appliances  -> compatibility   (phase 2; --appliance-limit 0 = ALL rows)

The store **secret** key authenticates the request and is read from ``--key`` or
the ``DN_DEMO_SECRET_KEY`` environment variable. It must never be committed or
placed in any frontend code.

Examples:
    export DN_DEMO_SECRET_KEY='...secret...'
    python3 sync_products.py --limit 3 --batch-size 3        # smoke test
    python3 sync_products.py --batch-size 10                 # full sync
    python3 sync_products.py --compat-only                   # re-stream fitment only
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
COMPAT_ROWS_PER_REQUEST = 5000


def _truncate(value: object, limit: int) -> str:
    text = str(value or "").strip()
    return text[:limit]


def normalize_appliances(rows: object, limit: int = 0) -> list[dict]:
    """Convert source ``Appliances`` rows into dashboard compatibility rows.

    ``limit`` == 0 keeps every row — the dashboard's SQL fitment table is
    uncapped (only its legacy Qdrant view caps per product, server-side)."""
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
        if limit and len(out) >= limit:
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
        # Appliance rows go through /v1/sync/compatibility (phase 2), not inline.
        "compatibility": [],
    }


def _post(url: str, key: str, body: dict, timeout: float) -> dict:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8") or "{}")


def post_batch(api_base: str, key: str, products: list[dict], full_sync: bool, total: int, timeout: float) -> dict:
    return _post(
        api_base.rstrip("/") + "/v1/sync",
        key,
        {"products": products, "full_sync": full_sync, "total_count": total},
        timeout,
    )


def post_compat_batch(api_base: str, key: str, products: list[dict], timeout: float) -> dict:
    # full_sync stays False: /v1/sync already cleared the store's fitment rows
    # (compat_full on the first product batch); True here would erase the
    # previous compatibility batches.
    return _post(
        api_base.rstrip("/") + "/v1/sync/compatibility",
        key,
        {"products": products, "full_sync": False},
        timeout,
    )


def iter_compat_batches(items: list[dict], appliance_limit: int, max_rows: int = COMPAT_ROWS_PER_REQUEST):
    """Yield ``/v1/sync/compatibility`` product batches of ≤ ``max_rows`` fitment
    rows, never splitting one product's rows across two requests."""
    batch: list[dict] = []
    batch_rows = 0
    for item in items:
        product = build_product(item) if isinstance(item, dict) else None
        if not product:
            continue
        appliances = normalize_appliances(item.get("Appliances") or item.get("appliances"), appliance_limit)
        if not appliances:
            continue
        entry = {
            "external_id": product["external_id"],
            "name": product["name"],
            "appliances": appliances,
        }
        if batch and batch_rows + len(appliances) > max_rows:
            yield batch, batch_rows
            batch, batch_rows = [], 0
        batch.append(entry)
        batch_rows += len(appliances)
    if batch:
        yield batch, batch_rows


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", default=DEFAULT_INPUT, help=f"source product export (default: {DEFAULT_INPUT})")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE, help=f"dashboard base URL (default: {DEFAULT_API_BASE})")
    parser.add_argument("--key", default=os.environ.get("DN_DEMO_SECRET_KEY", ""), help="store secret key (or env DN_DEMO_SECRET_KEY)")
    parser.add_argument("--limit", type=int, default=0, help="only sync the first N products (0 = all)")
    parser.add_argument("--batch-size", type=int, default=10, help="products per /v1/sync request (default: 10)")
    parser.add_argument("--appliance-limit", type=int, default=0, help="max fitment rows per product (0 = ALL, default)")
    parser.add_argument("--compat-only", action="store_true", help="skip products, only stream fitment rows")
    parser.add_argument("--skip-compat", action="store_true", help="only sync products, skip fitment rows")
    parser.add_argument("--timeout", type=float, default=180.0, help="per-request timeout in seconds")
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

    items = [item for item in data if isinstance(item, dict)]
    if args.limit > 0:
        items = items[: args.limit]

    # ---- Phase 1: product catalog ----
    if not args.compat_only:
        products = [p for p in (build_product(item) for item in items) if p]
        total = len(products)
        if total == 0:
            print("No valid products to sync.")
            return 0

        synced = 0
        for start in range(0, total, args.batch_size):
            batch = products[start : start + args.batch_size]
            full_sync = start == 0  # first batch resets collection + SQL indexes
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
        print(f"Products done. Synced {synced}/{total}.")

    # ---- Phase 2: full fitment data ----
    if not args.skip_compat:
        sent_rows = 0
        sent_batches = 0
        for batch, rows in iter_compat_batches(items, args.appliance_limit):
            try:
                result = post_compat_batch(args.api_base, args.key, batch, args.timeout)
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", "replace")[:500]
                print(f"\nHTTP {exc.code} on compat batch {sent_batches} ({sent_rows} rows sent): {detail}", file=sys.stderr)
                return 1
            except urllib.error.URLError as exc:
                print(f"\nNetwork error on compat batch {sent_batches} ({sent_rows} rows sent): {exc}", file=sys.stderr)
                return 1
            sent_rows += rows
            sent_batches += 1
            if sent_batches % 10 == 0 or rows >= COMPAT_ROWS_PER_REQUEST:
                print(f"  compat: {sent_rows} rows in {sent_batches} batches "
                      f"(last: sql={result.get('sql_fitment_rows')}, qdrant={result.get('synced')})")
        print(f"Compatibility done. Streamed {sent_rows} fitment rows in {sent_batches} batches.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
