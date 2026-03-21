"""
Пример запроса к векторному индексу: поиск по смыслу и вывод найденных чанков.
Запуск: python query_example.py "ваш запрос"
Или без аргумента — выполняются тестовые запросы из списка.
"""
import argparse
from pathlib import Path

import chromadb

from embedding_client import get_embedding

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = REPO_ROOT / "databases" / "good" / "chroma_db"
COLLECTION_NAME = "knowledge_base"
TOP_K = 5


def search(query: str, db_path: Path, top_k: int = TOP_K):
    """Возвращает top_k наиболее релевантных чанков для запроса."""
    client = chromadb.PersistentClient(path=str(db_path))
    collection = client.get_collection(name=COLLECTION_NAME)
    query_embedding = get_embedding(query, text_type="query").tolist()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    return results


def main():
    parser = argparse.ArgumentParser(description="Пример поиска по ChromaDB индексу.")
    parser.add_argument("query", nargs="*", help="Поисковый запрос (если не передан, запускаются тестовые)")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH, help="Путь к папке ChromaDB")
    parser.add_argument("--top-k", type=int, default=TOP_K, help="Количество возвращаемых чанков")
    args = parser.parse_args()

    if args.query:
        queries = [" ".join(args.query)]
    else:
        queries = [
            "Как варить пельмени на сильном огне?",
            "Кто такой Марк Козлов?",
            "Что такое Гора Рассольная?",
        ]

    for q in queries:
        print("Запрос:", q)
        print("-" * 60)
        res = search(q, db_path=args.db_path, top_k=args.top_k)
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
