"""
RAG-пайплайн: поиск по векторной базе (task_3) + промпт (Few-shot, CoT) + YandexGPT.
Промпты загружаются из папки prompts/. Конфиг — переменные окружения (API key, folder).
"""
import os
from pathlib import Path

import chromadb
import numpy as np
import requests
from openai import OpenAI

# --- Конфигурация ---
TASK_4_ROOT = Path(__file__).resolve().parent
REPO_ROOT = TASK_4_ROOT.parent
CHROMA_PATH = REPO_ROOT / "task_3" / "chroma_db"
PROMPTS_DIR = TASK_4_ROOT / "prompts"
COLLECTION_NAME = "knowledge_base"
TOP_K = 5
EMBED_URL = "https://ai.api.cloud.yandex.net:443/foundationModels/v1/textEmbedding"

YANDEX_CLOUD_MODEL = os.getenv("YANDEX_CLOUD_MODEL", "yandexgpt-lite")
YANDEX_CLOUD_API_KEY = os.getenv("YANDEX_CLOUD_API_KEY")
YANDEX_CLOUD_FOLDER = os.getenv("YANDEX_CLOUD_FOLDER")


def _load_prompts() -> dict[str, str]:
    """Загружает шаблоны из prompts/. Кэшируется при первом вызове."""
    if not hasattr(_load_prompts, "_cache"):
        _load_prompts._cache = {
            "system": (PROMPTS_DIR / "system.txt").read_text(encoding="utf-8").strip(),
            "few_shot": (PROMPTS_DIR / "few_shot.txt").read_text(encoding="utf-8").strip(),
            "main": (PROMPTS_DIR / "main.txt").read_text(encoding="utf-8"),
        }
    return _load_prompts._cache


def get_embedding(text: str, text_type: str = "doc") -> np.ndarray:
    """
    Эмбеддинг через Yandex API с авторизацией по API-ключу (те же переменные, что в gpt_tryout).
    text_type: "doc" для чанков, "query" для поискового запроса.
    """
    if not YANDEX_CLOUD_API_KEY or not YANDEX_CLOUD_FOLDER:
        raise RuntimeError(
            "Задайте YANDEX_CLOUD_API_KEY и YANDEX_CLOUD_FOLDER (те же, что для gpt_tryout)"
        )
    model_uri = (
        f"emb://{YANDEX_CLOUD_FOLDER}/text-search-doc/latest"
        if text_type == "doc"
        else f"emb://{YANDEX_CLOUD_FOLDER}/text-search-query/latest"
    )
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {YANDEX_CLOUD_API_KEY}",
        "x-folder-id": YANDEX_CLOUD_FOLDER,
    }
    resp = requests.post(
        EMBED_URL,
        json={"modelUri": model_uri, "text": text},
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    return np.array(resp.json()["embedding"], dtype="float32")


def search(query: str, top_k: int = TOP_K) -> dict:
    """Поиск по индексу task_3: эмбеддинг запроса (query) + ChromaDB."""
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    collection = client.get_collection(name=COLLECTION_NAME)
    query_embedding = get_embedding(query, text_type="query").tolist()
    return collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )


def _format_context(chunks_docs: list, chunks_metas: list) -> str:
    """Форматирует чанки в блок контекста для промпта."""
    parts = []
    for i, (doc, meta) in enumerate(zip(chunks_docs, chunks_metas), 1):
        source = meta.get("title", "?")
        parts.append(f"[Фрагмент {i} (источник: {source})]\n{doc}")
    return "\n\n".join(parts)


def build_prompt(user_query: str, chunks_docs: list, chunks_metas: list) -> str:
    """Собирает промпт из шаблонов в prompts/ и переданного контекста."""
    prompts = _load_prompts()
    context = _format_context(chunks_docs, chunks_metas)
    return prompts["main"].format(
        system=prompts["system"],
        context=context,
        few_shot=prompts["few_shot"],
        user_query=user_query,
    )


def _get_llm_client() -> OpenAI:
    """Клиент YandexGPT (как в gpt_tryout/index.py)."""
    if not YANDEX_CLOUD_API_KEY or not YANDEX_CLOUD_FOLDER:
        raise RuntimeError(
            "Задайте переменные окружения YANDEX_CLOUD_API_KEY и YANDEX_CLOUD_FOLDER"
        )
    return OpenAI(
        api_key=YANDEX_CLOUD_API_KEY,
        base_url="https://ai.api.cloud.yandex.net/v1",
        project=YANDEX_CLOUD_FOLDER,
    )


def _normalize_response(text: str) -> str:
    """Убирает ведущее «A:» / «А:» из ответа модели (остаток формата Q:/A: в промпте)."""
    text = text.strip()
    for prefix in ("A:", "А:"):
        if text.startswith(prefix):
            return text[len(prefix) :].strip()
    return text


def answer(user_query: str, top_k: int = TOP_K) -> str:
    """
    Полный RAG: поиск чанков → сборка промпта из шаблонов → вызов YandexGPT → нормализация ответа.
    """
    query = user_query.strip()
    if not query:
        return "Задайте, пожалуйста, вопрос."

    results = search(query, top_k=top_k)
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    if not docs:
        return "В базе не найдено подходящих фрагментов. Я не знаю."

    prompt = build_prompt(query, docs, metas)
    client = _get_llm_client()
    response = client.responses.create(
        model=f"gpt://{YANDEX_CLOUD_FOLDER}/{YANDEX_CLOUD_MODEL}",
        input=prompt,
        temperature=0.4,
        max_output_tokens=2048,
    )
    raw_text = response.output[0].content[0].text
    return _normalize_response(raw_text)
