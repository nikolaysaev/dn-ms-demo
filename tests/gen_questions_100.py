#!/usr/bin/env python3
"""Generate 100 Bulgarian test questions per category from the real catalog.

Inputs:  tests/out/groundtruth.json  (built by build_groundtruth.py from
         json/ProductsDetailsExport.json + json/products_category_analysis.md)
Outputs: tests/out/questions_100_per_category.json  (machine)
         tests/out/questions_100_per_category.csv   (human / spreadsheet)

Question templates mirror the intents observed in the merchant's LiveChat export
(142k customer messages): search for a specific part, availability, price,
code check, model compatibility, dimensions/specs, original-vs-substitute,
delivery-with-product, photo offer. Deterministic (seeded) and deduplicated.
"""
from __future__ import annotations

import csv
import json
import random
import re
from pathlib import Path

HERE = Path(__file__).parent
GT_PATH = HERE / "out" / "groundtruth.json"
OUT_JSON = HERE / "out" / "questions_100_per_category.json"
OUT_CSV = HERE / "out" / "questions_100_per_category.csv"
PER_CATEGORY = 100

# ---------------- name parsing helpers ----------------

# Second word letters-only, so "ARISTON MERLONI" matches but a trailing model
# token ("REFCO ECO-3-A2L") doesn't get glued onto the brand.
_BRAND_RX = re.compile(r"\b([A-Z][A-Z&.]{2,}(?:\s+[A-Z][A-Z&.]{2,})?)\b")
_BRAND_STOP = {
    "LED", "USB", "LCD", "PVC", "INOX", "EUR", "BGN", "OEM", "PNC", "HP",
    "EDP", "EDT", "II", "III", "PRO", "MAX", "MINI", "PLUS", "SET",
}


def split_name(raw: str) -> tuple[str, str]:
    """'Помпа за пералня BOSCH | 00140268' -> (clean name, code)."""
    parts = [p.strip() for p in raw.split("|")]
    name = parts[0]
    code = parts[1] if len(parts) > 1 and parts[1] else ""
    return name, code


def extract_brand(name: str) -> str:
    for m in _BRAND_RX.finditer(name):
        tok = m.group(1)
        if tok not in _BRAND_STOP and not tok.replace("-", "").replace(".", "").isdigit():
            return tok
    return ""


def extract_dim(name: str) -> str:
    m = re.search(r"(?:[φфØ]\s?\d+(?:[.,]\d+)?\s*(?:мм|mm)?|\d+\s?[xх×]\s?\d+\s*(?:мм|mm)?|\d+\s*(?:мм|mm)\b|\d+/\d+\"|\d+\s?W\b|\d+\s?V\b|\d+\s?N\b)", name)
    return m.group(0).strip() if m else ""


# ---------------- templates ----------------
# {n}=product name, {c}=code, {b}=brand, {cat}=subcategory, {parent}=parent
# category, {d}=dimension token. A template is only used when all of its
# placeholders resolve to non-empty values for the chosen product.

T_PRODUCT = [  # need {n}
    "Търся {n}",
    "Имате ли {n}?",
    "Здравейте, търся {n}",
    "Наличен ли е {n}?",
    "Каква е цената на {n}?",
    "Колко струва {n}?",
    "Здравейте, имате ли налично {n}?",
    "Може ли линк към {n}?",
    "Има ли наличност от {n}?",
    "Интересува ме {n} — цена и доставка?",
    "Оригинална част ли е {n}?",
    "{n} — оригинал или заместител е?",
    "До колко време доставяте {n}?",
    "Може ли да поръчам {n} с наложен платеж?",
    "Изпращате ли {n} с Еконт?",
    "Има ли гаранция {n}?",
]

T_CODE = [  # need {c}
    "Имате ли част с код {c}?",
    "Търся {c}",
    "Проверете код {c}, моля",
    "Наличност на код {c}?",
    "Каква е цената на артикул {c}?",
    "Здравейте, търся част номер {c}",
    "Код {c} — има ли го?",
    "Може ли информация за {c}?",
]

T_NAME_CODE = [  # need {n} and {c}
    "Търся {n} с код {c}",
    "{n} ({c}) — наличен ли е?",
    "Здравейте, {n}, код {c} — каква е цената?",
]

T_BRAND_CAT = [  # need {b} and {cat}
    "Имате ли {cat} за {b}?",
    "Търся {cat} {b}",
    "Какви {cat} имате за {b}?",
    "Предлагате ли {cat} на {b}?",
]

T_CAT = [  # need {cat}
    "Имате ли {cat}?",
    "Търся {cat}",
    "Какви {cat} предлагате?",
    "Покажете ми {cat}",
    "Здравейте, интересуват ме {cat}",
    "Може ли да видя наличните {cat}?",
    "Кои са най-евтините {cat}?",
    "Каква е цената на {cat}?",
    "Има ли промоция на {cat}?",
    "Кой е най-продаваният артикул от {cat}?",
]

