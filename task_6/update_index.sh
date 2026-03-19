#!/usr/bin/env bash
set -euo pipefail

# Удобная оболочка для cron/планировщиков.
# Запускает Python-скрипт update_index.py из корня репозитория.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"

VENV_PY="${REPO_ROOT}/task_3/venv/bin/python"
if [ -x "${VENV_PY}" ]; then
  "${VENV_PY}" "task_6/update_index.py" "$@"
else
  python3 "task_6/update_index.py" "$@"
fi

