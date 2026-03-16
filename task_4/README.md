# Задание 4. RAG-бот с Few-shot и Chain-of-Thought

Консольный бот: поиск по векторной базе (task_3), ответы через YandexGPT с техниками Few-shot и CoT.

## Зависимости

- Индекс и эмбеддинги из **task_3** (ChromaDB в `task_3/chroma_db/`, эмбеддинги — Yandex API).
- Вызов LLM — как в **gpt_tryout/index.py** (OpenAI-совместимый клиент, Yandex Cloud).

## Как запустить

1. Собрать индекс в task_3 (если ещё не собран):
   ```bash
   cd task_3
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   export YANDEX_CLOUD_FOLDER="<folder_id>"
   export YANDEX_IAM_TOKEN="<iam_token>"
   python build_index.py
   ```

2. В task_4 создать venv и установить зависимости:
   ```bash
   cd task_4
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Переменные окружения для бота (те же, что для gpt_tryout):
   - `YANDEX_CLOUD_FOLDER` — ID каталога.
   - `YANDEX_CLOUD_API_KEY` — для эмбеддингов (поиск) и для YandexGPT (ответы). Оба запроса идут с этим ключом.

4. Запуск (из каталога **task_4**):
   ```bash
   python bot.py
   ```
   Скрипт сам подхватывает `task_3` для импорта `embedding_client` и пути к `chroma_db`.

## Файлы

- `rag.py` — пайплайн RAG: поиск, сборка промпта из шаблонов, вызов YandexGPT.
- `bot.py` — консольный REPL.
- `prompts/` — шаблоны промптов (system.txt, few_shot.txt, main.txt); правка без изменения кода.
- `DIALOGS.md` — примеры диалогов (успешные и ответ «Я не знаю»).

## Результат по заданию

- Модуль RAG: загрузка индекса, приём запроса, поиск, промптинг (few-shot, CoT), генерация ответа.
- Запускаемый скрипт: `python bot.py`.
- Примеры диалогов: см. `DIALOGS.md`.
