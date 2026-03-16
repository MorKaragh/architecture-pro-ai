#!/usr/bin/env python3
"""
Консольный RAG-бот: REPL. Запуск из task_4 с активированным venv и переменными окружения.
"""
import sys
from pathlib import Path

TASK_4 = Path(__file__).resolve().parent
if str(TASK_4) not in sys.path:
    sys.path.insert(0, str(TASK_4))

from rag import answer

EXIT_COMMANDS = ("выход", "exit", "quit", "q")
PROMPT = "Вы: "


def main():
    print("RAG-бот по базе знаний «Половник, выводящий из запоя».")
    print("Задавайте вопросы. Пустая строка или 'выход' / 'exit' — завершение.\n")

    while True:
        try:
            user_input = input(PROMPT).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nДо свидания.")
            break

        if not user_input or user_input.lower() in EXIT_COMMANDS:
            print("До свидания.")
            break

        try:
            print("Бот:", answer(user_input))
        except Exception as e:
            print("Бот: Ошибка:", e)
        print()


if __name__ == "__main__":
    main()
