"""Simple console application for AInovelAssist workflows.

Features
--------
* Seed a demo story into SQLite for quick testing.
* Rebuild and query the TF-IDF vector index.
* Offer basic authoring helpers: free writing, review tips, inspiration.

The app is intentionally minimal so it can run anywhere Python is available.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from textwrap import dedent
from typing import List

from scripts.assistant import NovelAssistant
from scripts.vector_db import VectorStore

DEMO_TITLE = "边城纪事"
DEMO_CHAPTER = "序章：码头的徽章"
DEMO_TEXT = dedent(
    """
    阿黎在码头等船，晚风吹起旧城的号角声。陌生人递给她一枚带血的徽章，
    并让她去北方的灯塔。柳青躲在暗处观察，记录下每一个细节。雨将至，
    远处的钟声敲响，仿佛在催促她踏上未知的旅程。
    """
).strip()


def seed_demo_story(db_path: str) -> None:
    """Insert a short sample chapter if the demo story is missing."""
    assistant = NovelAssistant(db_path)
    repo = assistant.repo
    repo.bootstrap()
    with repo._connect() as conn:
        existing = conn.execute(
            """
            SELECT COUNT(*) FROM chapters
            WHERE document_id=(SELECT id FROM documents WHERE title=?)
            """,
            (DEMO_TITLE,),
        ).fetchone()[0]
    if existing:
        return
    assistant.collect_text(DEMO_TITLE, DEMO_CHAPTER, DEMO_TEXT, chunk_size=400)


def run_demo(db_path: str, index_path: str) -> str:
    """Build a mini workflow and return a human-readable summary."""
    seed_demo_story(db_path)

    assistant = NovelAssistant(db_path)
    store = VectorStore(db_path, index_path)
    store.rebuild()
    demo_query = "徽章 北方"
    results = store.search(demo_query, top_k=3)
    lines = store.as_lines(results)

    summary_lines = [
        "🎬 AInovelAssist 简易演示",
        f"数据库: {db_path}",
        f"向量索引: {index_path}",
        "",
        "自由创作示例:",
        assistant.free_write("写段小说来看看吧？", paragraphs=1),
        "",
        "相似检索示例 (查询: " + demo_query + "):",
        *lines,
        "",
        "灵感提示:",
        *assistant.inspire(DEMO_TITLE, hint="雨夜"),
    ]
    return "\n".join(summary_lines)


def _load_text(file_or_text: str) -> str:
    path = Path(file_or_text)
    if path.exists():
        return path.read_text(encoding="utf-8")
    return file_or_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AInovelAssist CLI 应用程序")
    parser.add_argument("--db", default="data/novel.db", help="SQLite 数据库路径")
    parser.add_argument(
        "--index", default="data/vector_store.joblib", help="向量索引存放路径"
    )

    sub = parser.add_subparsers(dest="command", required=False)

    sub.add_parser("demo", help="运行内置示例并输出结果")

    fw = sub.add_parser("free-write", help="生成自由创作段落")
    fw.add_argument("prompt", help="提示语")
    fw.add_argument("--paragraphs", type=int, default=2, help="段落数量")

    collect = sub.add_parser("collect", help="收纳章节并入库")
    collect.add_argument("document", help="作品标题")
    collect.add_argument("chapter", help="章节标题")
    collect.add_argument("content", help="章节内容或文件路径")
    collect.add_argument("--chunk-size", type=int, default=1200, help="分块大小")

    rebuild = sub.add_parser("rebuild", help="从数据库重建向量索引")
    rebuild.add_argument("--silent", action="store_true", help="只输出成功提示")

    search = sub.add_parser("search", help="在向量索引中检索相似段落")
    search.add_argument("query", help="查询文本")
    search.add_argument("--topk", type=int, default=5, help="返回数量")

    inspire = sub.add_parser("inspire", help="基于作品生成灵感提示")
    inspire.add_argument("document", help="作品标题")
    inspire.add_argument("--hint", help="额外提示", default=None)

    review = sub.add_parser("review", help="对新章节给出审稿建议")
    review.add_argument("document", help="作品标题")
    review.add_argument("content", help="章节内容或文件路径")

    return parser


def handle_command(args: argparse.Namespace) -> str:
    assistant = NovelAssistant(args.db)
    store = VectorStore(args.db, args.index)

    if args.command == "free-write":
        return assistant.free_write(args.prompt, paragraphs=args.paragraphs)

    if args.command == "collect":
        text = _load_text(args.content)
        doc_id, chapter_id, chunks = assistant.collect_text(
            args.document, args.chapter, text, chunk_size=args.chunk_size
        )
        return f"已入库: document_id={doc_id}, chapter_id={chapter_id}, chunks={chunks}"

    if args.command == "rebuild":
        store.rebuild()
        if args.silent:
            return "ok"
        return f"索引已保存至 {args.index}"

    if args.command == "search":
        results = store.search(args.query, top_k=args.topk)
        lines = store.as_lines(results)
        return "\n".join(lines) if lines else "未找到匹配结果。"

    if args.command == "inspire":
        ideas = assistant.inspire(args.document, hint=args.hint)
        return "\n".join(ideas)

    if args.command == "review":
        text = _load_text(args.content)
        feedback = assistant.review_chapter(args.document, text)
        return "\n".join(feedback)

    # default: run demo
    return run_demo(args.db, args.index)


def main(argv: List[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    output = handle_command(args)
    print(output)


if __name__ == "__main__":
    main()
