#!/usr/bin/env bash
set -euo pipefail

# Задание 6: инкрементальное обновление индекса (обёртка над task_6/update_index.sh).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

exec "${ROOT_DIR}/task_6/update_index.sh" "$@"
