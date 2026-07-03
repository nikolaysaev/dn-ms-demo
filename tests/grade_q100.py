#!/usr/bin/env python3
"""Grade q100 piece results. Usage: grade_q100.py <results.jsonl>"""
import json, sys
from collections import Counter, defaultdict
from pathlib import Path

OUT = Path(__file__).parent / "out"
gt = json.loads((OUT / "groundtruth.json").read_text())
pid2cat = {int(pid): int(v["cat"]) for pid, v in gt["products"].items()}

def grade(r):
    intent = r.get("type")
    picked = [int(p) for p in (r.get("picked_ids") or []) if p is not None]
    text = r.get("text") or ""
    if r.get("error"):
        return "ERROR"
    if r.get("gated"):
        return "GATED"
    if intent == "photo":
        return "PHOTO_OK" if ("прикачи" in text or "📎" in text or "снимката помага" in text) else ("OFF_INTENT" if picked else "EMPTY")
    exp_pid, exp_cat = r.get("expect_product_id"), r.get("expect_cat")
    if not picked:
        return "EMPTY"
    if exp_pid and exp_pid in picked:
        return "EXACT"
    if exp_cat and any(pid2cat.get(p) == exp_cat for p in picked):
        return "CAT_OK"
    return "OFF_CAT"

rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8") if l.strip()]
by_intent = defaultdict(Counter)
total = Counter()
compat_reasoned = [0, 0]
for r in rows:
    g = grade(r)
    by_intent[r.get("type")][g] += 1
    total[g] += 1
    if r.get("type") == "compatibility":
        compat_reasoned[1] += 1
        if "Подробен анализ" in (r.get("text") or ""):
            compat_reasoned[0] += 1

GOOD = {"EXACT", "CAT_OK", "PHOTO_OK"}
n = len(rows)
good = sum(total[g] for g in GOOD)
print(f"graded {n} results · GOOD {good} ({100*good/n:.1f}%)")
print(f"overall: {dict(total)}")
print(f"compatibility answers with reasoning card: {compat_reasoned[0]}/{compat_reasoned[1]}")
print()
for intent in sorted(by_intent):
    c = by_intent[intent]
    m = sum(c.values())
    g = sum(c[x] for x in GOOD)
    print(f"{intent:14s} n={m:4d} good={100*g/m:5.1f}%  {dict(c)}")
