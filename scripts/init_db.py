import sqlite3
from pathlib import Path 

def init_db():
    # 确保 data 文件夹存在（没有就创建）
    Path("data").mkdir(exist_ok=True)

    # 连接数据库（如果 data/novel.db 不存在，会自动新建）
    conn = sqlite3.connect("data/novel.db")
    cursor = conn.cursor()

    # 在数据库里新建一张表 documents
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        source TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chapters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER,
        idx INTEGER,
        title TEXT,
        path TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chapter_id INTEGER,
        idx INTEGER,
        text TEXT,
        char_len INTEGER
    );
    """)


    # 保存修改并关闭连接
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("数据库初始化完成！")

