#!/usr/bin/env python3
"""
Task 7: автоматическая проверка RAG по golden-набору + логирование.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TASK_7 = REPO_ROOT / "task_7"
DEFAULT_DB_PATH = TASK_7 / "chroma_db_gap"
DEFAULT_QUESTIONS = TASK_7 / "golden_questions.txt"
DEFAULT_LOG_PATH = TASK_7 / "logs" / "eval_logs.jsonl"
DEFAULT_SUMMARY_PATH = TASK_7 / "logs" / "eval_summary.json"


def _load_rag():
    task_4_dir = REPO_ROOT / "task_4"
    if str(task_4_dir) not in sys.path:
        sys.path.insert(0, str(task_4_dir))
    from rag import answer, search  # type: ignore

    return answer, search


def parse_golden(path: Path) -> list[dict]:
    raw = path.read_text(encoding="utf-8")
    blocks = [b.strip() for b in raw.split("\n---\n") if b.strip()]
    out: list[dict] = []

    for b in blocks:
        item: dict[str, str] = {}
        for line in b.splitlines():
            line = line.strip()
            if not line or ":" not in line:
                continue
            key, val = line.split(":", 1)
            item[key.strip().upper()] = val.strip()

        q = item.get("Q", "")
        if not q:
            continue
        should = item.get("SHOULD_HAVE_ANSWER", "yes").lower() in {"yes", "true", "1", "да"}
        out.append(
            {
                "question": q,
                "topic": item.get("TOPIC", ""),
                "expected": item.get("EXPECTED", ""),
                "should_have_answer": should,
            }
        )
    return out


def main() -> int:
    from rag_logging import is_successful_answer, iso_now

    parser = argparse.ArgumentParser(description="Evaluate RAG with logging for task_7")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--questions-path", type=Path, default=DEFAULT_QUESTIONS)
    parser.add_argument("--log-path", type=Path, default=DEFAULT_LOG_PATH)
    parser.add_argument("--summary-path", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--defense", type=str, default="protected", choices=["off", "protected"])
    parser.add_argument("--min-success-len", type=int, default=40)
    args = parser.parse_args()

    answer_fn, search_fn = _load_rag()
    questions = parse_golden(args.questions_path)
    args.log_path.parent.mkdir(parents=True, exist_ok=True)

    total = len(questions)
    hits = 0
    expected_yes = 0
    expected_no = 0

    with args.log_path.open("w", encoding="utf-8") as logf:
        for idx, q in enumerate(questions, start=1):
            query = q["question"]
            should_have = bool(q["should_have_answer"])
            if should_have:
                expected_yes += 1
            else:
                expected_no += 1

            timestamp = iso_now()
            search_error = None
            chunks_found = 0
            sources: list[str] = []

            try:
                sr = search_fn(query, db_path=args.db_path, top_k=args.top_k)
                docs = (sr.get("documents") or [[]])[0]
                metas = (sr.get("metadatas") or [[]])[0]
                chunks_found = len(docs)
                sources = sorted({(m or {}).get("title", "?") for m in metas})
            except Exception as e:  # noqa: BLE001
                search_error = repr(e)

            try:
                bot_answer = answer_fn(query, top_k=args.top_k, defense=args.defense, db_path=args.db_path)
            except Exception as e:  # noqa: BLE001
                bot_answer = f"ERROR: {e!r}"

            response_len = len(bot_answer.strip())
            success_flag = is_successful_answer(bot_answer, args.min_success_len)
            expected_ok = (should_have and success_flag) or ((not should_have) and (not success_flag))
            if expected_ok:
                hits += 1

            rec = {
                "id": idx,
                "timestamp": timestamp,
                "query": query,
                "topic": q["topic"],
                "expected": q["expected"],
                "should_have_answer": should_have,
                "chunks_found": chunks_found,
                "sources": sources,
                "response_length": response_len,
                "successful_answer": success_flag,
                "evaluation_pass": expected_ok,
                "answer": bot_answer,
                "search_error": search_error,
            }
            logf.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"[{idx}/{total}] pass={expected_ok} chunks={chunks_found} q={query}")

    summary = {
        "timestamp": iso_now(),
        "db_path": str(args.db_path),
        "questions_path": str(args.questions_path),
        "log_path": str(args.log_path),
        "total_questions": total,
        "expected_yes": expected_yes,
        "expected_no": expected_no,
        "passed": hits,
        "failed": total - hits,
        "accuracy": round((hits / total), 4) if total else 0.0,
        "defense_mode": args.defense,
        "top_k": args.top_k,
    }
    args.summary_path.parent.mkdir(parents=True, exist_ok=True)
    args.summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
