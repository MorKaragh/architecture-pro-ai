"""
Клиент для получения эмбеддингов через Yandex Cloud Foundation Models API.
Используется при построении индекса (doc) и при поиске (query).
"""
import os
from typing import List, Union

import numpy as np
import requests

# Переменные окружения: YANDEX_CLOUD_FOLDER, YANDEX_IAM_TOKEN
FOLDER_ID = os.getenv("YANDEX_CLOUD_FOLDER")
IAM_TOKEN = os.getenv("YANDEX_IAM_TOKEN")

EMBED_URL = "https://ai.api.cloud.yandex.net:443/foundationModels/v1/textEmbedding"
DOC_URI = f"emb://{FOLDER_ID}/text-search-doc/latest"
QUERY_URI = f"emb://{FOLDER_ID}/text-search-query/latest"

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {IAM_TOKEN}",
    "x-folder-id": f"{FOLDER_ID}",
}


def get_embedding(text: str, text_type: str = "doc") -> np.ndarray:
    """
    Возвращает эмбеддинг текста (вектор).
    text_type: "doc" — для чанков документов, "query" — для поискового запроса.
    """
    model_uri = DOC_URI if text_type == "doc" else QUERY_URI
    payload = {"modelUri": model_uri, "text": text}
    resp = requests.post(EMBED_URL, json=payload, headers=HEADERS)
    resp.raise_for_status()
    return np.array(resp.json()["embedding"], dtype="float32")


def get_embeddings_batch(texts: List[str], text_type: str = "doc") -> List[np.ndarray]:
    """Последовательно получает эмбеддинги для списка текстов (API по одному запросу на текст)."""
    return [get_embedding(t, text_type) for t in texts]
