# architecture-pro-ai

## Что сделано по заданиям

1. `task_1` — анализ моделей и инфраструктуры
   - Сформированы рекомендации по выбору LLM/эмбеддингов и векторной базы (см. `task_1/otchet_issledovanie_rag_infrastruktury.md`).

2. `task_2` — подготовка базы знаний
   - Подготовлен набор документов `task_2/final_fandom/` (исходные `.txt`, которые используются для индексации).

3. `task_3` — векторный индекс
   - Скрипт `task_3/build_index.py` строит ChromaDB в `task_3/chroma_db/` на основе документов из `task_2/final_fandom/`.

4. `task_4` — RAG-бот (few-shot)
   - Реализован пайплайн RAG: поиск по ChromaDB + сборка промпта по шаблонам из `task_4/prompts/` + генерация ответа через YandexGPT.
   - Запуск: консольный REPL `task_4/bot.py` (режим защиты включается параметром `--defense off|protected`).

5. `task_5` — демонстрация prompt-injection и защит
   - Сделана копия индекса: `task_3/chroma_db` -> `task_5/chroma_db` (оригинальная база не портится).
   - Добавлен “злонамеренный” документ `task_5/malicious_doc.txt`, он проиндексирован скриптом `task_5/index_malicious_doc.py` в `task_5/chroma_db`.
   - В `task_4/rag.py` добавлены режимы:
     - `off` — без защит: демонстрирует уязвимость (бот может вывести `swordfish`).
     - `protected` — Pre-prompt + post-filter/sanitization: подозрительные чанки отбрасываются, утечка не происходит.

## Переменные окружения

Нужны для работы с Yandex:
- `YANDEX_CLOUD_FOLDER`
- `YANDEX_CLOUD_API_KEY`
- `YANDEX_IAM_TOKEN` (нужен для индексации в task_3/task_5, если нет `YANDEX_CLOUD_API_KEY`)

## Запуск бота

Используйте удобные скрипты в корне:
- `./run_bot_normal.sh` — нормальная база (`task_3/chroma_db`), режим `--defense off`
- `./run_bot_bad_protected.sh` — плохая база (`task_5/chroma_db`), безопасный режим `--defense protected`
- `./run_bot_bad_unsafe.sh` — плохая база (`task_5/chroma_db`), небезопасный режим `--defense off`

Перед запуском task_5 при необходимости можно (однократно) переиндексировать “злонамеренный” документ:
- `task_5/venv/bin/python task_5/index_malicious_doc.py`