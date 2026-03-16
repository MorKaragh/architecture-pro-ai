"""
RAG-пайплайн: поиск по векторной базе (task_3) + промпт (Few-shot, CoT) + YandexGPT.
Использует тот же энкодер и индекс, что и task_3. Вызов LLM — как в gpt_tryout/index.py.
Для эмбеддингов и для LLM используем одни и те же переменные: YANDEX_CLOUD_API_KEY, YANDEX_CLOUD_FOLDER.
"""
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TASK_3 = REPO_ROOT / "task_3"

import chromadb
import numpy as np
import requests
from openai import OpenAI

CHROMA_PATH = TASK_3 / "chroma_db"
COLLECTION_NAME = "knowledge_base"
TOP_K = 5

# Те же переменные, что и в gpt_tryout — одного набора хватает и для эмбеддингов, и для LLM
YANDEX_CLOUD_MODEL = os.getenv("YANDEX_CLOUD_MODEL", "yandexgpt-lite")
YANDEX_CLOUD_API_KEY = os.getenv("YANDEX_CLOUD_API_KEY")
YANDEX_CLOUD_FOLDER = os.getenv("YANDEX_CLOUD_FOLDER")

EMBED_URL = "https://ai.api.cloud.yandex.net:443/foundationModels/v1/textEmbedding"


def get_embedding(text: str, text_type: str = "doc") -> np.ndarray:
    """
    Эмбеддинг через Yandex API с авторизацией по API-ключу (как в gpt_tryout).
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
    payload = {"modelUri": model_uri, "text": text}
    resp = requests.post(EMBED_URL, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    return np.array(resp.json()["embedding"], dtype="float32")

# Few-shot примеры из той же предметной области (база — фандом про варку пельменей и алкашей)
FEW_SHOT_EXAMPLES = """
Q: Что такое варка на сильном огне?
A: Варка на сильном огне — одно из шести основных способов варки, произошедших от варки при дневном свете. Это способ варки, имитирующий пламя; большинство стилей включают мощные одиночные удары. Разработана предком семьи Рябинин. К пользователям относятся Сергей Рябинин и Кирилл Рябинин.

Q: Кто такой Марк Козлов?
A: Марк Козлов — первый в своём роде алкаш, прародитель остальных алкашей, антагонист аниме и манги «Половник, выводящий из запоя». Убил большинство из семьи Печников и обратил Настю в алкаша. Имеет семь сердец и пять мозгов, способен менять внешность (мужчина, женщина, ребёнок).
"""

SYSTEM_COT = """Ты помощник по базе знаний о вселенной «Половник, выводящий из запоя» (варщики пельменей, алкаши, стили варки, персонажи).
Правила:
1. Сначала кратко опиши шаги: что ищешь, что нашёл в приведённых фрагментах.
2. Затем дай чёткий ответ, опираясь только на эти фрагменты.
3. Если в приведённых фрагментах нет ответа на вопрос — честно напиши: «Я не знаю» (и не придумывай)."""


def search(query: str, top_k: int = TOP_K):
    """Поиск по индексу task_3: эмбеддинг запроса (query) + ChromaDB."""
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    collection = client.get_collection(name=COLLECTION_NAME)
    query_embedding = get_embedding(query, text_type="query").tolist()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    return results


def build_prompt(user_query: str, chunks_docs: list, chunks_metas: list) -> str:
    """Собирает промпт: инструкция (CoT) + контекст + few-shot + вопрос пользователя."""
    context_parts = []
    for i, (doc, meta) in enumerate(zip(chunks_docs, chunks_metas), 1):
        source = meta.get("title", "?")
        context_parts.append(f"[Фрагмент {i} (источник: {source})]\n{doc}")
    context = "\n\n".join(context_parts)

    prompt = f"""{SYSTEM_COT}

Ниже — фрагменты из базы знаний. Опирайся только на них.

---
{context}
---

Примеры формата ответа (предметная область та же):

{FEW_SHOT_EXAMPLES.strip()}

Q: {user_query}
A:"""
    return prompt


def get_llm_client():
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


def answer(user_query: str, top_k: int = TOP_K) -> str:
    """
    Полный RAG: поиск чанков → сборка промпта (CoT + few-shot + контекст) → ответ LLM.
    """
    if not user_query.strip():
        return "Задайте, пожалуйста, вопрос."

    # Поиск по векторной базе
    results = search(user_query, top_k=top_k)
    docs = results["documents"][0]
    metas = results["metadatas"][0]

    if not docs:
        return "В базе не найдено подходящих фрагментов. Я не знаю."

    prompt = build_prompt(user_query, docs, metas)
    client = get_llm_client()

    response = client.responses.create(
        model=f"gpt://{YANDEX_CLOUD_FOLDER}/{YANDEX_CLOUD_MODEL}",
        input=prompt,
        temperature=0.4,
        max_output_tokens=2048,
    )

    text = response.output[0].content[0].text.strip()
    # Убираем ведущее "A:" / "А:" из ответа модели (остаток формата промпта Q:/A:)
    for prefix in ("A:", "А:"):
        if text.startswith(prefix):
            text = text[len(prefix) :].strip()
            break
    return text
