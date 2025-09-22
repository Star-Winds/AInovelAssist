# scripts/ingest.py
from pathlib import Path
import re

def load_chapter_text(path: str | Path) -> str:
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"Chapter file not found: {p}")

    # 读取并处理编码
    raw = p.read_bytes()
    # 简单尝试：utf-8 带/不带 BOM
    text = raw.decode("utf-8", errors="replace").lstrip("\ufeff")

    # 归一化换行：\r\n / \r -> \n
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 去除常见页眉/页脚/页码（按需扩展）
    # 例如：第12页 / Page 3 / —— 分割线 —— 等
    patterns = [
        r"^\s*第?\s*\d+\s*页\s*$",
        r"^\s*Page\s*\d+\s*$",
        r"^\s*[–—-]{2,}\s*$",
    ]
    for pat in patterns:
        text = re.sub(pat, "", text, flags=re.MULTILINE)

    # 合并多余空行（最多保留 1 行）
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 去除行首/尾多余空格
    text = "\n".join(line.strip() for line in text.split("\n"))

    # 收尾：整体首尾空白
    text = text.strip()

    return text

if __name__ == "__main__":
    # 方便命令行快速预览清洗结果
    import sys
    if len(sys.argv) != 2:
        print("Usage: python scripts/ingest.py <chapter.txt>")
        sys.exit(1)
    cleaned = load_chapter_text(sys.argv[1])
    print(cleaned)
