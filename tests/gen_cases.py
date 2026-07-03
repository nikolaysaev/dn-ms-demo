#!/usr/bin/env python3
"""Generate chatbot test cases from ground truth.

For every category produces:
  * browse queries     -> "do you carry <subcategory>?"
  * product-name query -> the human-readable part of a real product name
  * product-code query  -> the OEM / article number of a real product

Writes tests/out/cases.jsonl. Each line:
  {case_id, type, cat_id, parent, subcat, is_tool, query,
   expect_cat, expect_product_id}
"""
import json
import re
import sys
from pathlib import Path

OUTDIR = Path(__file__).resolve().parent / "out"
GT = OUTDIR / "groundtruth.json"
CASES = OUTDIR / "cases.jsonl"

PRODUCTS_PER_CAT = int(sys.argv[1]) if len(sys.argv) > 1 else 4

BROWSE_TEMPLATES = [
    "Търся {x}",
    "Имате ли {x}?",
]


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def split_name(name: str):
    """-> (descriptive_part, [codes])."""
    parts = [clean(p) for p in name.split("|")]
    desc = parts[0]
    codes = []
    for seg in parts[1:]:
        # a segment may itself contain several comma-separated codes
        for c in re.split(r"[,/]", seg):
            c = clean(c)
            if len(c) >= 5 and re.search(r"\d", c) and " " not in c:
                codes.append(c)
    return desc, codes


def sample_indices(n, k):
    """Evenly spread k indices across range(n)."""
    if n <= k:
        return list(range(n))
    step = n / k
    return sorted({int(i * step) for i in range(k)})


def main():
    gt = json.loads(GT.read_text(encoding="utf-8"))
    cats = gt["categories"]
    products = gt["products"]

    cases = []
    cid_counter = 0

    def add(**kw):
        nonlocal cid_counter
        cid_counter += 1
        kw["case_id"] = f"c{cid_counter:04d}"
        cases.append(kw)

    for cat_id, meta in cats.items():
        cat_id_i = int(cat_id)
        base = dict(cat_id=cat_id_i, parent=meta["parent"],
                    subcat=meta["subcat"], is_tool=meta["is_tool"])
        # browse
        for tpl in BROWSE_TEMPLATES:
            add(type="browse", query=tpl.format(x=meta["subcat"]),
                expect_cat=cat_id_i, expect_product_id=None, **base)
        # products
        ids = meta["product_ids"]
        for idx in sample_indices(len(ids), PRODUCTS_PER_CAT):
            pid = ids[idx]
            name = products.get(str(pid), {}).get("name", "")
            if not name:
                continue
            desc, codes = split_name(name)
            if desc:
                add(type="product_name", query=desc, expect_cat=cat_id_i,
                    expect_product_id=pid, **base)
            if codes:
                add(type="product_code", query=codes[0], expect_cat=cat_id_i,
                    expect_product_id=pid, **base)

    with CASES.open("w", encoding="utf-8") as f:
        for c in cases:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    by_type = {}
    for c in cases:
        by_type[c["type"]] = by_type.get(c["type"], 0) + 1
    print(f"Wrote {len(cases)} cases -> {CASES}", file=sys.stderr)
    for t, n in sorted(by_type.items()):
        print(f"  {t}: {n}", file=sys.stderr)


if __name__ == "__main__":
    main()
