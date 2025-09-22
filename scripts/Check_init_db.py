import sqlite3

def list_tables():
    conn = sqlite3.connect("data/novel.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    conn.close()
    return [t[0] for t in tables]

if __name__ == "__main__":
    print("数据库中的表：", list_tables())
