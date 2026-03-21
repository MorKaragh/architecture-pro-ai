#!/usr/bin/env python3
"""
Task 7: отдельная "испорченная" база знаний для оценки покрытия.

Важно: скрипт НЕ трогает рабочую базу `databases/good/chroma_db`.
Он собирает новый индекс в `task_7/chroma_db_gap`.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import time
from pathlib import Path

import chromadb
import requests
from langchain_text_splitters import RecursiveCharacterTextSplitter


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = REPO_ROOT / "task_2" / "final_fandom"
DEFAULT_DB_PATH = REPO_ROOT / "task_7" / "chroma_db_gap"
DEFAULT_MANIFEST_PATH = REPO_ROOT / "task_7" / "gap_index_manifest.json"
COLLECTION_NAME = "knowledge_base"

DEFAULT_EXCLUDE = "Константин,Марк_Козлов,Варка_при_луне"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
EMBED_RETRIES = 5
EMBED_RETRY_SLEEP_SEC = 2.0


EMBED_URL = "https://ai.api.cloud.yandex.net:443/foundationModels/v1/textEmbedding"


def _get_embedding(text: str, text_type: str = "doc"):
    folder_id = os.getenv("YANDEX_CLOUD_FOLDER")
    api_key = os.getenv("YANDEX_CLOUD_API_KEY")
    iam_token = os.getenv("YANDEX_IAM_TOKEN")
    if not folder_id:
        raise RuntimeError("YANDEX_CLOUD_FOLDER is required")

    model_uri = (
        f"emb://{folder_id}/text-search-doc/latest"
        if text_type == "doc"
        else f"emb://{folder_id}/text-search-query/latest"
    )

    auth_header = None
    if api_key:
        auth_header = f"Api-Key {api_key}"
    elif iam_token:
        auth_header = f"Bearer {iam_token}"
    if not auth_header:
        raise RuntimeError("Set YANDEX_CLOUD_API_KEY or YANDEX_IAM_TOKEN")

    headers = {
        "Content-Type": "application/json",
        "Authorization": auth_header,
        "x-folder-id": folder_id,
    }
    resp = requests.post(EMBED_URL, json={"modelUri": model_uri, "text": text}, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()["embedding"]


def _collect_docs(source_dir: Path, exclude_titles: set[str]) -> tuple[list[tuple[Path, str, str]], list[str]]:
    if not source_dir.is_dir():
        raise FileNotFoundError(f"source dir not found: {source_dir}")

    included: list[tuple[Path, str, str]] = []
    excluded_found: list[str] = []

    for p in sorted(source_dir.rglob("*.txt")):
        title = p.stem
        if title in exclude_titles:
            excluded_found.append(title)
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        included.append((p, title, text))
    return included, sorted(set(excluded_found))


def _chunk_docs(docs: list[tuple[Path, str, str]]) -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    out: list[dict] = []
    for path, title, text in docs:
        chunks = splitter.split_text(text)
        for i, chunk in enumerate(chunks):
            out.append(
                {
                    "id": f"task7__{title}_{i}",
                    "text": chunk,
                    "title": title,
                    "source": str(path),
                    "chunk_id": i,
                }
            )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Build separate degraded DB for task_7")
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--manifest-path", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--exclude", type=str, default=DEFAULT_EXCLUDE, help="Comma-separated file stems")
    args = parser.parse_args()

    exclude_titles = {x.strip() for x in args.exclude.split(",") if x.strip()}
    docs, excluded_found = _collect_docs(args.source_dir, exclude_titles)
    chunks = _chunk_docs(docs)

    if args.db_path.exists():
        shutil.rmtree(args.db_path)
    args.db_path.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(args.db_path))
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Task 7 degraded coverage DB"},
        configuration={"hnsw": {"space": "cosine"}},
    )

    t0 = time.perf_counter()
    embeddings = []
    for i, ch in enumerate(chunks):
        last_err: Exception | None = None
        emb = None
        for attempt in range(1, EMBED_RETRIES + 1):
            try:
                emb = _get_embedding(ch["text"], text_type="doc")
                break
            except Exception as e:  # noqa: BLE001
                last_err = e
                if attempt < EMBED_RETRIES:
                    time.sleep(EMBED_RETRY_SLEEP_SEC)
        if emb is None:
            raise RuntimeError(f"embedding failed at chunk {i} after {EMBED_RETRIES} retries: {last_err!r}")
        embeddings.append(emb)
        if (i + 1) % 50 == 0:
            print(f"embeddings: {i + 1}/{len(chunks)}")
    elapsed = round(time.perf_counter() - t0, 3)

    collection.add(
        ids=[c["id"] for c in chunks],
        embeddings=embeddings,
        documents=[c["text"] for c in chunks],
        metadatas=[
            {
                "title": c["title"],
                "source": c["source"],
                "task": "task_7_gap",
                "chunk_id": c["chunk_id"],
            }
            for c in chunks
        ],
    )

    manifest = {
        "source_dir": str(args.source_dir),
        "db_path": str(args.db_path),
        "collection_name": COLLECTION_NAME,
        "exclude_requested": sorted(exclude_titles),
        "exclude_found": excluded_found,
        "files_included": len(docs),
        "chunks_total": len(chunks),
        "embedding_elapsed_sec": elapsed,
    }
    args.manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(manifest, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
