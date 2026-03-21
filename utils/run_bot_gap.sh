#!/usr/bin/env bash
set -euo pipefail

# Задание 7: интерактивный бот по «базе с пробелами» + JSONL-лог (task_7/logs/bot_session.jsonl).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

"${ROOT_DIR}/venv/bin/python" \
  "${ROOT_DIR}/task_7/run_bot_gap.py" \
  "$@"
