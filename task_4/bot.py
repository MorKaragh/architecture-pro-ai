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


def _parse_defense_mode(argv: list[str]) -> str:
    """
    Поддержка режима защиты:
    - по умолчанию `off`
    - аргумент: --defense off|protected
    """
    if "--defense" in argv:
        idx = argv.index("--defense")
        if idx + 1 < len(argv):
            mode = argv[idx + 1].strip().lower()
            if mode in {"off", "protected"}:
                return mode
    return "off"


def main():
    print("RAG-бот по базе знаний «Половник, выводящий из запоя».")
    print("Задавайте вопросы. Пустая строка или 'выход' / 'exit' — завершение.\n")

    defense = _parse_defense_mode(sys.argv)
    print(f"Режим защиты: {defense}")
    print("Команды: /defense off | /defense protected\n")

    while True:
        try:
            user_input = input(PROMPT).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nДо свидания.")
            break

        if not user_input or user_input.lower() in EXIT_COMMANDS:
            print("До свидания.")
            break

        if user_input.startswith("/defense"):
            parts = user_input.split()
            if len(parts) == 2 and parts[1] in {"off", "protected"}:
                defense = parts[1]
                print(f"Режим защиты: {defense}\n")
            else:
                print("Использование: /defense off | /defense protected\n")
            continue

        try:
            print("Бот:", answer(user_input, defense=defense))
        except Exception as e:
            print("Бот: Ошибка:", e)
        print()


if __name__ == "__main__":
    main()
