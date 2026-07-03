#!/usr/bin/env python3
"""Match catalog products to real customer questions from the LiveChat export."""

from __future__ import annotations

import csv
import gc
import glob
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PRODUCTS_PATH = ROOT / "json" / "ProductsDetailsExport.json"
CHATS_PATH = ROOT / "json" / "LiveChat all.json"
QUESTION_GLOB = str(ROOT / "json" / "livechat_customer_questions_chunks" / "part_*.md")
CSV_PATH = ROOT / "json" / "product_livechat_questions.csv"
REPORT_PATH = ROOT / "json" / "product_livechat_analysis.md"
QUESTIONS_MD_PATH = ROOT / "json" / "product_livechat_questions.md"

QUESTION_RE = re.compile(
    r"^\d+\.\s+`(?P<date>[^`]+)`\s+`(?P<chat>[^`]+)`\s+"
    r"`(?P<theme>[^`]+)`\s+-\s+(?P<question>.*)$"
)
PRODUCT_URL_RE = re.compile(
    r"(?:/p/|[?&]products_id=)(\d+)(?:[/?&#]|$)", re.IGNORECASE
)
TOKEN_RE = re.compile(r"[0-9A-ZА-Я]+", re.IGNORECASE)
REFRIGERANT_RE = re.compile(r"R\d{2,4}[A-Z]*", re.IGNORECASE)


def compact(value: str) -> str:
    return "".join(TOKEN_RE.findall(value.upper()))


def extract_product_codes(name: str) -> list[str]:
    if "|" not in name:
        return []
    tail = name.rsplit("|", 1)[1].strip()
    codes = []
    for value in re.split(r"[,;]", tail):
        value = value.strip()
        if " - " in value:
            value = value.split(" - ", 1)[0].strip()
        normalized = compact(value)
        if (
            len(normalized) >= 5
            and any(ch.isdigit() for ch in normalized)
            and not REFRIGERANT_RE.fullmatch(normalized)
        ):
            codes.append(value)
    return codes


def load_products() -> tuple[dict[int, dict], dict[str, set[int]], dict[str, int]]:
    with PRODUCTS_PATH.open(encoding="utf-8") as handle:
        raw_products = json.load(handle)

    source_records = len(raw_products)
    products: dict[int, dict] = {}
    code_index: dict[str, set[int]] = defaultdict(set)
    for raw in raw_products:
        product_id = int(raw["Id"])
        codes = extract_product_codes(raw["Name"])
        products[product_id] = {
            "id": product_id,
            "name": raw["Name"].strip(),
            "category_id": raw.get("CategoryId"),
            "codes": codes,
        }
        for code in codes:
            code_index[compact(code)].add(product_id)

    del raw_products
    gc.collect()
    return products, code_index, {
        "source_records": source_records,
        "unique_product_ids": len(products),
        "duplicate_id_records": source_records - len(products),
    }


def load_questions() -> tuple[list[dict], dict[str, list[int]]]:
    questions: list[dict] = []
    by_chat: dict[str, list[int]] = defaultdict(list)
    for filename in sorted(glob.glob(QUESTION_GLOB)):
        with open(filename, encoding="utf-8") as handle:
            for line in handle:
                match = QUESTION_RE.match(line.rstrip())
                if not match:
                    continue
                question = match.groupdict()
                index = len(questions)
                questions.append(question)
                by_chat[question["chat"]].append(index)
    return questions, by_chat


def product_ids_from_text(text: str, valid_ids: set[int]) -> set[int]:
    return {
        product_id
        for value in PRODUCT_URL_RE.findall(text or "")
        if (product_id := int(value)) in valid_ids
    }


def load_chat_product_context(
    valid_ids: set[int], relevant_conversations: set[tuple[str, str]]
) -> tuple[dict[tuple[str, str], dict[int, set[str]]], dict[str, int]]:
    with CHATS_PATH.open(encoding="utf-8") as handle:
        chats = json.load(handle)

    context: dict[tuple[str, str], dict[int, set[str]]] = defaultdict(
        lambda: defaultdict(set)
    )
    stats = Counter()

    for chat in chats:
        chat_id = chat.get("id")
        thread = chat.get("thread") or {}
        date = (thread.get("created_at") or "")[:10]
        conversation_key = (chat_id, date)
        if conversation_key not in relevant_conversations:
            continue
        customer_ids = {
            user.get("id")
            for user in chat.get("users", [])
            if user.get("type") == "customer"
        }

        routing = ((chat.get("thread") or {}).get("properties") or {}).get("routing") or {}
        for product_id in product_ids_from_text(routing.get("start_url", ""), valid_ids):
            context[conversation_key][product_id].add("start_page_url")

        for user in chat.get("users", []):
            if user.get("type") != "customer":
                continue
            visit = user.get("visit") or {}
            for page in visit.get("last_pages") or []:
                for product_id in product_ids_from_text(page.get("url", ""), valid_ids):
                    context[conversation_key][product_id].add(
                        "customer_visited_product_url"
                    )

        for event in thread.get("events") or []:
            if event.get("type") != "message":
                continue
            text = event.get("text") or ""
            method = (
                "customer_message_product_url"
                if event.get("author_id") in customer_ids
                else "agent_shared_product_url"
            )
            for product_id in product_ids_from_text(text, valid_ids):
                context[conversation_key][product_id].add(method)

    stats["chats_scanned"] = len(chats)
    stats["conversations_with_catalog_product_url"] = len(context)
    stats["distinct_url_products"] = len(
        {product_id for matches in context.values() for product_id in matches}
    )
    del chats
    gc.collect()
    return context, dict(stats)