T_DIM = [  # need {n} and {d}
    "Търся {n} — важно е да е {d}",
    "Имате ли подобна част с размер {d}? Като {n}",
    "Какви са размерите на {n}?",
]

T_COMPAT = [  # need {n}
    "Съвместим ли е {n} с моя уред?",
    "За кои модели става {n}?",
    "Може ли да проверите дали {n} е подходящ за моя модел?",
]

T_PHOTO = [  # need {cat}
    "Имам снимка на старата част — търся {cat}",
    "Мога да пратя снимка на стикера, трябват ми {cat}",
]


def gen_for_category(cat_id: str, meta: dict, products: dict, rng: random.Random) -> list[dict]:
    cat = meta["subcat"]
    parent = meta.get("parent") or ""
    pids = [str(p) for p in meta.get("product_ids", []) if str(p) in products]
    rng.shuffle(pids)

    parsed = []
    for pid in pids:
        raw = products[pid]["name"]
        name, code = split_name(raw)
        parsed.append({
            "pid": pid, "name": name, "code": code,
            "brand": extract_brand(name), "dim": extract_dim(name),
        })

    out: list[dict] = []
    seen: set[str] = set()

    def add(q: str, intent: str, pid: str = "") -> None:
        q = re.sub(r"\s+", " ", q).strip()
        key = q.lower()
        if key in seen or len(out) >= PER_CATEGORY:
            return
        seen.add(key)
        out.append({"question": q, "intent": intent, "product_id": pid or None})

    # 1) category-level questions first (always available)
    for t in T_CAT:
        add(t.format(cat=cat.lower()), "browse")
    for t in T_PHOTO:
        add(t.format(cat=cat.lower()), "photo")

    # 2) brand × category — capped so brand paraphrases can't crowd out the
    #    product/code/compatibility questions below
    brands = list(dict.fromkeys(p["brand"] for p in parsed if p["brand"]))[:8]
    for i, b in enumerate(brands):
        for t in T_BRAND_CAT[: 2 if i >= 4 else 4]:
            add(t.format(b=b, cat=cat.lower()), "brand_browse")
            if len(out) >= PER_CATEGORY:
                return out

    # 3) per-product questions, round-robin over template groups so every
    #    product contributes before any template repeats
    groups = [
        (T_PRODUCT, ("name",), "product"),
        (T_CODE, ("code",), "code"),
        (T_NAME_CODE, ("name", "code"), "product_code"),
        (T_COMPAT, ("name",), "compatibility"),
        (T_DIM, ("name", "dim"), "dimensions"),
    ]
    ti = {id(g[0]): 0 for g in groups}
    for round_no in range(60):
        progressed = False
        for p in parsed:
            for templates, needs, intent in groups:
                if len(out) >= PER_CATEGORY:
                    return out
                idx = ti[id(templates)]
                t = templates[(idx + round_no) % len(templates)]
                vals = {"n": p["name"], "c": p["code"], "b": p["brand"],
                        "d": p["dim"], "cat": cat.lower(), "parent": parent.lower()}
                if any(not vals[{"name": "n", "code": "c", "dim": "d"}[k]] for k in needs):
                    continue
                before = len(out)
                add(t.format(**vals), intent, p["pid"])
                progressed = progressed or len(out) > before
        if not progressed:
            break

    # 4) pad with numbered paraphrases only if combinatorics ran dry
    i = 0
    while len(out) < PER_CATEGORY and parsed:
        p = parsed[i % len(parsed)]
        add(f"Здравейте, отново за {p['name']} — все още ли е наличен?", "product", p["pid"])
        add(f"Може ли оферта за {p['name']}?", "product", p["pid"])
        i += 1
        if i > PER_CATEGORY * 3:
            break
    return out


def main() -> None:
    gt = json.loads(GT_PATH.read_text(encoding="utf-8"))
    cats, products = gt["categories"], gt["products"]
    rng = random.Random(42)

    result = {}
    rows = []
    for cat_id in sorted(cats, key=int):
        meta = cats[cat_id]
        qs = gen_for_category(cat_id, meta, products, rng)
        result[cat_id] = {
            "category": meta["subcat"],
            "parent": meta.get("parent") or "",
            "is_tool": meta.get("is_tool", False),
            "n_questions": len(qs),
            "questions": qs,
        }
        for q in qs:
            rows.append([cat_id, meta.get("parent") or "", meta["subcat"],
                         q["intent"], q["product_id"] or "", q["question"]])

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    with OUT_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["category_id", "parent", "category", "intent", "product_id", "question"])
        w.writerows(rows)

    full = sum(1 for v in result.values() if v["n_questions"] == PER_CATEGORY)
    print(f"categories: {len(result)} · questions: {len(rows)} · full-100: {full}")
    short = [(cid, v['category'], v['n_questions']) for cid, v in result.items() if v['n_questions'] < PER_CATEGORY]
    for cid, name, n in short:
        print(f"  short: {cid} {name} -> {n}")


if __name__ == "__main__":
    main()
