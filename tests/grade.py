#!/usr/bin/env python3
"""Grade chatbot test results and write a mistake report.

Reads tests/out/results.jsonl + groundtruth.json, writes:
  * tests/out/results_graded.csv  — one row per case with outcome + flags
  * tests/out/report.md           — human-readable summary of where the bot errs

Outcomes per case:
  EXACT   product case: the expected product id was returned
  CAT_OK  returned product(s) from the correct category (no exact, or browse)
  OFF_CAT returned products but none from the expected category
  GATED   bot demanded an appliance model/OEM instead of answering
  EMPTY   no products and no gate
  ERROR   request failed

Mistake flags (the interesting failures):
  tool_gated  a standalone TOOL query was blocked by the appliance-model gate
  empty       a query built from a real catalogue product returned nothing
  off_cat     returned only products from the wrong category
  code_nohit  an OEM/article-code lookup did not surface its exact product
"""
import csv
import json
from collections import defaultdict
from pathlib import Path

OUTDIR = Path(__file__).resolve().parent / "out"
GT = OUTDIR / "groundtruth.json"
RESULTS = OUTDIR / "results.jsonl"
CSV_OUT = OUTDIR / "results_graded.csv"
MD_OUT = OUTDIR / "report.md"


def load_results():
    seen = {}
    for l in RESULTS.read_text(encoding="utf-8").splitlines():
        if not l.strip():
            continue
        d = json.loads(l)
        seen[d["case_id"]] = d  # last write wins (resume-safe)
    return list(seen.values())


def grade(r, products):
    if r.get("error"):
        return "ERROR", {}
    picked = r.get("picked_ids") or []
    picked_cats = [products.get(str(p), {}).get("cat") for p in picked]
    expect_cat = r.get("expect_cat")
    expect_pid = r.get("expect_product_id")
    any_cat = any(c == expect_cat for c in picked_cats)
    exact = expect_pid is not None and expect_pid in picked

    if r.get("n_picked", 0) == 0:
        outcome = "GATED" if r.get("gated") else "EMPTY"
    elif r["type"].startswith("product") and exact:
        outcome = "EXACT"
    elif any_cat:
        outcome = "CAT_OK"
    else:
        outcome = "OFF_CAT"

    flags = {
        "tool_gated": bool(r.get("is_tool") and outcome == "GATED"),
        "empty": outcome == "EMPTY",
        "off_cat": outcome == "OFF_CAT",
        "code_nohit": r["type"] == "product_code" and not exact,
    }
    return outcome, flags


