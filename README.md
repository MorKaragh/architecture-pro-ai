# architecture-pro-ai

Учебный проект: RAG-бот по обезличенной базе («Половник, выводящий из запоя»), ChromaDB, YandexGPT и Yandex Embeddings.

---

## Быстрый старт

| Шаг | Действие |
|-----|----------|
| 1 | Создать и активировать **`venv`** в корне репозитория, установить зависимости (`task_3/requirements.txt` и пакеты для `task_4` по необходимости). |
| 2 | Задать **`YANDEX_CLOUD_FOLDER`**, **`YANDEX_CLOUD_API_KEY`** (и при работе `task_3` через IAM — **`YANDEX_IAM_TOKEN`**). |
| 3 | Собрать основной индекс: **`./utils/run_task3_build_index.sh`** (или пункт меню **6**). |
| 4 | Запустить интерактивное меню: **`./main_interactive.sh`**. |

Меню вызывает сценарии из каталога **`utils/`** (боты, индексация, задания 3–7). Список имён файлов `utils/run_*.sh` совпадает с пунктами меню.

---

## Задания (wiki)

В каждой папке **`task_N/`** есть **`TASK.md`** (постановка курса, не редактировать), **`REPORT.md`** (краткий отчёт для ревьюера) и при необходимости **`README.md`** (как запускать локальные шаги). Отдельные **Markdown-артефакты** постановки (например `task_1/otchet_*.md`, `task_2/kimetsu_articles/DICTIONARY.md`, `task_4/DIALOGS.md`, `task_5/LOG_EXECUTION.md`, `task_6/LOG_EXECUTION.md`, `task_4/prompts/README.md`) **не удаляются** — они часть сдачи.

| Задание | Суть | Документы |
|---------|------|-----------|
| **1** | Сравнение LLM, эмбеддингов, векторных БД; конфигурации сервера | [TASK](task_1/TASK.md) · [REPORT](task_1/REPORT.md) · [отчёт-исследование](task_1/otchet_issledovanie_rag_infrastruktury.md) |
| **2** | Корпус `.txt`, словарь замен, материалы подготовки | [TASK](task_2/TASK.md) · [REPORT](task_2/REPORT.md) · [README](task_2/README.md) |
| **3** | Чанкинг, эмбеддинги Yandex, ChromaDB в `databases/good/chroma_db` | [TASK](task_3/TASK.md) · [REPORT](task_3/REPORT.md) · [README](task_3/README.md) |
| **4** | RAG + промпты + REPL, режим защиты от injection | [TASK](task_4/TASK.md) · [REPORT](task_4/REPORT.md) · [README](task_4/README.md) |
| **5** | Вредоносный документ в `databases/bad`, демо утечки / защиты | [TASK](task_5/TASK.md) · [REPORT](task_5/REPORT.md) · [README](task_5/README.md) |
| **6** | Инкрементальное обновление индекса, лог JSONL, cron | [TASK](task_6/TASK.md) · [REPORT](task_6/REPORT.md) · [README](task_6/README.md) |
| **7** | Gap-индекс, golden-набор, автооценка, логи, диаграмма | [TASK](task_7/TASK.md) · [REPORT](task_7/REPORT.md) · [README](task_7/README.md) |

---

## Структура (кратко)

- **`databases/good/chroma_db`** — основной индекс базы знаний.  
- **`databases/bad/chroma_db`** — индекс с вредоносным чанком (задание 5).  
- **`task_7/chroma_db_gap`** — индекс без части сущностей (задание 7).  
- **`utils/`** — оболочки запуска сценариев из корня.

---

## Переменные окружения

- **`YANDEX_CLOUD_FOLDER`** — идентификатор каталога в Yandex Cloud.  
- **`YANDEX_CLOUD_API_KEY`** — ключ для YandexGPT и эмбеддингов в `task_4` / общем пайплайне.  
- **`YANDEX_IAM_TOKEN`** — для `task_3/embedding_client.py` и `build_index.py`, если используется схема с IAM.
