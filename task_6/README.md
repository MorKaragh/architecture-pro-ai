# Task 6 — Автоматическое ежедневное обновление базы знаний

Задание требует автоматизировать обновление векторного индекса: подхват новых/изменённых документов, чанкинг, эмбеддинги, обновление ChromaDB и логирование.

В этом решении источник данных — локальная папка с `.txt` документами:
- по умолчанию: `task_6/source_docs/`;
- либо любой путь через параметр `--source-dir`.
Скрипт `task_6/update_index.py` инкрементально обновляет уже существующую базу ChromaDB из `databases/good/chroma_db/` (коллекция `knowledge_base`), ориентируясь на `sha256` файлов.

## Что запускается

- `task_6/update_index.py` — выполняет один проход:
  - сканирует `*.txt` в указанной папке источника;
  - для изменённых файлов пересчитывает чанки и эмбеддинги;
  - удаляет старые чанки этого файла (по сохранённому состоянию в `task_6/state.json`);
  - добавляет новые чанки в ChromaDB (`databases/good/chroma_db/`, коллекция `knowledge_base`);
  - дописывает JSON запись в `task_6/logs/index_update.jsonl`.

- `task_6/update_index.sh` — обёртка для удобного запуска из cron.

## Требования

Скрипт использует те же зависимости, что `task_3`:

- `chromadb`
- `langchain-text-splitters`
- `numpy`
- `requests`

Установка (пример, если вы ставили в отдельный venv):

```bash
pip install -r task_3/requirements.txt
```

Для режима `online` дополнительно нужны переменные окружения:

- `YANDEX_CLOUD_FOLDER`
- `YANDEX_CLOUD_API_KEY`

## Быстрый старт (локальная проверка без ключей)

Если ключей нет, скрипт автоматически перейдёт в режим `stub` эмбеддингов (можно явно указать `--mode stub`).
В `stub`-режиме индекс не пишется в `databases/good/chroma_db`, а обновляется отдельная коллекция в `task_6/chroma_db_stub/`.

1. Добавьте/создайте файл `task_6/source_docs/example.txt`.
2. Запустите:

```bash
./task_6/update_index.sh --mode stub
```

После первого прогона в логах появятся записи вида:

- сколько файлов было обработано
- сколько чанков добавлено/удалено
- размер индекса до/после

## Тест “добавлением нового документа”

1. Выполните индексирование.
2. Добавьте новый `*.txt` в папку источника.
3. Запустите индексирование повторно.
4. Проверьте `task_6/logs/index_update.jsonl` — появятся `files_added_or_updated > 0` и рост `chunks_added`.

Пример команды для внешнего источника:

```bash
./task_6/update_index.sh --mode online --source-dir "task_2/final_fandom/additional"
```

Пример успешного результата (`stdout`):

```json
{"run_id":"d533067e-c619-411f-9540-5c2908762645","ok":true,"files_seen":1,"files_added_or_updated":1,"chunks_added":23,"chunks_deleted":1,"index_size_after":382,"errors":0,"elapsed_sec":14.026}
```

## Периодический запуск (cron)

Пример cron для ежедневного запуска в 06:00:

```cron
0 6 * * * cd /path/to/architecture-pro-ai && bash task_6/update_index.sh --mode auto >> task_6/logs/cron_stdout.log 2>&1
```

При ошибках запись всё равно попадёт в stdout (и в JSONL лог, если ошибка произошла после старта run).

## Проверка сервисов Yandex

Для быстрой диагностики подключения используйте утилиту:

```bash
python3 utils/check_yandex_services.py
```

Скрипт проверяет `embedding` и `llm` endpoint для `Bearer` (IAM) и `Api-Key`.

## Краткий отчёт по заданию

Итоговый отчёт: `task_6/REPORT.md`.

## PlantUML-диаграмма

Диаграмма архитектуры лежит в `task_6/architecture.puml`.

