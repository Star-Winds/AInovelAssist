# scripts/ingest.py
# -*- coding: utf-8 -*-
import sys, argparse, sqlite3
from datetime import datetime
from pathlib import Path
from charset_normalizer import from_path
from docx import Document

def detect_and_read(path: Path):
    if path.suffix.lower() == ".docx":
        doc = Document(path); text = "\n".join(p.text for p in doc.paragraphs)
        return text, "docx", path.stat().st_size
    result = from_path(path); best = result.best()
    enc = (best.encoding or "utf-8").strip()
    if enc.lower().startswith("utf-8"): enc = "utf-8-sig"
    try:
        with open(path, "r", encoding=enc, errors="replace") as f: text = f.read()
    except Exception:
        with open(path, "r", encoding="utf-8", errors="replace") as f: text = f.read()
        enc = "utf-8(fallback)"
    return text, enc, path.stat().st_size

def clean_text(text: str) -> str:
    text = text.replace("\r\n","\n").replace("\r","\n")
    lines = [line.rstrip() for line in text.split("\n")]
    cleaned, empty = [], 0
    for line in lines:
        if line.strip()=="":
            empty += 1
            if empty<=1: cleaned.append("")
        else:
            empty = 0; cleaned.append(line)
    return "\n".join(cleaned).strip()

def split_into_chunks(text: str, chunk_size: int = 1200):
    if len(text) <= chunk_size: return [text]
    chunks, start = [], 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        window_start = max(start + int(chunk_size*0.7), start)
        cut = end
        for i in range(end, window_start, -1):
            if text[i-1] in "。！？；，、）】」』…—\n":
                cut = i; break
        chunks.append(text[start:cut].strip()); start = cut
    return [c for c in chunks if c]

def insert_into_db(db_path, doc_title, chapter_title, cleaned_text, chunk_size):
    conn = sqlite3.connect(db_path); conn.execute("PRAGMA foreign_keys = ON;")
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO documents(title, created_at) VALUES (?, ?)",
                (doc_title, datetime.now().isoformat(timespec="seconds"))
            ); document_id = cur.lastrowid
            cur = conn.execute(
                'INSERT INTO chapters(document_id, "index", title, path) VALUES (?, ?, ?, ?)',
                (document_id, 1, chapter_title, None)
            ); chapter_id = cur.lastrowid
            pieces = split_into_chunks(cleaned_text, chunk_size)
            for idx, piece in enumerate(pieces, start=1):
                conn.execute(
                    'INSERT INTO chunks(chapter_id, "index", text, char_len) VALUES (?, ?, ?, ?)',
                    (chapter_id, idx, piece, len(piece))
                )
        return document_id, chapter_id, len(pieces)
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="导入并清洗章节文本")
    parser.add_argument("filepath", help="要读取的章节文件路径")
    parser.add_argument("--print", action="store_true", help="打印清洗后的结果")
    parser.add_argument("--debug", action="store_true", help="打印调试信息")
    # 入库相关参数（关键）
    parser.add_argument("--to-db", action="store_true", help="将清洗后的文本导入 SQLite 数据库")
    parser.add_argument("--db-path", default="data/novel.db", help="数据库路径 (默认 data/novel.db)")
    parser.add_argument("--doc-title", default=None, help="文档标题（默认用文件名）")
    parser.add_argument("--chapter", default="第1章", help="章节标题（默认：第1章）")
    parser.add_argument("--chunk-size", type=int, default=1200, help="分块大小（字符数，默认1200）")
    args = parser.parse_args()

    path = Path(args.filepath)
    if not path.exists():
        print(f"❌ 文件不存在: {path}"); sys.exit(1)

    raw_text, enc, fsize = detect_and_read(path)
    cleaned = clean_text(raw_text)

    if args.debug:
        print("=== DEBUG ==="); print(f"文件: {path}")
        print(f"探测编码: {enc}"); print(f"文件大小(字节): {fsize}")
        print(f"清洗后长度: {len(cleaned)}"); print("=============\n")

    if args.print:
        print("=== 清洗后文本预览 ===\n"); print(cleaned[:2000])
        if len(cleaned) > 2000: print("\n=== (已截断预览) ===")

    if args.to_db:
        title = args.doc_title or path.stem
        doc_id, chap_id, n = insert_into_db(args.db_path, title, args.chapter, cleaned, args.chunk_size)
        print(f"🗂 已入库 → document_id={doc_id}, chapter_id={chap_id}, chunks={n}, db={args.db_path}")

if __name__ == "__main__":
    main()
