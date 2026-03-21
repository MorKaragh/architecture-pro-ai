#!/usr/bin/env bash
set -euo pipefail

# Задание 7: пересборка отдельного индекса без части сущностей (task_7/chroma_db_gap).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

"${ROOT_DIR}/venv/bin/python" \
  "${ROOT_DIR}/task_7/build_gap_index.py" \
  "$@"
