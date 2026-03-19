# Task 6 — Автоматическое ежедневное обновление базы знаний

Задание требует автоматизировать обновление векторного индекса: подхват новых/изменённых документов, чанкинг, эмбеддинги, обновление ChromaDB и логирование.

В этом решении источник данных — локальная папка `task_6/source_docs/`.
Скрипт `task_6/update_index.py` инкрементально обновляет уже существующую базу ChromaDB из `databases/good/chroma_db/` (коллекция `knowledge_base`), ориентируясь на `sha256` файлов.

## Что запускается

- `task_6/update_index.py` — выполняет один проход:
  - сканирует `task_6/source_docs/*.txt`;
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
2. Добавьте новый `*.txt` в `task_6/source_docs/`.
3. Запустите снова `python task_6/update_index.py ...`.
4. Проверьте `task_6/logs/index_update.jsonl` — появятся `files_added_or_updated > 0` и рост `chunks_added`.

## Периодический запуск (cron)

Пример cron для ежедневного запуска в 06:00:

```cron
0 6 * * * cd /path/to/architecture-pro-ai && bash task_6/update_index.sh --mode auto >> task_6/logs/cron_stdout.log 2>&1
```

При ошибках запись всё равно попадёт в stdout (и в JSONL лог, если ошибка произошла после старта run).

## PlantUML-диаграмма

Диаграмма архитектуры лежит в `task_6/architecture.puml`.

