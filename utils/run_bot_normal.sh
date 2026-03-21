#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
DB_PATH="${ROOT_DIR}/databases/good/chroma_db"

"${ROOT_DIR}/venv/bin/python" \
  "${ROOT_DIR}/task_4/bot.py" \
  --db-path "${DB_PATH}" \
  --defense off
