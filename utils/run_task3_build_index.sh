#!/usr/bin/env bash
set -euo pipefail

# Задание 3: полная пересборка основного индекса в databases/good/chroma_db.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

"${ROOT_DIR}/venv/bin/python" \
  "${ROOT_DIR}/task_3/build_index.py" \
  "$@"
