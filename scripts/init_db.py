import sqlite3
from pathlib import Path


def init_db(db_path: str = "data/novel.db"):
    """Initialize SQLite database with required tables.

    The function is idempotent and can be pointed at a custom database path
    (useful in tests). It also ensures parent folders exist.
    """
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Enable foreign keys for SQLite
    cur.execute("PRAGMA foreign_keys = ON;")

    # documents
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        source TEXT,
        created_at TEXT
    );
    """
    )

    # chapters ("index" kept quoted to avoid keyword conflicts)
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS chapters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        "index" INTEGER,
        title TEXT,
        path TEXT,
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
    );
    """
    )

    # chunks
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chapter_id INTEGER NOT NULL,
        "index" INTEGER,
        text TEXT,
        char_len INTEGER,
        FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
    );
    """
    )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("✅ 数据库初始化完成！data/novel.db 已就绪。")
