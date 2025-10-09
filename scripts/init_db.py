import sqlite3
from pathlib import Path

def init_db():
    # 确保 data 文件夹存在
    Path("data").mkdir(exist_ok=True)

    conn = sqlite3.connect("data/novel.db")
    cur = conn.cursor()

    # 开启外键
    cur.execute("PRAGMA foreign_keys = ON;")

    # documents
    cur.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        source TEXT,
        created_at TEXT
    );
    """)

    # chapters（注意 "index" 用引号）
    cur.execute("""
    CREATE TABLE IF NOT EXISTS chapters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        "index" INTEGER,
        title TEXT,
        path TEXT,
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
    );
    """)

    # chunks
    cur.execute("""
    CREATE TABLE IF NOT EXISTS chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chapter_id INTEGER NOT NULL,
        "index" INTEGER,
        text TEXT,
        char_len INTEGER,
        FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("✅ 数据库初始化完成！data/novel.db 已就绪。")
