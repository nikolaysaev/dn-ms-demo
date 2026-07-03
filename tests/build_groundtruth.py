#!/usr/bin/env python3
"""Build ground-truth lookups for the apogee99 chatbot test harness.

Outputs tests/out/groundtruth.json:
  {
    "categories": { "<cat_id>": {
        "parent": str, "subcat": str, "is_tool": bool,
        "n_products": int, "product_ids": [int, ...] } },
    "products":   { "<id>": {"cat": int, "name": str} }
  }

Category metadata (parent + inferred subcategory names) comes from the
human-curated index table in json/products_category_analysis.md. The
authoritative id->category mapping and product names come from the full
json/ProductsDetailsExport.json export.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "json" / "products_category_analysis.md"
EXPORT = ROOT / "json" / "ProductsDetailsExport.json"
OUT = Path(__file__).resolve().parent / "out" / "groundtruth.json"

# Parent categories that are genuine appliance spare parts, where asking for an
# appliance model / OEM number is a legitimate compatibility flow. Everything
# else is a standalone tool/instrument, where demanding an appliance model is a bug.
SPARE_PART_PARENT = "Резервни части за перални"


def parse_category_table():
    """Parse the markdown index table -> {cat_id: {parent, subcat}}."""
    cats = {}
    row = re.compile(r"^\|\s*(.+?)\s*\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(\d+)\s*\|\s*$")
    for line in ANALYSIS.read_text(encoding="utf-8").splitlines():
        m = row.match(line)
        if not m:
            continue
        parent, cat_id, subcat, _n = m.groups()
        if parent.lower().startswith("category"):  # header row
            continue
        cats[int(cat_id)] = {
            "parent": parent,
            "subcat": subcat,
            "is_tool": parent != SPARE_PART_PARENT,
        }
    return cats


def main():
    cats = parse_category_table()
    print(f"Parsed {len(cats)} categories from analysis table", file=sys.stderr)

    print("Loading full product export (this is ~150MB)...", file=sys.stderr)
    data = json.loads(EXPORT.read_text(encoding="utf-8"))
    print(f"Loaded {len(data)} products", file=sys.stderr)

    products = {}
    by_cat = {cid: [] for cid in cats}
    for p in data:
        pid = p.get("Id")
        cid = p.get("CategoryId")
        if pid is None:
            continue
        products[str(pid)] = {"cat": cid, "name": p.get("Name") or ""}
        if cid in by_cat:
            by_cat[cid].append(pid)

    out_cats = {}
    for cid, meta in cats.items():
        ids = by_cat.get(cid, [])
        out_cats[str(cid)] = {
            **meta,
            "n_products": len(ids),
            "product_ids": ids,
        }

    OUT.write_text(json.dumps(
        {"categories": out_cats, "products": products}, ensure_ascii=False), encoding="utf-8")
    n_tool = sum(1 for c in out_cats.values() if c["is_tool"])
    print(f"Wrote {OUT}", file=sys.stderr)
    print(f"  {len(out_cats)} categories ({n_tool} tool, {len(out_cats)-n_tool} spare-part)", file=sys.stderr)
    print(f"  {len(products)} products mapped", file=sys.stderr)


if __name__ == "__main__":
    main()
