# scripts/ingest.py
# -*- coding: utf-8 -*-
"""
强化版：更稳的文本读取
- UTF-8 BOM 自动处理
- 对可疑编码(如 cp949/euc_kr)做多候选重试，自动选择“更像中文”的结果
- 保留 --print / --debug
"""

import sys
import argparse
from pathlib import Path
from charset_normalizer import from_path
from docx import Document


def _score_text_for_cn(text: str) -> int:
    """为解码结果打分：越像中文分数越高，出现替换符/控制符越多越低"""
    score = 0
    fffd = text.count("\ufffd")  # 无法解码的替换符
    # 统计中日韩统一表意文字 & 常见中文标点
    cjk = sum(0x4e00 <= ord(ch) <= 0x9fff for ch in text)
    cn_punc = "，。！？、；：「」『』（）《》—…·"
    punc = sum(ch in cn_punc for ch in text)
    # 减去明显异常字符（私用区/控制符）
    ctrl = sum(ord(ch) < 32 and ch not in "\n\t\r" for ch in text)

    score += cjk * 2 + punc * 2
    score -= fffd * 5 + ctrl * 2
    return score


def _try_read(path: Path, enc: str) -> str:
    # utf-8 BOM 处理：优先用 utf-8-sig 去掉 BOM
    enc_norm = enc.lower().replace("-", "_")
    if enc_norm.startswith("utf_8"):
        enc = "utf-8-sig"
    with open(path, "r", encoding=enc, errors="replace") as f:
        return f.read()


def detect_and_read(path: Path):
    """
    返回 (text:str, chosen_encoding:str, file_size:int)
    策略：
      1) docx 用 python-docx
      2) 其他文本：先用 charset-normalizer 的 best.encoding
      3) 若可疑或解码像乱码，则在候选编码集合中择优
    """
    if path.suffix.lower() == ".docx":
        doc = Document(path)
        text = "\n".join(p.text for p in doc.paragraphs)
        return text, "docx", path.stat().st_size

    # 先探测一次
    result = from_path(path)
    if not result:
        raise ValueError(f"无法探测文件编码: {path}")
    best = result.best()
    detected = (best.encoding or "utf-8").strip()

    # 构造候选编码（按优先级，去重）
    candidates = []
    def add(enc):
        if enc and enc not in candidates:
            candidates.append(enc)

    add(detected)
    # 常见中文编码/回退
    add("utf-8-sig")
    add("gbk"); add("cp936")
    add("big5")
    add("utf-16")
    # 如果误判成韩文相关，强制把 gbk/cp936 放前面再试
    if detected.lower() in ("cp949", "euc_kr", "ks_c_5601-1987"):
        candidates = ["gbk", "cp936", "utf-8-sig", detected, "big5", "utf-16"]

    # 逐个尝试并打分
    best_text, best_enc, best_score = "", None, -10**9
    for enc in candidates:
        try:
            text = _try_read(path, enc)
            sc = _score_text_for_cn(text)
            if sc > best_score:
                best_text, best_enc, best_score = text, enc, sc
        except Exception:
            continue

    # 兜底：再尝试 utf-8
    if best_enc is None:
        best_text = _try_read(path, "utf-8-sig")
        best_enc = "utf-8-sig"

    return best_text, best_enc, path.stat().st_size


def clean_text(text: str) -> str:
    """统一换行符并压缩多余空行"""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    cleaned, empty_count = [], 0
    for line in lines:
        if line.strip() == "":
            empty_count += 1
            if empty_count <= 1:
                cleaned.append("")
        else:
            empty_count = 0
            cleaned.append(line)
    return "\n".join(cleaned).strip()


def main():
    parser = argparse.ArgumentParser(description="导入并清洗章节文本")
    parser.add_argument("filepath", help="要读取的章节文件路径")
    parser.add_argument("--print", action="store_true", help="打印清洗后的结果")
    parser.add_argument("--debug", action="store_true", help="打印调试信息")
    args = parser.parse_args()

    path = Path(args.filepath)
    if not path.exists():
        print(f"❌ 文件不存在: {path}")
        sys.exit(1)

    raw_text, enc, fsize = detect_and_read(path)
    cleaned = clean_text(raw_text)

    if args.debug:
        print("=== DEBUG ===")
        print(f"文件: {path}")
        print(f"探测/选择的编码: {enc}")
        print(f"文件大小(字节): {fsize}")
        print(f"原始长度: {len(raw_text)}")
        preview = raw_text[:120].replace("\n", "\\n")
        print(f"原始前120字符: {preview}")
        print(f"清洗后长度: {len(cleaned)}")
        print("=============\n")

    if args.print:
        print("=== 清洗后文本预览 ===\n")
        if cleaned:
            print(cleaned[:2000])
            if len(cleaned) > 2000:
                print("\n=== (已截断预览) ===")
        else:
            print("(清洗后为空，长度=0)")
    else:
        print(f"✅ 成功读取并清洗文件: {path.name} ({len(cleaned)} 字符)")


if __name__ == "__main__":
    main()
