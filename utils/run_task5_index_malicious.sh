#!/usr/bin/env bash
set -euo pipefail

# Задание 5: индексация вредоносного документа в databases/bad/chroma_db (для run_bot_bad_*.sh).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

"${ROOT_DIR}/venv/bin/python" \
  "${ROOT_DIR}/task_5/index_malicious_doc.py" \
  "$@"
