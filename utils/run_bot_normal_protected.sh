#!/usr/bin/env bash
set -euo pipefail

# RAG-бот по «хорошей» базе (task_3/4) с защитой от prompt injection.
# Сценарий: сравнение с run_bot_normal.sh (defense off) и с «плохой» БД.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
DB_PATH="${ROOT_DIR}/databases/good/chroma_db"

"${ROOT_DIR}/venv/bin/python" \
  "${ROOT_DIR}/task_4/bot.py" \
  --db-path "${DB_PATH}" \
  --defense protected
