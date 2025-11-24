"""Lightweight vector database built on top of the existing SQLite chunks.

The module keeps dependencies minimal by using pure Python TF-IDF over
character n-grams (2–4) so it works reasonably well for Chinese without
extra tokenizers. Index data is persisted with pickle for quick reloads.
"""
from __future__ import annotations

import argparse
import math
import pickle
import sqlite3
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


@dataclass
class SearchResult:
    chunk_id: int
    score: float
    document_title: str | None
    chapter_title: str | None
    preview: str


def _char_ngrams(text: str, min_n: int = 2, max_n: int = 4) -> List[str]:
    """Generate character n-grams; fallback to unigrams for very short text."""
    normalized = text.replace("\n", " ").strip()
    if not normalized:
        return []
    tokens: List[str] = []
    length = len(normalized)
    for i in range(length):
        if normalized[i].isspace():
            continue
        for n in range(min_n, max_n + 1):
            end = i + n
            if end <= length:
                span = normalized[i:end]
                if span.strip():
                    tokens.append(span)
    if not tokens:
        tokens = [ch for ch in normalized if not ch.isspace()]
    return tokens


def _tfidf_vector(tokens: Iterable[str], vocab: Dict[str, int], idf: List[float]) -> Tuple[Dict[int, float], float]:
    counts = Counter(tokens)
    total = sum(counts.values()) or 1
    vec: Dict[int, float] = {}
    norm = 0.0
    for token, tf in counts.items():
        idx = vocab.get(token)
        if idx is None:
            continue
        weight = (tf / total) * idf[idx]
        vec[idx] = weight
        norm += weight * weight
    norm = math.sqrt(norm) if norm else 0.0
    return vec, norm


class VectorStore:
    """Persist embeddings for chunks and enable similarity search."""

    def __init__(self, db_path: str = "data/novel.db", index_path: str = "data/vector_store.joblib"):
        self.db_path = Path(db_path)
        self.index_path = Path(index_path)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.vocab: Dict[str, int] = {}
        self.idf: List[float] = []
        self.embeddings: List[Tuple[Dict[int, float], float]] = []
        self.metadata: List[dict] = []

    # ---------------- internal helpers ----------------
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _load_index(self) -> None:
        if not self.index_path.exists():
            raise FileNotFoundError(f"向量索引不存在：{self.index_path}. 请先执行 --rebuild。")
        with self.index_path.open("rb") as f:
            payload = pickle.load(f)
        self.vocab = payload["vocab"]
        self.idf = payload["idf"]
        self.embeddings = payload["embeddings"]
        self.metadata = payload["metadata"]

    # ---------------- public API ----------------
    def rebuild(self) -> None:
        """Recompute vectors from all chunks and persist them."""
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT c.id AS chunk_id, c.text, ch.title AS chapter_title, d.title AS document_title
                FROM chunks c
                LEFT JOIN chapters ch ON ch.id = c.chapter_id
                LEFT JOIN documents d ON d.id = ch.document_id
                WHERE c.text IS NOT NULL AND length(c.text) > 0
                ORDER BY c.id;
                """
            ).fetchall()

        if not rows:
            raise RuntimeError("数据库中没有可索引的分块，请先使用 ingest/assistant 导入文本。")

        texts = [row["text"] for row in rows]
        tokenized = [_char_ngrams(txt) for txt in texts]

        # document frequency / vocabulary
        df_counts: Counter[str] = Counter()
        for tokens in tokenized:
            df_counts.update(set(tokens))
        vocab = {token: idx for idx, token in enumerate(sorted(df_counts))}
        idf = []
        doc_total = len(tokenized)
        for token in sorted(df_counts):
            df = df_counts[token]
            idf.append(math.log((1 + doc_total) / (1 + df)) + 1)

        embeddings: List[Tuple[Dict[int, float], float]] = []
        for tokens in tokenized:
            vec, norm = _tfidf_vector(tokens, vocab, idf)
            embeddings.append((vec, norm))

        metadata = []
        for row, txt in zip(rows, texts):
            preview = txt.replace("\n", " ").strip()
            preview = preview[:120] + ("…" if len(preview) > 120 else "")
            metadata.append(
                {
                    "chunk_id": row["chunk_id"],
                    "document_title": row["document_title"],
                    "chapter_title": row["chapter_title"],
                    "preview": preview,
                }
            )

        with self.index_path.open("wb") as f:
            pickle.dump(
                {"vocab": vocab, "idf": idf, "embeddings": embeddings, "metadata": metadata},
                f,
            )

        self.vocab = vocab
        self.idf = idf
        self.embeddings = embeddings
        self.metadata = metadata

    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        if not query.strip():
            raise ValueError("查询不能为空。")
        if not self.vocab or not self.embeddings:
            self._load_index()

        tokens = _char_ngrams(query)
        q_vec, q_norm = _tfidf_vector(tokens, self.vocab, self.idf)
        if q_norm == 0:
            return []

        scores: List[float] = []
        for vec, norm in self.embeddings:
            if norm == 0:
                scores.append(0.0)
                continue
            dot = sum(weight * vec.get(idx, 0.0) for idx, weight in q_vec.items())
            scores.append(dot / (q_norm * norm))

        top_k = max(1, min(top_k, len(scores)))
        best_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results: List[SearchResult] = []
        for idx in best_idx:
            meta = self.metadata[idx]
            results.append(
                SearchResult(
                    chunk_id=meta["chunk_id"],
                    score=float(scores[idx]),
                    document_title=meta.get("document_title"),
                    chapter_title=meta.get("chapter_title"),
                    preview=meta.get("preview", ""),
                )
            )
        return results

    def as_lines(self, results: Sequence[SearchResult]) -> List[str]:
        lines: List[str] = []
        for item in results:
            lines.append(
                f"[score={item.score:.3f}] {item.document_title or '-'} / {item.chapter_title or '-'}"
                f" (chunk#{item.chunk_id}) -> {item.preview}"
            )
        return lines


def main() -> None:
    ap = argparse.ArgumentParser(description="基于 TF-IDF 的轻量向量数据库")
    ap.add_argument("query", nargs="?", help="要搜索的文本。留空只重建索引。")
    ap.add_argument("--db", default="data/novel.db", help="SQLite 数据库路径")
    ap.add_argument("--index", default="data/vector_store.joblib", help="向量索引持久化路径")
    ap.add_argument("--topk", type=int, default=5, help="返回的相似段落数量")
    ap.add_argument("--rebuild", action="store_true", help="从 chunks 重建向量索引")
    args = ap.parse_args()

    store = VectorStore(db_path=args.db, index_path=args.index)

    if args.rebuild:
        print("🔧 正在重建向量索引…")
        store.rebuild()
        print(f"✅ 已保存到 {args.index}")

    if args.query:
        results = store.search(args.query, top_k=args.topk)
        for line in store.as_lines(results):
            print(line)
    elif not args.rebuild:
        ap.print_help()


if __name__ == "__main__":
    main()
