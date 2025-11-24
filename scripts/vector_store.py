"""Lightweight vector database for managing chunk embeddings and token stats.

The goal is to provide a plug-in backend that can be swapped with a real
LLM embedding API later. For now we default to a deterministic hash-based
embedding so tests stay offline-friendly.
"""
from __future__ import annotations

import math
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Sequence

from scripts.repository import StoryRepository
from scripts.init_db import init_db

EmbeddingFn = Callable[[str, int], Sequence[float]]


@dataclass
class VectorMatch:
    chunk_id: int
    chapter_title: str
    text: str
    score: float
    model: str


class VectorStore:
    """Store and search chunk embeddings inside SQLite.

    The store is intentionally simple: embeddings are serialized as comma
    separated floats so they can be inspected and migrated easily. Consumers
    can inject their own embedding function (e.g., an API call to an LLM
    provider) by passing ``embedder``.
    """

    def __init__(self, db_path: str = "data/novel.db"):
        self.db_path = Path(db_path)
        self.repo = StoryRepository(db_path)

    # --- Embedding helpers -------------------------------------------------
    @staticmethod
    def _tokenize(text: str) -> List[str]:
        # Greedy match Chinese sequences or alphanumerics to keep tokens stable
        return re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z0-9]+", text)

    @classmethod
    def hash_embedding(cls, text: str, dim: int = 128) -> List[float]:
        """Generate a deterministic sparse vector based on token hashes."""
        tokens = cls._tokenize(text)
        vec = [0.0] * dim
        for token in tokens:
            bucket = hash(token) % dim
            vec[bucket] += 1.0
        return cls._normalize(vec)

    @staticmethod
    def _normalize(vec: Sequence[float]) -> List[float]:
        denom = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / denom for v in vec]

    @staticmethod
    def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
        return sum(x * y for x, y in zip(a, b))

    # --- Persistence -------------------------------------------------------
    def bootstrap(self) -> None:
        init_db(str(self.db_path))

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _store_vector(
        self,
        chunk_id: int,
        vector: Sequence[float],
        model: str,
        token_count: int,
        dim: int,
    ) -> None:
        serialized = ",".join(f"{v:.6f}" for v in vector)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO embeddings(chunk_id, model, dim, vector, token_count, created_at)
                VALUES(?, ?, ?, ?, ?, ?)
                ON CONFLICT(chunk_id, model)
                DO UPDATE SET vector=excluded.vector, dim=excluded.dim, token_count=excluded.token_count, created_at=excluded.created_at
                """,
                (chunk_id, model, dim, serialized, token_count, datetime.now().isoformat(timespec="seconds")),
            )

    @staticmethod
    def _deserialize(vector_text: str) -> List[float]:
        return [float(x) for x in vector_text.split(",") if x]

    # --- Public API --------------------------------------------------------
    def index_document(
        self,
        document_title: str,
        model: str = "hash",
        dim: int = 128,
        embedder: EmbeddingFn | None = None,
    ) -> int:
        """Create or refresh embeddings for every chunk in a document.

        Returns the number of chunks processed.
        """
        self.bootstrap()
        fn = embedder or self.hash_embedding
        chunks = list(self.repo.iter_chunks(document_title))
        for chunk_id, chapter_title, text in chunks:
            vector = fn(text, dim)
            token_count = len(self._tokenize(text))
            self._store_vector(chunk_id, vector, model, token_count, dim)
        return len(chunks)

    def similarity_search(
        self,
        query: str,
        top_k: int = 5,
        model: str = "hash",
        dim: int = 128,
        embedder: EmbeddingFn | None = None,
    ) -> List[VectorMatch]:
        """Return the most similar chunks for a query."""
        self.bootstrap()
        fn = embedder or self.hash_embedding
        query_vec = fn(query, dim)

        with self._connect() as conn:
            rows = conn.execute(
                "SELECT e.chunk_id, e.vector, c.text, ch.title as chapter_title FROM embeddings e "
                "JOIN chunks c ON e.chunk_id=c.id "
                "JOIN chapters ch ON c.chapter_id=ch.id "
                "JOIN documents d ON ch.document_id=d.id "
                "WHERE e.model=? ORDER BY e.id",
                (model,),
            ).fetchall()

        matches: List[VectorMatch] = []
        for row in rows:
            vec = self._deserialize(row["vector"])
            score = self._cosine(query_vec, vec)
            matches.append(
                VectorMatch(
                    chunk_id=row["chunk_id"],
                    chapter_title=row["chapter_title"],
                    text=row["text"],
                    score=score,
                    model=model,
                )
            )
        matches.sort(key=lambda m: m.score, reverse=True)
        return matches[:top_k]

    def dump_for_api(self, query: str, top_k: int = 3) -> dict:
        """Helper to craft a ready-to-send payload for downstream LLM APIs."""
        hits = self.similarity_search(query, top_k=top_k)
        return {
            "query": query,
            "model": hits[0].model if hits else "hash",
            "context": [
                {"chapter": m.chapter_title, "score": round(m.score, 3), "text": m.text}
                for m in hits
            ],
        }


if __name__ == "__main__":
    store = VectorStore()
    count = store.index_document("示例文档")
    print(f"✅ 已更新向量索引，共 {count} 条分块。")
