# Техническое описание (руководство для продолжения работы)

Документ описывает, что сделано в техническом плане, где что лежит и что делать при сбоях. Для продолжения работы в новой сессии или при передаче задачи.

---

## 1. Общая картина

- **Задание 3:** векторный индекс базы знаний для семантического поиска.
- **База знаний:** только чтение из `task_2/final_fandom/` — все файлы `*.txt`. Файлы в этой папке **не изменяются** скриптами.
- **Эмбеддинги:** Yandex Cloud API (Foundation Models, textEmbedding) — модели `text-search-doc` и `text-search-query`.
- **Векторная БД:** ChromaDB (локально, папка на диске). Метрика поиска — cosine.

---

## 2. Структура репозитория (релевантные части)

```
architecture-pro-ai/
├── TECH_MAN.md              # этот файл
├── gpt_tryout/
│   ├── embedding.py         # демо-скрипт семантического поиска (Пушкин/ромашка)
│   └── venv/                # venv с requests, numpy, scipy; для task_3 туда добавлены chromadb, langchain-text-splitters
├── task_2/
│   └── final_fandom/        # база знаний: .txt файлы, только чтение
└── task_3/
    ├── embedding_client.py  # клиент Yandex API (get_embedding)
    ├── build_index.py       # построение индекса: чанки → эмбеддинги → ChromaDB
    ├── query_example.py     # пример запроса к индексу
    ├── chroma_db/           # каталог индекса ChromaDB (создаётся после первого успешного build_index.py)
    ├── requirements.txt     # chromadb, langchain-text-splitters, numpy, requests
    └── README.md            # описание задания и как запускать
```

---

## 3. Что сделано по шагам

### 3.1 Эмбеддинги (Yandex API)

- **Файл:** `task_3/embedding_client.py`.
- **Переменные окружения:** `YANDEX_CLOUD_FOLDER`, `YANDEX_IAM_TOKEN`. Без них скрипты падают.
- **Функции:** `get_embedding(text, text_type="doc"|"query")` — один запрос к API, возвращает вектор `np.ndarray` (float32).
- **Эндпоинт:** `https://ai.api.cloud.yandex.net:443/foundationModels/v1/textEmbedding`.

### 3.2 Чанкирование

- В `build_index.py`: **RecursiveCharacterTextSplitter** (LangChain).
- Параметры: `chunk_size=1000` символов, `chunk_overlap=150`.
- Для каждого чанка сохраняются: `source` (путь к файлу), `title` (имя файла без .txt), `chunk_id` вида `{title}_{i}`.

### 3.3 Построение индекса

- **Скрипт:** `task_3/build_index.py`.
- Читает все `*.txt` из `task_2/final_fandom/` (путь задаётся относительно корня репозитория: `REPO_ROOT / "task_2" / "final_fandom"`).
- Удаляет старую папку `task_3/chroma_db/` (если есть) и создаёт коллекцию заново.
- Коллекция ChromaDB: имя `knowledge_base`, метрика **cosine** (`configuration={"hnsw": {"space": "cosine"}}`).
- Эмбеддинги запрашиваются **по одному** (батч-API у Yandex в коде не используется). При большом числе чанков выполнение занимает несколько минут.

### 3.4 Поиск по индексу

- **Скрипт:** `task_3/query_example.py`.
- Загружает коллекцию из `task_3/chroma_db/`, эмбеддинг запроса через `get_embedding(..., text_type="query")`, поиск по ChromaDB, вывод топ-5 чанков с метаданными и расстоянием.

---

## 4. Зависимости и окружение

- **Python:** 3.x (использовался 3.12).
- **Установка для task_3:**  
  `pip install -r task_3/requirements.txt`  
  (chromadb, langchain-text-splitters, numpy, requests).
- **Venv:** можно использовать `gpt_tryout/venv` (туда уже ставились chromadb и langchain-text-splitters) или отдельный venv в `task_3/`. Запуск из корня или из `task_3/` с учётом того, что импорт идёт `from embedding_client import ...`, поэтому текущая директория при запуске должна быть `task_3/` (или в PYTHONPATH должна быть `task_3`).

