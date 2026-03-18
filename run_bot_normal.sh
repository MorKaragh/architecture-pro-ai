#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export CHROMA_PATH="${ROOT_DIR}/task_3/chroma_db"

"${ROOT_DIR}/task_4/venv/bin/python" \
  "${ROOT_DIR}/task_4/bot.py" \
  --defense off

