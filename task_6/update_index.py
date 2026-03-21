"""
Задание 6: автоматическое ежедневное обновление базы знаний.

Скрипт инкрементально обходит источник данных (папку с *.txt),
выделяет чанки, получает эмбеддинги и обновляет ChromaDB.

Режимы эмбеддингов:
- online: Yandex embedding API через `task_3/embedding_client.py`
- stub: детерминированные "фейковые" эмбеддинги (для локальной проверки пайплайна без ключей).

Важно: в `stub`-режиме индекс по умолчанию пишется в отдельную коллекцию, чтобы не загрязнять реальный индекс из `task_3`.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import json
import os
import sys
import time
import uuid
from pathlib import Path

import chromadb
import numpy as np
from langchain_text_splitters import RecursiveCharacterTextSplitter


REPO_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_SOURCE_DIR = REPO_ROOT / "task_6" / "source_docs"
DEFAULT_CHROMA_PATH = REPO_ROOT / "databases" / "good" / "chroma_db"
DEFAULT_MANIFEST_PATH = REPO_ROOT / "task_6" / "state.json"
DEFAULT_LOG_PATH = REPO_ROOT / "task_6" / "logs" / "index_update.jsonl"

COLLECTION_NAME = "knowledge_base"

# Для локальной проверки без ключей.
DEFAULT_STUB_CHROMA_PATH = REPO_ROOT / "task_6" / "chroma_db_stub"
DEFAULT_STUB_COLLECTION_NAME = "knowledge_base_task6_stub"

# Совпадает с task_3/build_index.py
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 150

# В task_3 chunk_id имеют вид `{title}_{i}`.
# Чтобы чанки из task_6 не конфликтовали по id, добавляем свой префикс.
TASK6_CHUNK_PREFIX = "task6__"


def _iso_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel_to_doc_key(rel_path: Path) -> str:
    """
    Уникальный ключ документа для формирования chunk_id.
    Приводим путь без суффикса к виду без слэшей.
    """
    no_suffix = rel_path.with_suffix("")
    return no_suffix.as_posix().replace("/", "__").replace("\\", "__")


@dataclasses.dataclass(frozen=True)
class SourceFile:
    abs_path: Path
    rel_path: Path
    sha256: str
    mtime_ns: int
    doc_key: str
    title: str


class StubEmbedder:
    """Детерминированные эмбеддинги для отладки без доступа к Yandex API."""

    def __init__(self, dim: int = 256):
        if dim <= 0:
            raise ValueError("stub dim must be > 0")
        self.dim = dim

    def get_embedding(self, text: str, text_type: str = "doc") -> np.ndarray:
        # Включаем text_type в seed, чтобы doc/query не смешивались.
        seed_material = f"{text_type}::" + text
        base = hashlib.sha256(seed_material.encode("utf-8")).digest()

        # Разворачиваем sha в dim float32 (повторяя хеши с counter).
        out = np.empty(self.dim, dtype=np.float32)
        filled = 0
        counter = 0
        while filled < self.dim:
            digest = hashlib.sha256(base + counter.to_bytes(4, "little")).digest()
            for b in digest:
                if filled >= self.dim:
                    break
                out[filled] = (b / 255.0) * 2.0 - 1.0  # [-1, 1]
                filled += 1
            counter += 1

        # Нормализация для устойчивости cosine-подобия.
        norm = float(np.linalg.norm(out))
        if norm > 0:
            out = out / norm
        return out


class OnlineEmbedder:
    def __init__(self, max_retries: int = 3, retry_delay_sec: float = 2.0):
        self.max_retries = max_retries
        self.retry_delay_sec = retry_delay_sec

        # task_3/embedding_client.py ожидает импорты из своей директории.
        task_3_dir = REPO_ROOT / "task_3"
        sys.path.insert(0, str(task_3_dir))
        from embedding_client import get_embedding  # type: ignore

        self._get_embedding = get_embedding

    def get_embedding(self, text: str, text_type: str = "doc") -> np.ndarray:
        last_err: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return self._get_embedding(text, text_type=text_type)
            except Exception as e:  # noqa: BLE001 - логируем и ретраим
                last_err = e
                if attempt >= self.max_retries:
                    raise
                time.sleep(self.retry_delay_sec)
        if last_err is not None:
            raise last_err
        raise RuntimeError("OnlineEmbedder: unreachable state")


def _build_splitter(chunk_size: int, chunk_overlap: int) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )


def load_source_files(source_dir: Path) -> list[SourceFile]:
    if not source_dir.is_dir():
        raise FileNotFoundError(f"source_dir not found: {source_dir}")

    source_files: list[SourceFile] = []
    for abs_path in sorted(source_dir.glob("*.txt")):
        # Только .txt в корне source_dir, без рекурсии.
        rel_path = abs_path.relative_to(source_dir)
        doc_key = rel_to_doc_key(rel_path)
        title = abs_path.stem
        mtime_ns = abs_path.stat().st_mtime_ns
        sha = sha256_file(abs_path)
        source_files.append(
            SourceFile(
                abs_path=abs_path,
                rel_path=rel_path,
                sha256=sha,
                mtime_ns=mtime_ns,
                doc_key=doc_key,
                title=title,
            )
        )
    return source_files


def ensure_dirs() -> None:
    DEFAULT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def read_manifest(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_manifest(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def append_log(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def count_collection(collection: chromadb.api.models.Collection.Collection) -> int:
    # В разных версиях Chroma сигнатуры могут отличаться, поэтому пробуем несколько вариантов.
    if hasattr(collection, "count"):
        try:
            return int(collection.count())
        except Exception:
            pass
    res = collection.get(include=["ids"])
    ids = res.get("ids") or []
    return len(ids)


def get_embedder(mode: str, stub_dim: int) -> StubEmbedder | OnlineEmbedder:
    mode = mode.lower().strip()
    if mode not in {"auto", "online", "stub"}:
        raise ValueError("mode must be one of: auto|online|stub")

    if mode == "stub":
        return StubEmbedder(dim=stub_dim)

    if mode == "online":
        return OnlineEmbedder()

    # auto: если есть переменные окружения, пробуем online. Иначе stub.
    have_keys = bool(os.getenv("YANDEX_CLOUD_API_KEY")) and bool(os.getenv("YANDEX_CLOUD_FOLDER"))
    if have_keys:
        return OnlineEmbedder()
    return StubEmbedder(dim=stub_dim)


def main() -> int:
    parser = argparse.ArgumentParser(description="Инкрементальное обновление ChromaDB по папке с документами")
    parser.add_argument("--source-dir", type=str, default=str(DEFAULT_SOURCE_DIR))
    parser.add_argument("--chroma-path", type=str, default=str(DEFAULT_CHROMA_PATH))
    parser.add_argument("--collection-name", type=str, default=COLLECTION_NAME)
    parser.add_argument("--stub-chroma-path", type=str, default=str(DEFAULT_STUB_CHROMA_PATH))
    parser.add_argument("--stub-collection-name", type=str, default=DEFAULT_STUB_COLLECTION_NAME)
    parser.add_argument("--manifest", type=str, default=str(DEFAULT_MANIFEST_PATH))
    parser.add_argument("--log-path", type=str, default=str(DEFAULT_LOG_PATH))

    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--chunk-overlap", type=int, default=DEFAULT_CHUNK_OVERLAP)

    parser.add_argument("--mode", type=str, default="auto", choices=["auto", "online", "stub"])
    parser.add_argument("--stub-dim", type=int, default=256)

    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--retry-delay-sec", type=float, default=2.0)

    # Полный пересчёт именно source_docs (не трогает внешнюю good-базу полностью).
    parser.add_argument("--rebuild", action="store_true", help="Пересчитать source_docs заново (только для чанков этого задания)")
    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    chroma_path = Path(args.chroma_path)
    effective_collection_name = args.collection_name
    manifest_path = Path(args.manifest)
    log_path = Path(args.log_path)

    ensure_dirs()

    run_id = str(uuid.uuid4())
    start_ts = _iso_now()
    started_at = time.perf_counter()

    record: dict = {
        "run_id": run_id,
        "start_time": start_ts,
        "source_dir": str(source_dir),
        "chroma_path": str(chroma_path),
        "collection_name": effective_collection_name,
        "mode": args.mode,
        "chunk_size": args.chunk_size,
        "chunk_overlap": args.chunk_overlap,
        "files_seen": 0,
        "files_added_or_updated": 0,
        "files_unchanged": 0,
        "chunks_added": 0,
        "chunks_deleted": 0,
        "index_size_before": None,
        "index_size_after": None,
        "errors": [],
    }

    # Manifest: храним состояние для инкрементального удаления старых чанков.
    manifest = read_manifest(manifest_path)
    files_state: dict = manifest.get("files", {})

    # Embeddings mode.
    embedder = get_embedder(args.mode, args.stub_dim)
    if isinstance(embedder, OnlineEmbedder):
        # Подстроим ретраи под CLI.
        embedder.max_retries = int(args.max_retries)
        embedder.retry_delay_sec = float(args.retry_delay_sec)
    if isinstance(embedder, StubEmbedder):
        # Чтобы не портить существующий task_3 индекс при локальной проверке.
        chroma_path = Path(args.stub_chroma_path)
        effective_collection_name = args.stub_collection_name
        record["chroma_path"] = str(chroma_path)
        record["collection_name"] = effective_collection_name

    # Indices / Chroma.
    chroma_path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(chroma_path))
    splitter = _build_splitter(args.chunk_size, args.chunk_overlap)

    # Создаём коллекцию (если ещё нет).
    collection_metadata = {"description": "Incremental KB for task_6"}
    try:
        collection = client.get_collection(name=effective_collection_name)
    except Exception:
        collection = client.create_collection(
            name=effective_collection_name,
            metadata=collection_metadata,
            configuration={"hnsw": {"space": "cosine"}},
        )

    try:
        record["index_size_before"] = count_collection(collection)
    except Exception:
        record["index_size_before"] = None

    source_files = load_source_files(source_dir)
    record["files_seen"] = len(source_files)

    files_added_or_updated = 0
    files_unchanged = 0
    chunks_added = 0
    chunks_deleted = 0

    current_rel_keys = {str(sf.rel_path) for sf in source_files}

    # Если включен rebuild — пересобираем индексацию целиком для source_docs,
    # удаляя ранее проиндексированные чанки из manifest (но не трогая остальной task_3 индекс).
    if args.rebuild:
        for rel_key, prev in list(files_state.items()):
            if not prev or "chunk_count" not in prev or "chunk_prefix" not in prev:
                continue
            old_chunk_count = int(prev["chunk_count"])
            old_chunk_prefix = str(prev["chunk_prefix"])
            old_ids = [f"{old_chunk_prefix}_{i}" for i in range(old_chunk_count)]
            try:
                collection.delete(ids=old_ids)
                chunks_deleted += len(old_ids)
            except Exception as e:  # noqa: BLE001
                record["errors"].append(
                    {
                        "type": "delete_failed_rebuild",
                        "file": rel_key,
                        "error": repr(e),
                    }
                )
        files_state = {}
    else:
        # Удаляем чанки документов, которые пропали из source_dir.
        missing_keys = set(files_state.keys()) - current_rel_keys
        for rel_key in missing_keys:
            prev = files_state.get(rel_key) or {}
            if "chunk_count" not in prev or "chunk_prefix" not in prev:
                continue
            old_chunk_count = int(prev["chunk_count"])
            old_chunk_prefix = str(prev["chunk_prefix"])
            old_ids = [f"{old_chunk_prefix}_{i}" for i in range(old_chunk_count)]
            try:
                collection.delete(ids=old_ids)
                chunks_deleted += len(old_ids)
            except Exception as e:  # noqa: BLE001
                record["errors"].append(
                    {
                        "type": "delete_failed_missing_file",
                        "file": rel_key,
                        "error": repr(e),
                    }
                )
            files_state.pop(rel_key, None)

    # Обновляем/переиндексируем только изменённые файлы.
    for sf in source_files:
        rel_key = str(sf.rel_path)
        prev = files_state.get(rel_key)

        if prev and prev.get("sha256") == sf.sha256:
            files_unchanged += 1
            continue

        # Если документ поменялся — удаляем его старые чанки по сохранённому chunk_count.
        if prev and "chunk_count" in prev:
            old_chunk_count = int(prev["chunk_count"])
            old_chunk_prefix = str(prev["chunk_prefix"])
            old_ids = [f"{old_chunk_prefix}_{i}" for i in range(old_chunk_count)]
            try:
                collection.delete(ids=old_ids)
                chunks_deleted += len(old_ids)
            except Exception as e:  # noqa: BLE001
                # Не останавливаемся: добавление новых чанков с теми же ids всё равно упадёт,
                # но в лог попадёт причина.
                record["errors"].append(
                    {
                        "type": "delete_failed",
                        "file": rel_key,
                        "error": repr(e),
                    }
                )

        # Чанкинг.
        text = sf.abs_path.read_text(encoding="utf-8", errors="ignore")
        chunk_texts = splitter.split_text(text)
        chunk_prefix = f"{TASK6_CHUNK_PREFIX}{sf.doc_key}"
        chunk_ids = [f"{chunk_prefix}_{i}" for i in range(len(chunk_texts))]

        # Эмбеддинги и добавление в индекс.
        # Chroma (и Yandex embedding) в данном курсе используются по одному тексту,
        # поэтому оставляем последовательный режим, чтобы поведение было предсказуемым.
        embeddings: list[list[float]] = []
        for i, chunk in enumerate(chunk_texts):
            emb = embedder.get_embedding(chunk, text_type="doc")
            embeddings.append(emb.astype(np.float32).tolist())

            if (i + 1) % 50 == 0:
                # Без print в лог-файле, но чтобы пользователю было видно прогресс.
                print(f"[{rel_key}] embeddings: {i + 1}/{len(chunk_texts)}")

        metadatas = [
            {"source": rel_key, "title": sf.title, "chunk_prefix": chunk_prefix}
            for _ in chunk_texts
        ]

        collection.add(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=chunk_texts,
            metadatas=metadatas,
        )

        files_added_or_updated += 1
        chunks_added += len(chunk_texts)

        # Обновляем состояние в manifest.
        files_state[rel_key] = {
            "sha256": sf.sha256,
            "mtime_ns": sf.mtime_ns,
            "chunk_prefix": chunk_prefix,
            "chunk_count": len(chunk_texts),
            "updated_at": _iso_now(),
        }

    # Итог.
    try:
        record["index_size_after"] = count_collection(collection)
    except Exception:
        record["index_size_after"] = None

    record.update(
        {
            "files_added_or_updated": files_added_or_updated,
            "files_unchanged": files_unchanged,
            "chunks_added": chunks_added,
            "chunks_deleted": chunks_deleted,
            "end_time": _iso_now(),
            "elapsed_sec": round(time.perf_counter() - started_at, 3),
        }
    )

    manifest_out = {
        "updated_at": _iso_now(),
        "chunking": {"chunk_size": args.chunk_size, "chunk_overlap": args.chunk_overlap},
        "files": files_state,
        "last_run": {"run_id": run_id, "start_time": start_ts, "end_time": record.get("end_time")},
    }

    write_manifest(manifest_path, manifest_out)
    append_log(log_path, record)

    # Печать для stdout (удобно для cron).
    ok = len(record["errors"]) == 0
    print(
        json.dumps(
            {
                "run_id": run_id,
                "ok": ok,
                "files_seen": record["files_seen"],
                "files_added_or_updated": record["files_added_or_updated"],
                "chunks_added": record["chunks_added"],
                "chunks_deleted": record["chunks_deleted"],
                "index_size_after": record["index_size_after"],
                "errors": len(record["errors"]),
                "elapsed_sec": record["elapsed_sec"],
            },
            ensure_ascii=False,
        )
    )

    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())