---

## 5. Как продолжить работу в другой сессии

1. Активировать venv (например `gpt_tryout/venv` или `task_3/venv`) и проверить:  
   `pip list | grep -E 'chromadb|langchain'`.
2. Выставить `YANDEX_CLOUD_FOLDER` и `YANDEX_IAM_TOKEN`.
3. Пересобрать индекс при изменении базы знаний или параметров чанков:  
   `cd task_3 && python build_index.py`.
4. Проверить поиск:  
   `python query_example.py "тестовый запрос"`.

Дальнейшие шаги по заданию (например, интеграция с ботом или LLM) — подключать к `task_3/embedding_client.py` и к индексу в `task_3/chroma_db/` (через ChromaDB API, как в `query_example.py`).

---

## 6. Если что-то пошло не так

### 6.1 Ошибки при запуске `build_index.py` или `query_example.py`

- **`FileNotFoundError: Папка базы знаний не найдена`**  
  Проверить, что из текущей директории путь к репозиторию верный: `build_index.py` считает корень как `Path(__file__).resolve().parent.parent`. Запускать лучше из `task_3/`:  
  `cd task_3 && python build_index.py`.

- **`KeyError: 'embedding'` или 401/403 от API**  
  Проверить переменные окружения: `YANDEX_CLOUD_FOLDER`, `YANDEX_IAM_TOKEN`. Токен должен быть действующим (IAM-токены имеют срок жизни). При 403 — права каталога/сервисного аккаунта в Yandex Cloud.

- **Ошибка от ChromaDB при `create_collection(..., configuration=...)`**  
  В старых версиях ChromaDB параметр `configuration` может отличаться или отсутствовать. Вариант обхода: в `build_index.py` заменить вызов на  
  `client.get_or_create_collection(name="knowledge_base")`  
  и убрать аргумент `configuration`. Поиск будет по метрике по умолчанию (часто L2); порядок результатов может немного отличаться от cosine.

### 6.2 Индекс не найден при запросе

- **Папки `task_3/chroma_db/` нет или она пустая**  
  Сначала выполнить `python build_index.py` и дождаться сообщения «Индекс сохранён в ...».

- **`get_collection` падает (коллекция не найдена)**  
  Убедиться, что запускаете из той же директории/проекта, где запускался `build_index.py` (путь к `chroma_db` задаётся относительно `task_3/`).

### 6.3 Долгая работа или таймауты

- Эмбеддинги запрашиваются по одному; при сотнях чанков возможны десятки секунд или минуты. Таймауты при необходимости увеличить в `embedding_client.py` (например, в `requests.post(..., timeout=60)`).
- При лимитах API Yandex можно добавить паузу между запросами в цикле в `build_index.py` (например, `time.sleep(0.2)` после каждого `get_embedding`).

### 6.4 Изменение базы знаний или параметров чанков

- Файлы в `task_2/final_fandom/` менять вручную можно; скрипты их только читают.
- После изменения текстов или после смены `CHUNK_SIZE` / `CHUNK_OVERLAP` в `build_index.py` нужно заново запустить `build_index.py` — он пересоздаёт `chroma_db/` и коллекцию.

---

## 7. Полезные команды

```bash
# Из корня репозитория
cd task_3
export YANDEX_CLOUD_FOLDER="<folder_id>"
export YANDEX_IAM_TOKEN="<token>"

# Сборка индекса (первый раз или после изменений в final_fandom / параметрах чанков)
python build_index.py

# Поиск: свой запрос
python query_example.py "Как варить пельмени на сильном огне?"

# Поиск: встроенные тестовые запросы
python query_example.py
```

---

## 8. Связь с другими заданиями

- **Задание 1:** выбор модели эмбеддингов и векторной БД (ChromaDB, облачный API) описан в отчёте по заданию 1; в курсе принято использовать облачные API (Yandex), без локальных LLM.
- **Задание 2:** база знаний подготовлена в `task_2/final_fandom/`.
- **Дальше (бот, RAG):** брать контекст из `query_example.search()` (или аналога) и передавать в LLM для ответа пользователю.
