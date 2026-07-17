#!/usr/bin/env python3
"""Sync the demo product database into the CartAssist dashboard.

Reads the local product export (``json/ProductsDetailsExport.json``) and pushes
it to the dashboard's catalog-ingest endpoint:

    POST /v1/ingest    — product catalog (embedding + Qdrant + SQL code terms)

This is the **custom-site catalog push** path (WIDGET.html §5 "Catalog"): a
server-to-server, bearer-authed call. The store's **secret** key authenticates
it (``--key`` or ``DN_DEMO_SECRET_KEY``) and must never be committed or placed
in any frontend code — the widget itself carries no secret.

Field mapping — the push (source) shape the dashboard's default OpenCart-push
mapping expects (``dn_adapters.strategies.catalog_push.OPENCART_PUSH_MAPPING``,
which maps source → the canonical CatalogItem):

    Id          -> external_id
    Name        -> name         (truncated to 320 chars)
    Description -> description  (truncated to 2500 chars)
    CategoryId  -> categories

COMPATIBILITY / FITMENT IS **PARKED** — it is deliberately NOT pushed here.
The old dashboard had a second phase (``POST /v1/sync/compatibility``) that
streamed the export's ~2.08M appliance-fitment rows. The rebuilt dashboard has
**no such endpoint**: compatibility ingestion is an open design question and the
parser/mapping + retrieval layer is a documented scaffold (see the dashboard's
CLAUDE.md "Parked" section and docs/COMPATIBILITY.html). ``POST /v1/ingest``
tolerates inline ``compatibility`` on a product but only COUNTS it and reports
it back as ``skipped_compatibility`` — the rows are never indexed. So this
script sends products only; pushing appliance rows would just inflate payloads
for data the server discards. The old phase-2 streamer lives in this repo's git
history if/when compatibility is unparked.

Examples:
    export DN_DEMO_SECRET_KEY='...secret...'
    python3 sync_products.py --api-base http://127.0.0.1:8002 --limit 3 --batch-size 3   # smoke test
    python3 sync_products.py --batch-size 10                                             # full sync
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


def _truncate(value: object, limit: int) -> str:
    text = str(value or "").strip()
    return text[:limit]


def build_product(item: dict) -> dict | None:
    """One export row → one push product, or ``None`` to skip it.

    The dashboard requires an integer-castable product id (it keys the Qdrant
    point on it), so a non-numeric ``Id`` is skipped here rather than rejected
    server-side. Appliance rows are intentionally not included — see the module
    docstring (compatibility ingestion is parked).
    """
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
    """POST one product batch to ``/v1/ingest`` (the plugin/push surface).

    ``full_sync=True`` on the first batch resets the store's collection + SQL
    indexes; later batches append.
    """
    return _post(
        api_base.rstrip("/") + "/v1/ingest",
        key,
        {"products": products, "full_sync": full_sync, "total_count": total},
        timeout,
    )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", default=DEFAULT_INPUT, help=f"source product export (default: {DEFAULT_INPUT})")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE, help=f"dashboard base URL (default: {DEFAULT_API_BASE})")
    parser.add_argument("--key", default=os.environ.get("DN_DEMO_SECRET_KEY", ""), help="store secret key (or env DN_DEMO_SECRET_KEY)")
    parser.add_argument("--limit", type=int, default=0, help="only sync the first N products (0 = all)")
    parser.add_argument("--batch-size", type=int, default=10, help="products per /v1/ingest request (default: 10)")
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

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
