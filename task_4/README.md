# Задание 4 — RAG-бот (Few-shot, Chain-of-Thought)

Консольный бот: ChromaDB (`databases/good/chroma_db`) + шаблоны в `prompts/` + YandexGPT.

## Запуск

Рекомендуется общий venv в **корне репозитория** и меню **`./main_interactive.sh`** (пункты для бота и индексов).

Прямой запуск из корня:

```bash
./venv/bin/python task_4/bot.py [--db-path ПУТЬ] [--defense off|protected]
```

Переменные окружения: `YANDEX_CLOUD_FOLDER`, `YANDEX_CLOUD_API_KEY` (эмбеддинги и LLM).

## Файлы

| Файл / папка | Назначение |
|--------------|------------|
| `rag.py` | Поиск, сборка промпта, защита `protected`, вызов модели |
| `bot.py` | REPL |
| `prompts/system.txt` | Системная инструкция (шаги → ответ, отказ при отсутствии данных) |
| `prompts/few_shot.txt` | Few-shot примеры |
| `prompts/main.txt` | Шаблон с плейсхолдерами `{system}`, `{context}`, `{few_shot}`, `{user_query}` |
| `prompts/README.md` | Краткое описание шаблонов (артефакт задания) |
| `DIALOGS.md` | Примеры диалогов с оценкой качества (артефакт задания) |

Тон и правила меняются правкой `.txt` в `prompts/` без изменения кода.
