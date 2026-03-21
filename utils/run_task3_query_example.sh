#!/usr/bin/env bash
set -euo pipefail

# Задание 3: пример семантического поиска по ChromaDB (без LLM). Аргументы передаются в query_example.py.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

"${ROOT_DIR}/venv/bin/python" \
  "${ROOT_DIR}/task_3/query_example.py" \
  "$@"
