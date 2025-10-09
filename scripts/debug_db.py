# -*- coding: utf-8 -*-
import sqlite3, sys, os, textwrap

DB = sys.argv[1] if len(sys.argv) > 1 else "data/novel.db"

def show_rows(cur, sql, args=()):
    cur.execute(sql, args)
    rows = cur.fetchall()
    for r in rows:
        print("  -", r)

if not os.path.exists(DB):
    print(f"[FAIL] DB not found: {DB}")
    sys.exit(1)

print(f"[OK] Using DB: {DB} (size={os.path.getsize(DB)} bytes)")
conn = sqlite3.connect(DB)
cur = conn.cursor()

# 基本计数
for tbl in ["documents", "chapters", "chunks", "chunks_fts"]:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {tbl};")
        n = cur.fetchone()[0]
        print(f"[COUNT] {tbl}: {n}")
    except Exception as e:
        print(f"[WARN] table {tbl} not found or error: {e}")

# 抽样看看 chunks 内容
print("\n[SAMPLE] chunks (id, text[0:50])")
try:
    cur.execute("SELECT id, substr(text,1,50) FROM chunks LIMIT 5;")
    for cid, t in cur.fetchall():
        print(f"  #{cid}: {t}")
except Exception as e:
    print("  (error reading chunks):", e)

# 抽样看看 FTS 索引的内容（注意：这里看的是分词后的 text）
print("\n[SAMPLE] chunks_fts (rowid, text[0:50])")
try:
    cur.execute("SELECT rowid, substr(text,1,50) FROM chunks_fts LIMIT 5;")
    for rid, t in cur.fetchall():
        print(f"  rowid={rid}: {t}")
except Exception as e:
    print("  (error reading chunks_fts):", e)

# 用 LIKE 做一次直观验证（不走 FTS），看看库里有没有“文本”
print("\n[LIKE TEST] chunks.text LIKE %文本% :")
try:
    cur.execute("SELECT COUNT(*) FROM chunks WHERE text LIKE '%'||?||'%';", ("文本",))
    cnt = cur.fetchone()[0]
    print("  matches:", cnt)
    if cnt:
        cur.execute("SELECT id, substr(text,1,50) FROM chunks WHERE text LIKE '%'||?||'%' LIMIT 3;", ("文本",))
        for r in cur.fetchall():
            print(" ", r)
except Exception as e:
    print("  (error LIKE test):", e)

conn.close()
