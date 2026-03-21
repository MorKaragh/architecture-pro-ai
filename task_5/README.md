# Задание 5 — prompt injection и защита

## Суть

В отдельную коллекцию ChromaDB (`databases/bad/chroma_db`) индексируется вредоносный фрагмент (`malicious_doc.txt`). Режимы защиты реализованы в **`task_4/rag.py`** (`--defense off|protected`).

## Запуск индексации

Из **корня репозитория** (общий `venv`):

```bash
./utils/run_task5_index_malicious.sh
```

Или:

```bash
./venv/bin/python task_5/index_malicious_doc.py
```

## Проверка бота

Удобнее меню **`./main_interactive.sh`** → пункты «плохая база» (unsafe / protected). Переменные: `YANDEX_CLOUD_FOLDER`, `YANDEX_CLOUD_API_KEY`.

Результаты испытаний — в **`REPORT.md`**; полный лог диалогов (артефакт задания) — **`LOG_EXECUTION.md`**.