def main():
    gt = json.loads(GT.read_text(encoding="utf-8"))
    products = gt["products"]
    cats = gt["categories"]
    results = load_results()

    rows = []
    for r in results:
        outcome, flags = grade(r, products)
        rows.append({**r, "outcome": outcome, **{f"flag_{k}": v for k, v in flags.items()}})

    # ---- CSV ----
    cols = ["case_id", "type", "parent", "subcat", "cat_id", "is_tool", "query",
            "outcome", "n_picked", "gated", "severity", "confidence",
            "expect_product_id", "picked_ids",
            "flag_tool_gated", "flag_empty", "flag_off_cat", "flag_code_nohit"]
    with CSV_OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({**r, "picked_ids": json.dumps(r.get("picked_ids"), ensure_ascii=False)})

    # ---- aggregates ----
    n = len(rows)
    by_outcome = defaultdict(int)
    by_type_outcome = defaultdict(lambda: defaultdict(int))
    for r in rows:
        by_outcome[r["outcome"]] += 1
        by_type_outcome[r["type"]][r["outcome"]] += 1

    # per-category mistake tally
    cat_stats = defaultdict(lambda: {"n": 0, "tool_gated": 0, "empty": 0, "off_cat": 0,
                                     "code_nohit": 0, "is_tool": False, "subcat": "", "parent": ""})
    for r in rows:
        cid = str(r["cat_id"])
        s = cat_stats[cid]
        s["n"] += 1
        s["is_tool"] = r["is_tool"]
        s["subcat"] = r["subcat"]
        s["parent"] = r["parent"]
        for fl in ("tool_gated", "empty", "off_cat", "code_nohit"):
            if r.get(f"flag_{fl}"):
                s[fl] += 1

    def section(title, predicate, fields):
        lines = [f"\n## {title}\n"]
        hits = [r for r in rows if predicate(r)]
        if not hits:
            lines.append("_None._\n")
            return "\n".join(lines), 0
        lines.append("| Category | Type | Query | Outcome | n | Picked |")
        lines.append("|---|---|---|---|--:|---|")
        for r in sorted(hits, key=lambda x: (x["parent"], x["subcat"]))[:120]:
            picked = ", ".join(str(p) for p in (r.get("picked_ids") or [])[:4]) or "—"
            q = r["query"].replace("|", "/")[:55]
            lines.append(f"| {r['subcat'][:28]} | {r['type'].replace('product_','p_')} | {q} | {r['outcome']} | {r['n_picked']} | {picked} |")
        if len(hits) > 120:
            lines.append(f"\n_…and {len(hits)-120} more (see results_graded.csv)._")
        return "\n".join(lines), len(hits)

    md = []
    md.append("# apogee99 chatbot — test report\n")
    md.append(f"Store 4 · local stack (dashboard :8002 → core :8001) · **{n} test cases**\n")
    md.append("Cases are generated from the real catalogue: browse queries per "
              "subcategory plus product-name and OEM-code lookups for sampled products.\n")

    md.append("## Outcome summary\n")
    md.append("| Outcome | Count | % |")
    md.append("|---|--:|--:|")
    for o in ["EXACT", "CAT_OK", "OFF_CAT", "GATED", "EMPTY", "ERROR"]:
        c = by_outcome.get(o, 0)
        md.append(f"| {o} | {c} | {100*c/n:.0f}% |")

    md.append("\n## By query type\n")
    md.append("| Type | EXACT | CAT_OK | OFF_CAT | GATED | EMPTY | ERROR |")
    md.append("|---|--:|--:|--:|--:|--:|--:|")
    for t in sorted(by_type_outcome):
        d = by_type_outcome[t]
        md.append(f"| {t} | " + " | ".join(str(d.get(o, 0)) for o in
                  ["EXACT", "CAT_OK", "OFF_CAT", "GATED", "EMPTY", "ERROR"]) + " |")

    # mistake sections
    s1, n1 = section("🔴 Tool queries blocked by the appliance-model gate",
                     lambda r: r["flag_tool_gated"], None)
    s2, n2 = section("🟠 Existing-product queries that returned nothing (EMPTY)",
                     lambda r: r["flag_empty"], None)
    s3, n3 = section("🟡 Off-category results (returned wrong-category products)",
                     lambda r: r["flag_off_cat"], None)

    md.append(f"\n## Mistake counts\n")
    md.append(f"- 🔴 tool gated: **{n1}**")
    md.append(f"- 🟠 empty for real product: **{n2}**")
    md.append(f"- 🟡 off-category: **{n3}**")
    code_total = sum(1 for r in rows if r["type"] == "product_code")
    code_nohit = sum(1 for r in rows if r.get("flag_code_nohit"))
    if code_total:
        md.append(f"- OEM-code lookups not returning their exact product: **{code_nohit}/{code_total}** "
                  f"({100*code_nohit/code_total:.0f}%)")

    # worst categories
    md.append("\n## Worst categories (by mistake count)\n")
    md.append("| Category | Tool? | cases | tool_gated | empty | off_cat | code_nohit |")
    md.append("|---|:-:|--:|--:|--:|--:|--:|")
    ranked = sorted(cat_stats.values(),
                    key=lambda s: -(s["tool_gated"] + s["empty"] + s["off_cat"]))
    for s in ranked:
        tot = s["tool_gated"] + s["empty"] + s["off_cat"]
        if tot == 0:
            continue
        md.append(f"| {s['subcat'][:30]} | {'T' if s['is_tool'] else 'P'} | {s['n']} | "
                  f"{s['tool_gated']} | {s['empty']} | {s['off_cat']} | {s['code_nohit']} |")

    md.append(s1)
    md.append(s2)
    md.append(s3)

    MD_OUT.write_text("\n".join(md), encoding="utf-8")
    print(f"Graded {n} results.")
    print(f"  outcomes: {dict(by_outcome)}")
    print(f"  mistakes: tool_gated={n1} empty={n2} off_cat={n3} code_nohit={code_nohit}/{code_total}")
    print(f"  wrote {CSV_OUT}")
    print(f"  wrote {MD_OUT}")


if __name__ == "__main__":
    main()
