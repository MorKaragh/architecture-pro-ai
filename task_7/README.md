# Task 7 — Аналитика покрытия и качества базы знаний

**Быстрый запуск из корня:** `./main_interactive.sh` (пункты gap-бот, сборка gap-индекса, evaluate) или `./utils/run_task7_*.sh`.

Этот шаг выполнен в изолированном контуре, чтобы не ломать рабочую базу из прошлых заданий.

## Что сделано

- Создан скрипт построения "испорченной" БД: `task_7/build_gap_index.py`.
- Скрипт намеренно удаляет 3 ключевые сущности по именам файлов:
  - `Константин`
  - `Марк_Козлов`
  - `Варка_при_луне`
- Индекс создаётся в отдельной папке: `task_7/chroma_db_gap` (коллекция `knowledge_base`).
- Добавлен золотой набор вопросов: `task_7/golden_questions.txt` (12 вопросов).
- Добавлен автооценщик: `task_7/evaluate.py`.
- Добавлена диаграмма последовательности: `task_7/sequence_diagram.puml`.

## Как запустить

1) Построить отдельную "испорченную" базу:

```bash
python3 task_7/build_gap_index.py
```

2) Прогнать автооценку по golden-набору:

```bash
python3 task_7/evaluate.py --db-path task_7/chroma_db_gap --questions-path task_7/golden_questions.txt
```

## Что сохраняется

- Логи запросов: `task_7/logs/eval_logs.jsonl`
- Итог агрегации: `task_7/logs/eval_summary.json`
- Манифест сборки gap-индекса: `task_7/gap_index_manifest.json`

Каждая запись в `eval_logs.jsonl` содержит:
- `query`
- `timestamp`
- `chunks_found`
- `response_length`
- `successful_answer`
- `sources`
- а также `evaluation_pass` относительно ожидания из golden-набора.

## Почему это безопасно для уже выполненных задач

- Рабочая база `databases/good/chroma_db` не изменяется.
- Все эксперименты Task 7 работают только с `task_7/chroma_db_gap`.
