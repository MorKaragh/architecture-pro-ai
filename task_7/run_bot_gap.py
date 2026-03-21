#!/usr/bin/env python3
"""
Интерактивный RAG-бот (как task_4/bot.py) с базой «с пробелами» и логированием по требованиям задания 7.

По умолчанию: ChromaDB task_7/chroma_db_gap, лог дописывается в task_7/logs/bot_session.jsonl.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TASK_4 = REPO_ROOT / "task_4"
DEFAULT_DB_PATH = REPO_ROOT / "task_7" / "chroma_db_gap"
DEFAULT_LOG_PATH = REPO_ROOT / "task_7" / "logs" / "bot_session.jsonl"

EXIT_COMMANDS = ("выход", "exit", "quit", "q")
PROMPT = "Вы: "


def _load_rag():
    if str(TASK_4) not in sys.path:
        sys.path.insert(0, str(TASK_4))
    from rag import answer, search  # type: ignore

    return answer, search


def _parse_defense_inline(user_input: str, current: str) -> tuple[str, bool]:
    """Возвращает (режим, consumed) если строка — команда /defense."""
    if not user_input.startswith("/defense"):
        return current, False
    parts = user_input.split()
    if len(parts) == 2 and parts[1] in {"off", "protected"}:
        return parts[1], True
    return current, True


def main() -> int:
    from rag_logging import is_successful_answer, iso_now

    parser = argparse.ArgumentParser(description="RAG-бот с gap-индексом и JSONL-логом (task 7)")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH, help="Путь к ChromaDB (по умолчанию gap)")
    parser.add_argument("--defense", type=str, default="protected", choices=["off", "protected"])
    parser.add_argument("--log-path", type=Path, default=DEFAULT_LOG_PATH)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--min-success-len", type=int, default=40)
    args = parser.parse_args()

    db_path = args.db_path.expanduser().resolve()
    log_path = args.log_path.expanduser().resolve()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    answer_fn, search_fn = _load_rag()
    defense = args.defense

    print("RAG-бот с базой «с пробелами покрытия» (task_7/chroma_db_gap).")
    print("Лог запросов: JSONL с полями задания 7 (query, timestamp, чанки, источники, длина, успех).")
    print("Пустая строка или выход — завершение.\n")
    print(f"База: {db_path}")
    print(f"Режим защиты: {defense}")
    print(f"Лог: {log_path}")
    print("Команды: /defense off | /defense protected\n")

    req_id = 0
    while True:
        try:
            user_input = input(PROMPT).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nДо свидания.")
            break

        if not user_input or user_input.lower() in EXIT_COMMANDS:
            print("До свидания.")
            break

        new_defense, consumed = _parse_defense_inline(user_input, defense)
        if consumed:
            if new_defense != defense:
                defense = new_defense
                print(f"Режим защиты: {defense}\n")
            else:
                print("Использование: /defense off | /defense protected\n")
            continue

        req_id += 1
        timestamp = iso_now()
        chunks_found = 0
        sources: list[str] = []
        search_error: str | None = None

        try:
            sr = search_fn(user_input, db_path=db_path, top_k=args.top_k)
            docs = (sr.get("documents") or [[]])[0]
            metas = (sr.get("metadatas") or [[]])[0]
            chunks_found = len(docs)
            sources = sorted({(m or {}).get("title", "?") for m in metas})
        except Exception as e:  # noqa: BLE001
            search_error = repr(e)

        try:
            bot_answer = answer_fn(
                user_input, top_k=args.top_k, defense=defense, db_path=db_path
            )
        except Exception as e:  # noqa: BLE001
            bot_answer = f"Ошибка: {e!r}"

        response_stripped = bot_answer.strip()
        response_len = len(response_stripped)
        success_flag = is_successful_answer(bot_answer, args.min_success_len)

        rec = {
            "id": req_id,
            "mode": "interactive",
            "timestamp": timestamp,
            "query": user_input,
            "chunks_found": chunks_found,
            "sources": sources,
            "response_length": response_len,
            "successful_answer": success_flag,
            "answer": bot_answer,
            "search_error": search_error,
            "defense": defense,
            "db_path": str(db_path),
        }
        with log_path.open("a", encoding="utf-8") as logf:
            logf.write(json.dumps(rec, ensure_ascii=False) + "\n")

        print("Бот:", bot_answer)
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