def code_matches(question: str, code_index: dict[str, set[int]]) -> dict[int, bool]:
    tokens = TOKEN_RE.findall(question.upper())
    candidates: set[str] = set()
    for width in range(1, min(5, len(tokens)) + 1):
        for start in range(0, len(tokens) - width + 1):
            value = "".join(tokens[start : start + width])
            if len(value) >= 5 and any(ch.isdigit() for ch in value):
                candidates.add(value)
    matches: dict[int, bool] = {}
    for candidate in candidates:
        product_ids = code_index.get(candidate, ())
        for product_id in product_ids:
            matches[product_id] = matches.get(product_id, False) or len(product_ids) == 1
    return matches


def confidence(methods: set[str], url_product_count: int) -> str:
    if (
        "unique_exact_product_code" in methods
        or "customer_message_product_url" in methods
    ):
        return "high"
    if url_product_count == 1 and (
        "start_page_url" in methods or "customer_visited_product_url" in methods
    ):
        return "high"
    return "medium"


def build_rows(
    products: dict[int, dict],
    code_index: dict[str, set[int]],
    questions: list[dict],
    chat_context: dict[tuple[str, str], dict[int, set[str]]],
) -> list[dict]:
    rows: list[dict] = []
    seen = set()

    for question_index, question in enumerate(questions):
        chat_id = question["chat"]
        conversation_key = (chat_id, question["date"])
        matches = {
            product_id: set(methods)
            for product_id, methods in chat_context.get(conversation_key, {}).items()
        }
        for product_id, is_unique in code_matches(
            question["question"], code_index
        ).items():
            matches.setdefault(product_id, set()).add("exact_product_code")
            if is_unique:
                matches[product_id].add("unique_exact_product_code")

        url_product_count = len(chat_context.get(conversation_key, {}))
        for product_id, methods in matches.items():
            key = (product_id, question_index)
            if key in seen:
                continue
            seen.add(key)
            product = products[product_id]
            rows.append(
                {
                    "product_id": product_id,
                    "category_id": product["category_id"],
                    "product_name": product["name"],
                    "product_codes": "; ".join(product["codes"]),
                    "chat_id": chat_id,
                    "date": question["date"],
                    "theme": question["theme"],
                    "question": question["question"],
                    "match_methods": "; ".join(sorted(methods)),
                    "confidence": confidence(methods, url_product_count),
                }
            )
    return rows


def write_csv(rows: list[dict]) -> None:
    fieldnames = [
        "product_id",
        "category_id",
        "product_name",
        "product_codes",
        "chat_id",
        "date",
        "theme",
        "question",
        "match_methods",
        "confidence",
    ]
    with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def markdown_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def markdown_text(value: object) -> str:
    return " ".join(str(value).split())


