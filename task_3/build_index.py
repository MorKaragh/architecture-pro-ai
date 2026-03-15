"""
Построение векторного индекса базы знаний (задание 3).
Читает .txt из папки final_fandom, режет на чанки, получает эмбеддинги через Yandex API,
сохраняет индекс в ChromaDB. Файлы в final_fandom не изменяются.
"""
import os
import time
from pathlib import Path

import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter

from embedding_client import get_embedding

# Путь к базе знаний (только чтение). Относительно корня репозитория.
REPO_ROOT = Path(__file__).resolve().parent.parent
KB_PATH = REPO_ROOT / "task_2" / "final_fandom"
# Папка, куда сохраняем индекс ChromaDB (внутри task_3)
CHROMA_PATH = Path(__file__).resolve().parent / "chroma_db"

# Чанки: ~100–300 слов ≈ 600–1800 символов. Берём 1000 символов, перекрытие 150.
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


def load_documents():
    """Загружает все .txt из final_fandom. Возвращает список (путь_файла, текст)."""
    if not KB_PATH.is_dir():
        raise FileNotFoundError(f"Папка базы знаний не найдена: {KB_PATH}")
    docs = []
    for path in sorted(KB_PATH.glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        docs.append((str(path), path.stem, text))
    return docs


def chunk_documents(docs):
    """Разбивает документы на чанки с сохранением источника и позиции."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks_meta = []
    for file_path, title, text in docs:
        chunks = splitter.split_text(text)
        for i, chunk_text in enumerate(chunks):
            chunks_meta.append(
                {
                    "text": chunk_text,
                    "source": file_path,
                    "title": title,
                    "chunk_id": f"{title}_{i}",
                }
            )
    return chunks_meta


def build_and_save_index():
    """Собирает чанки, получает эмбеддинги, сохраняет индекс в ChromaDB."""
    print("Загрузка документов из", KB_PATH, "...")
    docs = load_documents()
    print(f"Загружено файлов: {len(docs)}")

    print("Разбиение на чанки...")
    chunks = chunk_documents(docs)
    print(f"Получено чанков: {len(chunks)}")

    # Очищаем старый индекс и создаём коллекцию заново
    if CHROMA_PATH.exists():
        import shutil
        shutil.rmtree(CHROMA_PATH)
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    collection = client.create_collection(
        name="knowledge_base",
        metadata={"description": "База знаний final_fandom"},
        configuration={"hnsw": {"space": "cosine"}},  # косинусная метрика для текстовых эмбеддингов
    )

    # Эмбеддинги по одному (API не батчит). Можно добавить небольшую задержку при лимитах.
    embeddings = []
    t0 = time.perf_counter()
    for i, meta in enumerate(chunks):
        emb = get_embedding(meta["text"], text_type="doc")
        embeddings.append(emb.tolist())
        if (i + 1) % 20 == 0:
            print(f"  эмбеддингов: {i + 1}/{len(chunks)}")
    elapsed = time.perf_counter() - t0
    print(f"Эмбеддинги получены за {elapsed:.1f} с")

    # Добавляем в Chroma: id, embedding, document (текст), metadata
    ids = [m["chunk_id"] for m in chunks]
    documents = [m["text"] for m in chunks]
    metadatas = [
        {"source": m["source"], "title": m["title"], "chunk_id": m["chunk_id"]}
        for m in chunks
    ]
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )
    print(f"Индекс сохранён в {CHROMA_PATH}")
    return len(chunks), elapsed


if __name__ == "__main__":
    n_chunks, elapsed = build_and_save_index()
    print(f"Готово. Чанков в индексе: {n_chunks}, время: {elapsed:.1f} с")
