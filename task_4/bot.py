#!/usr/bin/env python3
"""
Консольный RAG-бот: REPL с минимальным интерфейсом.
Запуск: из корня репо с активированным venv и PYTHONPATH, включающим task_3 и task_4.

  cd task_4
  python -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  export YANDEX_CLOUD_FOLDER="..."
  export YANDEX_CLOUD_API_KEY="..."
  python bot.py
"""
import sys
from pathlib import Path

# Чтобы импортировать rag из task_4 при запуске из task_4
TASK_4 = Path(__file__).resolve().parent
if str(TASK_4) not in sys.path:
    sys.path.insert(0, str(TASK_4))

from rag import answer


def main():
    print("RAG-бот по базе знаний «Половник, выводящий из запоя».")
    print("Задавайте вопросы. Пустая строка или 'выход' / 'exit' — завершение.\n")

    while True:
        try:
            user_input = input("Вы: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nДо свидания.")
            break

        if not user_input or user_input.lower() in ("выход", "exit", "quit", "q"):
            print("До свидания.")
            break

        try:
            reply = answer(user_input)
            print("Бот:", reply)
        except Exception as e:
            print("Бот: Ошибка:", e)
        print()


if __name__ == "__main__":
    main()
