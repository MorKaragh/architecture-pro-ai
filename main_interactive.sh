#!/usr/bin/env bash
# Главная точка входа для интерактивной работы с проектом: меню сценариев (боты, индексы, проверки).
# Сами сценарии лежат в utils/.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UTILS="${ROOT_DIR}/utils"

if [[ ! -d "${UTILS}" ]]; then
  echo "Не найдена папка ${UTILS}" >&2
  exit 1
fi

if [[ ! -x "${ROOT_DIR}/venv/bin/python" ]]; then
  echo "Внимание: нет исполняемого ${ROOT_DIR}/venv/bin/python — часть сценариев может не запуститься." >&2
fi

_bold() { tput bold 2>/dev/null || true; }
_reset() { tput sgr0 2>/dev/null || true; }
_cyan() { tput setaf 6 2>/dev/null || true; }
_dim() { tput dim 2>/dev/null || true; }
_yellow() { tput setaf 3 2>/dev/null || true; }

pause() {
  echo
  _dim
  read -r -p "Enter — вернуться в меню " _ </dev/tty 2>/dev/null || read -r -p "Enter — вернуться в меню " _
  _reset
}

run_util() {
  local script="$1"
  shift
  set +e
  bash "${UTILS}/${script}" "$@"
  local code=$?
  set -e
  if [[ "${code}" -ne 0 ]]; then
    echo
    _yellow
    echo "Завершено с кодом ${code}"
    _reset
  fi
  pause
}

draw_frame() {
  clear
  _cyan
  echo "  ┌────────────────────────────────────────────────────────────┐"
  echo "  │                                                            │"
  echo -n "  │   "
  _bold
  echo -n "Главное меню — интерактивная работа"
  _reset
  _cyan
  echo "                    │"
  echo "  │   architecture-pro-ai · сценарии из utils/                 │"
  echo "  │                                                            │"
  echo "  └────────────────────────────────────────────────────────────┘"
  _reset
  echo
}

show_menu() {
  _bold
  echo "  Боты (консольный REPL, YandexGPT + ChromaDB)"
  _reset
  echo "    1 — Хорошая база (good) · защита off"
  echo "    2 — Хорошая база (good) · защита protected"
  echo "    3 — Плохая база (bad, task 5) · защита off (демо утечки)"
  echo "    4 — Плохая база (bad) · защита protected"
  echo "    5 — Задание 7: база с пробелами + лог JSONL (gap)"
  echo
  _bold
  echo "  Утилиты и проверки"
  _reset
  echo "    6 — Задание 3: собрать основной индекс (databases/good)"
  echo "    7 — Задание 3: пример семантического поиска (без LLM)"
  echo "    8 — Задание 5: проиндексировать вредоносный документ в bad"
  echo "    9 — Задание 6: инкрементальное обновление индекса"
  echo "   10 — Задание 7: собрать gap-индекс (chroma_db_gap)"
  echo "   11 — Задание 7: прогон golden-набора (evaluate)"
  echo
  _dim
  echo "    0 — выход   ·   прямые скрипты: utils/run_*.sh"
  _reset
  echo
}

main_loop() {
  while true; do
    draw_frame
    show_menu
    _bold
    read -r -p "  Выберите номер: " choice </dev/tty 2>/dev/null || read -r -p "  Выберите номер: " choice
    _reset
    echo

    case "${choice}" in
      1) run_util run_bot_normal.sh ;;
      2) run_util run_bot_normal_protected.sh ;;
      3) run_util run_bot_bad_unsafe.sh ;;
      4) run_util run_bot_bad_protected.sh ;;
      5) run_util run_bot_gap.sh ;;
      6) run_util run_task3_build_index.sh ;;
      7) run_util run_task3_query_example.sh ;;
      8) run_util run_task5_index_malicious.sh ;;
      9) run_util run_task6_update_index.sh ;;
      10) run_util run_task7_build_gap_index.sh ;;
      11) run_util run_task7_evaluate.sh ;;
      0 | q | Q | exit | выход)
        clear
        echo "До свидания."
        exit 0
        ;;
      *)
        _yellow
        echo "  Неизвестный пункт: «${choice}». Введите число 0–11."
        _reset
        pause
        ;;
    esac
  done
}

main_loop