def write_questions_markdown(rows: list[dict]) -> None:
    product_rows: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        product_rows[row["product_id"]].append(row)

    lines = ["# Product questions", ""]
    for product_id in sorted(product_rows):
        matched_rows = product_rows[product_id]
        product_name = markdown_text(matched_rows[0]["product_name"])
        lines += [f"## {product_name} (`{product_id}`)", ""]

        seen_questions = set()
        for row in sorted(
            matched_rows,
            key=lambda item: (item["date"], item["chat_id"], item["question"]),
            reverse=True,
        ):
            question = markdown_text(row["question"])
            if not question or question in seen_questions:
                continue
            seen_questions.add(question)
            lines.append(f"- {question}")
        lines.append("")

    QUESTIONS_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_report(
    products: dict[int, dict],
    product_stats: dict[str, int],
    questions: list[dict],
    rows: list[dict],
    chat_stats: dict[str, int],
) -> None:
    product_rows: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        product_rows[row["product_id"]].append(row)

    high_rows = [row for row in rows if row["confidence"] == "high"]
    matched_question_keys = {
        (row["chat_id"], row["date"], row["question"]) for row in rows
    }
    matched_chats = {(row["chat_id"], row["date"]) for row in rows}
    high_products = {row["product_id"] for row in high_rows}
    theme_counts = Counter(row["theme"] for row in rows)
    category_counts = Counter(row["category_id"] for row in rows)
    method_counts = Counter(
        method
        for row in rows
        for method in row["match_methods"].split("; ")
        if method
    )

    product_summary = []
    for product_id, matched_rows in product_rows.items():
        distinct_questions = {
            (row["chat_id"], row["date"], row["question"]) for row in matched_rows
        }
        distinct_chats = {(row["chat_id"], row["date"]) for row in matched_rows}
        product_summary.append(
            (
                len(distinct_questions),
                len(distinct_chats),
                product_id,
                products[product_id]["name"],
            )
        )
    product_summary.sort(reverse=True)

    lines = [
        "# Product–LiveChat Question Analysis",
        "",
        f"Product source: `{PRODUCTS_PATH.relative_to(ROOT)}`  ",
        f"Chat source: `{CHATS_PATH.relative_to(ROOT)}`  ",
        f"Question extraction source: `{Path(QUESTION_GLOB).parent.relative_to(ROOT)}/`",
        "",
        "## Executive summary",
        "",
        f"- Catalog records analyzed: **{product_stats['source_records']:,}**",
        f"- Unique catalog product IDs: **{product_stats['unique_product_ids']:,}** "
        f"({product_stats['duplicate_id_records']:,} duplicate-ID records in the export)",
        f"- LiveChat conversations scanned: **{chat_stats['chats_scanned']:,}**",
        f"- Extracted customer questions searched: **{len(questions):,}**",
        f"- Catalog products connected to at least one question: **{len(product_rows):,}**",
        f"- Products with at least one high-confidence connection: **{len(high_products):,}**",
        f"- Matched conversations: **{len(matched_chats):,}**",
        f"- Distinct matched customer questions: **{len(matched_question_keys):,}**",
        f"- Product-question associations: **{len(rows):,}** "
        f"({len(high_rows):,} high confidence, {len(rows) - len(high_rows):,} medium confidence)",
        "",
        "The detailed, filterable result is in "
        f"`{CSV_PATH.relative_to(ROOT)}`. One customer question can be associated with "
        "more than one product when the conversation compares several product pages.",
        "",
        "## Matching method",
        "",
        "1. Direct product-page IDs from LiveChat URLs (`/p/{Id}`) were joined to the catalog `Id`.",
        "2. Product codes from catalog names (the value after `|`) were matched exactly after punctuation/spacing normalization; refrigerant labels such as `R410A` were excluded.",
        "3. Other customer questions from the same conversation were retained, which links follow-ups such as availability, price, compatibility, delivery, and returns to the identified product.",
        "4. Appliance-model-only matches were intentionally excluded: one appliance model can map to many spare parts and would create substantial false positives.",
        "",
        "High confidence means a unique exact code/customer-posted URL, or a conversation with one unambiguous visited/start product page. Shared codes and other URL-context matches are marked medium confidence.",
        "",
        "## Match evidence",
        "",
        "| Evidence | Associations |",
        "|---|---:|",
    ]
    for method, count in method_counts.most_common():
        lines.append(f"| {markdown_cell(method)} | {count:,} |")

    lines += [
        "",
        "## Question themes",
        "",
        "| Theme | Associations |",
        "|---|---:|",
    ]
    for theme, count in theme_counts.most_common():
        lines.append(f"| {markdown_cell(theme)} | {count:,} |")

    lines += [
        "",
        "## Categories with most question associations",
        "",
        "| CategoryId | Associations | Distinct products |",
        "|---:|---:|---:|",
    ]
    for category_id, count in category_counts.most_common(20):
        distinct = len(
            {
                row["product_id"]
                for row in rows
                if row["category_id"] == category_id
            }
        )
        lines.append(f"| {category_id} | {count:,} | {distinct:,} |")

    lines += [
        "",
        "## Products with most customer questions",
        "",
        "| ProductId | Questions | Chats | Product |",
        "|---:|---:|---:|---|",
    ]
    for question_count, chat_count, product_id, name in product_summary[:40]:
        lines.append(
            f"| {product_id} | {question_count:,} | {chat_count:,} | {markdown_cell(name)} |"
        )

    lines += ["", "## Representative matched questions", ""]
    for _, _, product_id, name in product_summary[:15]:
        lines += [f"### {markdown_cell(name)} (`{product_id}`)", ""]
        sample_seen = set()
        for row in sorted(
            product_rows[product_id],
            key=lambda item: (item["date"], item["chat_id"]),
            reverse=True,
        ):
            sample_key = (row["chat_id"], row["question"])
            if sample_key in sample_seen:
                continue
            sample_seen.add(sample_key)
            lines.append(
                f"- `{row['date']}` `{row['chat_id']}` `{row['theme']}` "
                f"(`{row['confidence']}`) — {row['question']}"
            )
            if len(sample_seen) == 5:
                break
        lines.append("")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    products, code_index, product_stats = load_products()
    questions, questions_by_chat = load_questions()
    chat_context, chat_stats = load_chat_product_context(
        set(products),
        {
            (question["chat"], question["date"])
            for question in questions
        },
    )
    rows = build_rows(
        products, code_index, questions, chat_context
    )
    rows.sort(
        key=lambda row: (
            row["product_id"],
            row["date"],
            row["chat_id"],
            row["question"],
        )
    )
    write_csv(rows)
    write_report(products, product_stats, questions, rows, chat_stats)
    write_questions_markdown(rows)
    print(f"Wrote {len(rows):,} associations to {CSV_PATH}")
    print(f"Wrote report to {REPORT_PATH}")
    print(f"Wrote questions to {QUESTIONS_MD_PATH}")


if __name__ == "__main__":
    main()
