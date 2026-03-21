# architecture-pro-ai

Учебный проект: RAG-бот по обезличенной базе знаний («Половник, выводящий из запоя»). Стек: **ChromaDB**, **YandexGPT**, эмбеддинги **Yandex Cloud** (text-search-doc / text-search-query).

---

## Быстрый старт

1. В корне репозитория создать и активировать **`venv`**, установить зависимости из **`task_3/requirements.txt`** и пакеты для **`task_4/requirements.txt`** (если запускаете бота).
2. Задать переменные окружения (см. раздел ниже).
3. Собрать основной индекс: **`./utils/run_task3_build_index.sh`**.
4. Запустить сценарии через меню **`./main_interactive.sh`** — там же боты, индексация для заданий 5–7 и утилиты.

Прямой запуск без меню: скрипты в каталоге **`utils/`** (`run_bot_normal.sh`, `run_task7_evaluate.sh` и т.д.).

---

## Где что лежит

| Путь | Назначение |
|------|------------|
| **`task_N/`** | Материалы по номеру задания: постановка, отчёт, инструкции запуска. |
| **`task_2/final_fandom/`** | Тексты базы знаний (`.txt`) для индексации. |
| **`databases/good/chroma_db`** | Рабочий векторный индекс (после `build_index`). |
| **`databases/bad/chroma_db`** | Отдельный индекс с «вредоносным» документом (задание 5). |
| **`task_7/chroma_db_gap`** | Индекс с намеренными пробелами в покрытии (задание 7). |
| **`utils/`** | Оболочки `*.sh` для запуска из корня одной командой. |

---

## Как ориентироваться в задании `task_N`

В типичной папке задания:

- **`TASK.md`** — формулировка задания от курса.
- **`REPORT.md`** — краткий отчёт: что сделано, ключевые выводы, ссылки на артефакты.
- **`README.md`** — есть не у всех заданий; если файл есть, там шаги запуска скриптов именно для этого этапа.

Дополнительные материалы рядом с заданием (примеры диалогов, логи прогонов, словари, развёрнутое исследование) лежат по путям из **`REPORT.md`** и таблицы ниже.

---

## Оглавление по заданиям

| № | Тема | Постановка | Отчёт | Запуск | Важные артефакты |
|---|------|------------|-------|--------|------------------|
| 1 | Модели, эмбеддинги, векторные БД | [TASK](task_1/TASK.md) | [REPORT](task_1/REPORT.md) | — | [Полное исследование](task_1/otchet_issledovanie_rag_infrastruktury.md) |
| 2 | База знаний | [TASK](task_2/TASK.md) | [REPORT](task_2/REPORT.md) | [README](task_2/README.md) | Корпус `final_fandom/`, [DICTIONARY.md](task_2/kimetsu_articles/DICTIONARY.md), `terms_map.json` |
| 3 | Векторный индекс | [TASK](task_3/TASK.md) | [REPORT](task_3/REPORT.md) | [README](task_3/README.md) | `build_index.py`, `query_example.py` |
| 4 | RAG-бот | [TASK](task_4/TASK.md) | [REPORT](task_4/REPORT.md) | [README](task_4/README.md) | `rag.py`, `bot.py`, `prompts/`, [DIALOGS.md](task_4/DIALOGS.md) |
| 5 | Prompt injection | [TASK](task_5/TASK.md) | [REPORT](task_5/REPORT.md) | [README](task_5/README.md) | `malicious_doc.txt`, [LOG_EXECUTION.md](task_5/LOG_EXECUTION.md) |
| 6 | Обновление индекса | [TASK](task_6/TASK.md) | [REPORT](task_6/REPORT.md) | [README](task_6/README.md) | `update_index.py`, логи, [пример записи](task_6/LOG_EXECUTION.md) |
| 7 | Качество покрытия | [TASK](task_7/TASK.md) | [REPORT](task_7/REPORT.md) | [README](task_7/README.md) | `golden_questions.txt`, `evaluate.py`, `logs/`, `sequence_diagram.puml` |

---

## Переменные окружения

| Переменная | Зачем |
|------------|--------|
| **`YANDEX_CLOUD_FOLDER`** | ID каталога в Yandex Cloud. |
| **`YANDEX_CLOUD_API_KEY`** | Доступ к YandexGPT и эмбеддингам в типичном сценарии бота (`task_4`). |
| **`YANDEX_IAM_TOKEN`** | Альтернатива для **`task_3`** (`embedding_client.py`), если индекс собираете через IAM. |
