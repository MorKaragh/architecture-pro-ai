#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_PATH="${ROOT_DIR}/databases/good/chroma_db"

"${ROOT_DIR}/venv/bin/python" \
  "${ROOT_DIR}/task_4/bot.py" \
  --db-path "${DB_PATH}" \
  --defense off

