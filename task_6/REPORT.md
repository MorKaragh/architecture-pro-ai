# Отчёт по заданию 6: автоматическое ежедневное обновление базы знаний

## Что реализовано

- Источник данных: локальная папка с документами (`task_6/source_docs/*.txt` или передаваемый `--source-dir`).
- Скрипт обновления: `task_6/update_index.py` (обёртка для запуска: `task_6/update_index.sh`).
- Обновление инкрементальное:
  - сканируются новые/изменённые файлы (по `sha256`);
  - удаляются старые чанки изменённых/удалённых документов;
  - добавляются новые чанки и эмбеддинги в ChromaDB.
- Периодический запуск подготовлен через cron (пример в `task_6/README.md`).
- Архитектурная диаграмма в PlantUML: `task_6/architecture.puml`.

## Логирование (требование задания)

Лог пишется в JSONL: `task_6/logs/index_update.jsonl` (одна запись на один запуск).
Для фиксации артефакта в репозитории дополнительно сохранён пример записи: `task_6/index_update_sample.jsonl`.

В записи присутствуют поля:
- `start_time`, `end_time`;
- `files_seen`, `files_added_or_updated`, `files_unchanged`;
- `chunks_added`, `chunks_deleted`;
- `index_size_before`, `index_size_after`;
- `errors`, `elapsed_sec`, `run_id`.

## Демонстрация обновления (проверка на новом документе)

Был выполнен запуск с внешним источником новых данных:

```bash
./task_6/update_index.sh --mode online --source-dir "task_2/final_fandom/additional"
```

Результат запуска (stdout):

```json
{"run_id": "d533067e-c619-411f-9540-5c2908762645", "ok": true, "files_seen": 1, "files_added_or_updated": 1, "chunks_added": 23, "chunks_deleted": 1, "index_size_after": 382, "errors": 0, "elapsed_sec": 14.026}
```

Соответствующая запись в `index_update.jsonl`:
- `source_dir`: `task_2/final_fandom/additional`
- `mode`: `online`
- `files_added_or_updated`: `1`
- `chunks_added`: `23`
- `index_size_before`: `359`
- `index_size_after`: `382`
- `errors`: `[]`

## Вывод

Задание 6 выполнено: реализованы автоматизированное обновление индекса, инкрементальная обработка документов, журналирование запусков, схема архитектуры и демонстрация обновления на добавленных данных.

## Валидация отчёта

- Проверено наличие ключевых артефактов:
  - `task_6/update_index.py`
  - `task_6/update_index.sh`
  - `task_6/architecture.puml`
  - `task_6/index_update_sample.jsonl`
- Проверено соответствие структуры лога требованиям постановки (время, размеры, чанки, ошибки).

