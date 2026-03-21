# architecture-pro-ai

## Что сделано по заданиям

1. `task_1` — анализ моделей и инфраструктуры
   - Сформированы рекомендации по выбору LLM/эмбеддингов и векторной базы (см. `task_1/otchet_issledovanie_rag_infrastruktury.md`).

2. `task_2` — подготовка базы знаний
   - Подготовлен набор документов `task_2/final_fandom/` (исходные `.txt`, которые используются для индексации).

3. `task_3` — векторный индекс
   - Скрипт `task_3/build_index.py` строит ChromaDB в `databases/good/chroma_db/` на основе документов из `task_2/final_fandom/`.

4. `task_4` — RAG-бот (few-shot)
   - Реализован пайплайн RAG: поиск по ChromaDB + сборка промпта по шаблонам из `task_4/prompts/` + генерация ответа через YandexGPT.
   - Запуск: консольный REPL `task_4/bot.py` (режим защиты включается параметром `--defense off|protected`).

5. `task_5` — демонстрация prompt-injection и защит
   - Сделана отдельная “плохая” база: `databases/bad/chroma_db` (оригинальная good-база не портится).
   - Добавлен “злонамеренный” документ `task_5/malicious_doc.txt`, он проиндексирован скриптом `task_5/index_malicious_doc.py` в `databases/bad/chroma_db`.
   - В `task_4/rag.py` добавлены режимы:
     - `off` — без защит: демонстрирует уязвимость (бот может вывести `swordfish`).
     - `protected` — Pre-prompt + post-filter/sanitization: подозрительные чанки отбрасываются, утечка не происходит.

## Переменные окружения

Нужны для работы с Yandex:
- `YANDEX_CLOUD_FOLDER`
- `YANDEX_CLOUD_API_KEY`
- `YANDEX_IAM_TOKEN` 

## Запуск сценариев

Интерактивное меню (боты, индексация, задания 3–7):

- `./main_interactive.sh` — главное меню интерактивной работы со сценариями

Прямой запуск отдельных сценариев — скрипты в `utils/` (например `utils/run_bot_normal.sh`). Полный список пунктов меню совпадает с именами `utils/run_*.sh`.

Перед демонстрацией task_5 при необходимости (однократно) переиндексируйте вредоносный документ:

- `./utils/run_task5_index_malicious.sh`