# Задание 3. Векторный индекс базы знаний

**Быстрый запуск из корня репозитория** (общий `venv`): `./utils/run_task3_build_index.sh`, `./utils/run_task3_query_example.sh "ваш запрос"`.

## Модель эмбеддингов

- **Название:** Yandex Foundation Models — `text-search-doc` (для документов/чанков) и `text-search-query` (для запросов).
- **API:** [Yandex Cloud — Foundation Models, textEmbedding](https://cloud.yandex.ru/docs/yandexgpt/api-ref/embeddings).
- **Размер эмбеддингов:** задаётся моделью (уточняется по ответу API при первом запуске).

## База знаний

- **Путь:** `task_2/final_fandom/` (в репозитории). Используются только файлы `*.txt`. Исходные файлы не изменяются.

## Результат индексации

- **Индекс:** папка `databases/good/chroma_db/` (ChromaDB, персистентное хранилище).
- **Чанков в индексе:** см. вывод скрипта `build_index.py` после запуска (или укажите число после первого прогона).
- **Время генерации:** см. вывод `build_index.py`.

## Как запустить

1. Установить зависимости (лучше в venv):
   ```bash
   cd task_3
   python -m venv venv
   source venv/bin/activate   # или venv\Scripts\activate на Windows
   pip install -r requirements.txt
   ```

2. Задать переменные окружения Yandex Cloud:
   - `YANDEX_CLOUD_FOLDER` — ID каталога.
   - `YANDEX_IAM_TOKEN` — IAM-токен.

3. Построить индекс (читает только из `task_2/final_fandom/`, не меняет файлы там):
   ```bash
   python build_index.py
   ```

4. Пример запроса к индексу:
   ```bash
   python query_example.py "Как варить пельмени на сильном огне?"
   ```
   Без аргументов скрипт выполнит несколько тестовых запросов и выведет найденные чанки.

## Файлы

- `build_index.py` — построение и сохранение индекса (чанки + эмбеддинги в ChromaDB).
- `query_example.py` — пример поиска по индексу: запрос + топ найденных чанков.
- `embedding_client.py` — получение эмбеддингов через Yandex API.
