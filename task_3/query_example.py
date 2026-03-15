"""
Пример запроса к векторному индексу: поиск по смыслу и вывод найденных чанков.
Запуск: python query_example.py "ваш запрос"
Или без аргумента — выполняются тестовые запросы из списка.
"""
import sys
from pathlib import Path

import chromadb

from embedding_client import get_embedding

CHROMA_PATH = Path(__file__).resolve().parent / "chroma_db"
COLLECTION_NAME = "knowledge_base"
TOP_K = 5


def search(query: str, top_k: int = TOP_K):
    """Возвращает top_k наиболее релевантных чанков для запроса."""
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    collection = client.get_collection(name=COLLECTION_NAME)
    query_embedding = get_embedding(query, text_type="query").tolist()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    return results


def main():
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        queries = [query]
    else:
        queries = [
            "Как варить пельмени на сильном огне?",
            "Кто такой Марк Козлов?",
            "Что такое Гора Рассольная?",
        ]

    for q in queries:
        print("Запрос:", q)
        print("-" * 60)
        res = search(q)
        docs = res["documents"][0]
        metas = res["metadatas"][0]
        dists = res["distances"][0]
        for i, (doc, meta, d) in enumerate(zip(docs, metas, dists), 1):
            print(f"[{i}] (источник: {meta['title']}, расстояние: {d:.4f})")
            print(doc[:400] + ("..." if len(doc) > 400 else ""))
            print()
        print()


if __name__ == "__main__":
    main()
