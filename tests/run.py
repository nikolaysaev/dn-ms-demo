#!/usr/bin/env python3
"""Run generated test cases against the local apogee99 chatbot.

Sends each case to the dashboard public API (/v1/chat/ask) with a fresh
session id, respecting the public rate limit (chat_ask = 45/min). Results are
streamed to tests/out/results.jsonl and the run is resumable (already-completed
case_ids are skipped).

Usage: python3 tests/run.py [--limit N] [--workers W] [--rpm R]
"""
import argparse
import json
import re
import threading
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

OUTDIR = Path(__file__).resolve().parent / "out"
CASES = OUTDIR / "cases.jsonl"
RESULTS = OUTDIR / "results.jsonl"

API = "http://127.0.0.1:8002/v1/chat/ask"
# Tenanted by store_key + Origin. `store_key` is the store's opaque, immutable
# public_id — the only external handle; the internal numeric store_id never
# appears on the wire (the legacy "11" is retired).
STORE_KEY = "apogee99_e6swgn"

GATE_MARKERS = (
    "идентификатори на уреда",
    "Нужни са данни",
    "сервизния стикер",
    "OEM/PNC",
)


def strip_html(html: str) -> str:
    txt = re.sub(r"<[^>]+>", " ", html or "")
    return re.sub(r"\s+", " ", txt).strip()


class RateLimiter:
    """Simple global min-interval limiter (thread-safe)."""

    def __init__(self, rpm):
        self.interval = 60.0 / rpm
        self.lock = threading.Lock()
        self.next_at = 0.0

    def wait(self):
        with self.lock:
            now = time.monotonic()
            wait = self.next_at - now
            if wait > 0:
                time.sleep(wait)
                now = time.monotonic()
            self.next_at = max(now, self.next_at) + self.interval


def ask(session_id, user_text, timeout=120):
    payload = json.dumps({
        "store_key": STORE_KEY,
        "session_id": session_id,
        "user_text": user_text,
    }).encode("utf-8")
    req = urllib.request.Request(API, data=payload,
                                 headers={"Content-Type": "application/json", "Origin": "http://127.0.0.1:8090"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def run_case(case, limiter, retries=3):
    sid = f"qa_{case['case_id']}_{int(time.time()*1000)}"
    for attempt in range(retries):
        limiter.wait()
        try:
            status, data = ask(sid, case["query"])
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(3 * (attempt + 1))
                continue
            return {**case, "error": f"HTTP {e.code}", "ok": False}
        except Exception as e:  # noqa: BLE001
            if attempt < retries - 1:
                time.sleep(2)
                continue
            return {**case, "error": str(e), "ok": False}

        picked = data.get("picked", []) or []
        text = strip_html(data.get("message_html", ""))
        gated = any(m in (data.get("message_html", "") + (data.get("ask_follow_up") or ""))
                    for m in GATE_MARKERS)
        return {
            **case,
            "ok": bool(data.get("ok")),
            "severity": data.get("severity"),
            "confidence": data.get("confidence"),
            "escalated": bool(data.get("escalated")),
            "gated": gated,
            "n_picked": len(picked),
            "picked_ids": [p.get("id") for p in picked],
            "picked_names": [p.get("name") for p in picked],
            "text": text[:800],
            "ask_follow_up": data.get("ask_follow_up"),
        }
    return {**case, "error": "rate_limited", "ok": False}


def main():
    global CASES, RESULTS
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--rpm", type=int, default=40)
    ap.add_argument("--fresh", action="store_true", help="ignore existing results")
    ap.add_argument("--cases", default=str(CASES), help="cases jsonl path")
    ap.add_argument("--results", default=str(RESULTS), help="results jsonl path")
    args = ap.parse_args()

    CASES = Path(args.cases)
    RESULTS = Path(args.results)

    cases = [json.loads(l) for l in CASES.read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.limit:
        cases = cases[: args.limit]

    done = set()
    if RESULTS.exists() and not args.fresh:
        for l in RESULTS.read_text(encoding="utf-8").splitlines():
            if l.strip():
                try:
                    done.add(json.loads(l)["case_id"])
                except Exception:
                    pass
    todo = [c for c in cases if c["case_id"] not in done]
    print(f"{len(cases)} cases, {len(done)} already done, {len(todo)} to run", flush=True)

    limiter = RateLimiter(args.rpm)
    write_lock = threading.Lock()
    counter = {"n": 0}
    mode = "w" if args.fresh else "a"
    with RESULTS.open(mode, encoding="utf-8") as out:
        def worker(case):
            res = run_case(case, limiter)
            with write_lock:
                out.write(json.dumps(res, ensure_ascii=False) + "\n")
                out.flush()
                counter["n"] += 1
                if counter["n"] % 20 == 0:
                    print(f"  ... {counter['n']}/{len(todo)}", flush=True)
            return res

        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            list(ex.map(worker, todo))

    print(f"Done. {counter['n']} results appended to {RESULTS}", flush=True)


if __name__ == "__main__":
    main()
