#!/usr/bin/env bash
set -euo pipefail

# Задание 7: автопрогон golden-набора, логи task_7/logs/eval_logs.jsonl и eval_summary.json.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

"${ROOT_DIR}/venv/bin/python" \
  "${ROOT_DIR}/task_7/evaluate.py" \
  "$@"
