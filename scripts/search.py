# -*- coding: utf-8 -*-
"""
FTS5 search over chunks with CJK-friendly 1+2 gram indexing.
Fix: join via fts rowid (content-less tables have NULL column values).
"""

import argparse
import sqlite3
import re
from typing import List, Tuple, Optional

# ---------------- CJK helpers ----------------
CJK_RANGE = (
    r"\u3400-\u4DBF"   # CJK Ext A
    r"\u4E00-\u9FFF"   # CJK Unified
    r"\uF900-\uFAFF"   # CJK Compatibility Ideographs
    r"\U00020000-\U0002A6DF"  # Ext B
    r"\U0002A700-\U0002B73F"  # Ext C
    r"\U0002B740-\U0002B81F"  # Ext D
    r"\U0002B820-\U0002CEAF"  # Ext E
    r"\U0002CEB0-\U0002EBEF"  # Ext F
)
CJK_RE = re.compile(f"[{CJK_RANGE}]")

def has_cjk(s: str) -> bool:
    return bool(CJK_RE.search(s))

def grams_1_2(s: str) -> List[str]:
    cleaned = []
    for ch in s:
        if CJK_RE.match(ch) or ch.isalnum():
            cleaned.append(ch)
        else:
            cleaned.append(" ")
    s2 = "".join(cleaned)

    grams: List[str] = []
    i = 0
    n = len(s2)
    while i < n:
        ch = s2[i]
        if CJK_RE.match(ch):
            j = i
            while j < n and CJK_RE.match(s2[j]):
                j += 1
            seg = s2[i:j]
            grams.extend(list(seg))                # unigrams
            grams.extend(seg[k:k+2] for k in range(len(seg) - 1))  # bigrams
            i = j
        else:
            start = i
            while i < n and not CJK_RE.match(s2[i]):
                i += 1
            seg = s2[start:i].strip()
            if seg:
                grams.append(seg)
    return grams

def to_index_text(s: Optional[str]) -> str:
    if not s:
        return ""
    return " ".join(grams_1_2(s)) if has_cjk(s) else s

def to_query_text(q: str) -> str:
    q = q.strip().strip('"').strip("'")
    return " ".join(grams_1_2(q)) if has_cjk(q) else q

# ---------------- FTS core ----------------
def check_fts5_enabled(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    try:
        cur.execute("CREATE VIRTUAL TABLE IF NOT EXISTS temp.fts5_probe USING fts5(x);")
        cur.execute("DROP TABLE temp.fts5_probe;")
    except sqlite3.OperationalError as e:
        raise RuntimeError("Your SQLite build lacks FTS5.") from e

def ensure_fts(conn: sqlite3.Connection) -> None:
    """
    Build/refresh a content-less FTS5 index from chunks, storing 1+2-gram text.
    IMPORTANT: join with chunks via fts rowid == chunks.id
    """
    check_fts5_enabled(conn)
    cur = conn.cursor()
    # Recreate (simplify: only one indexed column 'text')
    cur.execute("DROP TABLE IF EXISTS chunks_fts;")
    cur.execute("""
        CREATE VIRTUAL TABLE chunks_fts
        USING fts5(
            text,
            content=''   -- content-less: values are not stored, only the index
        );
    """)

    # Fill from base table; set rowid to chunks.id for stable join
    cur.execute("SELECT id, text FROM chunks WHERE text IS NOT NULL AND length(text) > 0;")
    rows = cur.fetchall()
    payload = []
    for cid, txt in rows:
        idx_text = to_index_text(txt or "")
        if idx_text:
            payload.append((cid, idx_text))
    if payload:
        cur.executemany(
            "INSERT INTO chunks_fts(rowid, text) VALUES(?, ?);",
            payload
        )
    conn.commit()

def search(conn: sqlite3.Connection, query: str, limit: int = 20
) -> List[Tuple[int, str, Optional[str], Optional[str]]]:
    cur = conn.cursor()
    cur.execute("""
        SELECT c.id, c.text, ch.title AS chapter, d.title AS doc
        FROM chunks_fts f
        JOIN chunks c ON c.id = f.rowid         -- <<<<<< key fix here
        LEFT JOIN chapters ch ON ch.id = c.chapter_id
        LEFT JOIN documents d ON d.id = ch.document_id
        WHERE chunks_fts MATCH ?
        LIMIT ?;
    """, (query, limit))
    return cur.fetchall()

def format_row(cid: int, text: Optional[str], chapter: Optional[str],
               doc: Optional[str], width: int = 120) -> str:
    preview = (text or "").replace("\r", " ").replace("\n", " ")
    if len(preview) > width:
        preview = preview[: width - 1] + "…"
    return f"[{doc or '-'} / {chapter or '-'}] chunk#{cid}: {preview}"

def main() -> None:
    ap = argparse.ArgumentParser(description="FTS5 search with CJK 1+2 gram; join via rowid.")
    ap.add_argument("query", help="CJK supported; plain text is OK.")
    ap.add_argument("--db", default="data/novel.db")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--reindex", action="store_true", help="Rebuild index before search")
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)

    if args.reindex:
        print("Rebuilding FTS5 index (CJK 1+2-gram)…")
        ensure_fts(conn)
        print("Reindex done.\n")

    q = to_query_text(args.query or "")
    if not q:
        raise SystemExit("Empty query.")
    print("[DEBUG] query ->", q)

    # Quick sanity count directly on FTS table
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM chunks_fts WHERE chunks_fts MATCH ?;", (q,))
    print(f"[DEBUG] raw MATCH count in FTS index: {cur.fetchone()[0]}")

    rows = search(conn, q, args.limit)
    if not rows:
        print("No results.")
        return

    for cid, txt, chap, doc in rows:
        print(format_row(cid, txt, chap, doc))

if __name__ == "__main__":
    main()
