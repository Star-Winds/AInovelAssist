from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable, Tuple

from scripts.ingest import clean_text, split_into_chunks
from scripts.init_db import init_db


class StoryRepository:
    """Small helper around the SQLite schema for storing chapters and chunks."""

    def __init__(self, db_path: str = "data/novel.db"):
        self.db_path = Path(db_path)

    def bootstrap(self) -> None:
        init_db(str(self.db_path))

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _document_id(self, document_title: str) -> int | None:
        with self._connect() as conn:
            cur = conn.execute("SELECT id FROM documents WHERE title=?", (document_title,))
            row = cur.fetchone()
            return row["id"] if row else None

    def upsert_document(self, title: str, source: str | None = None) -> int:
        self.bootstrap()
        with self._connect() as conn:
            cur = conn.execute("SELECT id FROM documents WHERE title=?", (title,))
            row = cur.fetchone()
            if row:
                return row["id"]
            cur = conn.execute(
                "INSERT INTO documents(title, source, created_at) VALUES (?, ?, ?)",
                (title, source, datetime.now().isoformat(timespec="seconds")),
            )
            return cur.lastrowid

    def _next_chapter_index(self, conn, document_id: int) -> int:
        cur = conn.execute(
            'SELECT COALESCE(MAX("index"), 0) FROM chapters WHERE document_id=?',
            (document_id,),
        )
        return cur.fetchone()[0] + 1

    def add_chapter(
        self,
        document_title: str,
        chapter_title: str,
        raw_text: str,
        chunk_size: int = 1200,
        path: str | None = None,
    ) -> Tuple[int, int, int]:
        """Store a chapter and its chunks. Returns (document_id, chapter_id, chunks)."""
        cleaned = clean_text(raw_text)
        pieces = split_into_chunks(cleaned, chunk_size)

        doc_id = self.upsert_document(document_title)
        with self._connect() as conn:
            chapter_index = self._next_chapter_index(conn, doc_id)
            cur = conn.execute(
                'INSERT INTO chapters(document_id, "index", title, path) VALUES (?, ?, ?, ?)',
                (doc_id, chapter_index, chapter_title, path),
            )
            chapter_id = cur.lastrowid
            for idx, piece in enumerate(pieces, start=1):
                conn.execute(
                    'INSERT INTO chunks(chapter_id, "index", text, char_len) VALUES (?, ?, ?, ?)',
                    (chapter_id, idx, piece, len(piece)),
                )
        return doc_id, chapter_id, len(pieces)

    def iter_chapters(self, document_title: str) -> Iterable[Tuple[str, str]]:
        """Yield chapter title and concatenated text for a document (ordered)."""
        self.bootstrap()
        with self._connect() as conn:
            doc_id = self._document_id(document_title)
            if not doc_id:
                return []
            chapters = conn.execute(
                'SELECT id, "index", title FROM chapters WHERE document_id=? ORDER BY "index"',
                (doc_id,),
            ).fetchall()
            for chap in chapters:
                chunks = conn.execute(
                    'SELECT text FROM chunks WHERE chapter_id=? ORDER BY "index"',
                    (chap["id"],),
                ).fetchall()
                yield chap["title"], "\n".join(c["text"] for c in chunks)

    def iter_chunks(self, document_title: str) -> Iterable[Tuple[int, str, str]]:
        """Yield chunk_id, chapter_title, text for a document in order."""
        self.bootstrap()
        with self._connect() as conn:
            doc_id = self._document_id(document_title)
            if not doc_id:
                return []
            rows = conn.execute(
                'SELECT c.id as chunk_id, ch.title as chapter_title, c.text as text '\
                'FROM chapters ch JOIN chunks c ON ch.id=c.chapter_id '\
                'WHERE ch.document_id=? ORDER BY ch."index", c."index"',
                (doc_id,),
            ).fetchall()
            for row in rows:
                yield row["chunk_id"], row["chapter_title"], row["text"]

    def flatten_document(self, document_title: str) -> str:
        parts = [text for _, text in self.iter_chapters(document_title)]
        return "\n".join(parts)
