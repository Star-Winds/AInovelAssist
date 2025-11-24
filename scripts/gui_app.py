"""Minimal Tkinter UI for AInovelAssist.

The UI focuses on a few core workflows:
- Run the demo pipeline (seed, rebuild vectors, search, inspire).
- Free write paragraphs from a prompt.
- Collect chapter text into SQLite.
- Rebuild and search the TF-IDF vector index.
- Generate inspiration or review feedback for a document.

It is intentionally lightweight so it can be packaged into a single-file
executable via PyInstaller.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from scripts.app import DEMO_CHAPTER, DEMO_TEXT, DEMO_TITLE
from scripts.assistant import NovelAssistant
from scripts.vector_db import VectorStore


class Application(ttk.Frame):
    def __init__(self, master: tk.Tk, db_path: str, index_path: str):
        super().__init__(master)
        self.master = master
        self.db_path = tk.StringVar(value=db_path)
        self.index_path = tk.StringVar(value=index_path)

        self.prompt = tk.StringVar(value="写段小说来看看吧？")
        self.document = tk.StringVar(value=DEMO_TITLE)
        self.chapter = tk.StringVar(value=DEMO_CHAPTER)
        self.search_query = tk.StringVar(value="徽章 北方")
        self.hint = tk.StringVar(value="雨夜")

        self.output = tk.Text(self, height=20, width=80, wrap="word")
        self._build_layout()

    # --------------------- layout ---------------------
    def _build_layout(self) -> None:
        self.master.title("AInovelAssist UI")
        self.pack(fill="both", expand=True, padx=10, pady=10)

        # Paths row
        path_frame = ttk.LabelFrame(self, text="存储位置")
        path_frame.pack(fill="x", pady=5)
        ttk.Label(path_frame, text="数据库").grid(row=0, column=0, sticky="w")
        ttk.Entry(path_frame, textvariable=self.db_path, width=50).grid(
            row=0, column=1, sticky="ew", padx=4, pady=2
        )
        ttk.Label(path_frame, text="向量索引").grid(row=1, column=0, sticky="w")
        ttk.Entry(path_frame, textvariable=self.index_path, width=50).grid(
            row=1, column=1, sticky="ew", padx=4, pady=2
        )

        # Prompt row
        prompt_frame = ttk.LabelFrame(self, text="创作与检索")
        prompt_frame.pack(fill="x", pady=5)
        ttk.Label(prompt_frame, text="自由创作提示").grid(row=0, column=0, sticky="w")
        ttk.Entry(prompt_frame, textvariable=self.prompt, width=60).grid(
            row=0, column=1, sticky="ew", padx=4, pady=2
        )
        ttk.Label(prompt_frame, text="检索关键词").grid(row=1, column=0, sticky="w")
        ttk.Entry(prompt_frame, textvariable=self.search_query, width=60).grid(
            row=1, column=1, sticky="ew", padx=4, pady=2
        )
        ttk.Label(prompt_frame, text="灵感提示词").grid(row=2, column=0, sticky="w")
        ttk.Entry(prompt_frame, textvariable=self.hint, width=60).grid(
            row=2, column=1, sticky="ew", padx=4, pady=2
        )

        # Document row
        doc_frame = ttk.LabelFrame(self, text="作品信息")
        doc_frame.pack(fill="x", pady=5)
        ttk.Label(doc_frame, text="作品标题").grid(row=0, column=0, sticky="w")
        ttk.Entry(doc_frame, textvariable=self.document, width=40).grid(
            row=0, column=1, sticky="ew", padx=4, pady=2
        )
        ttk.Label(doc_frame, text="章节标题").grid(row=1, column=0, sticky="w")
        ttk.Entry(doc_frame, textvariable=self.chapter, width=40).grid(
            row=1, column=1, sticky="ew", padx=4, pady=2
        )

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", pady=8)
        actions = [
            ("运行 Demo", self.run_demo),
            ("自由创作", self.free_write),
            ("收纳章节", self.collect_text),
            ("重建向量", self.rebuild_index),
            ("相似检索", self.search_chunks),
            ("灵感提示", self.inspire),
            ("章节审阅", self.review_chapter),
        ]
        for idx, (label, func) in enumerate(actions):
            ttk.Button(button_frame, text=label, command=func).grid(
                row=0, column=idx, padx=3, pady=2
            )

        # Output box
        output_frame = ttk.LabelFrame(self, text="输出")
        output_frame.pack(fill="both", expand=True, pady=5)
        self.output.pack(in_=output_frame, fill="both", expand=True, padx=6, pady=6)
        self.output.configure(state="disabled")

    # --------------------- helpers ---------------------
    def _show_text(self, text: str) -> None:
        self.output.configure(state="normal")
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, text)
        self.output.configure(state="disabled")

    def _run_action(self, handler: Callable[[], str]) -> None:
        try:
            result = handler()
        except Exception as exc:  # surface error to UI
            result = f"❌ 操作失败：{exc}"
        self._show_text(result)

    def _create_assistant(self) -> NovelAssistant:
        return NovelAssistant(self.db_path.get())

    def _create_store(self) -> VectorStore:
        return VectorStore(self.db_path.get(), self.index_path.get())

    # --------------------- actions ---------------------
    def run_demo(self) -> None:
        def handler() -> str:
            assistant = self._create_assistant()
            store = self._create_store()
            assistant.collect_text(DEMO_TITLE, DEMO_CHAPTER, DEMO_TEXT, chunk_size=400)
            store.rebuild()
            results = store.search(self.search_query.get(), top_k=3)
            lines = store.as_lines(results)
            inspire = assistant.inspire(DEMO_TITLE, hint=self.hint.get())
            return "\n".join(
                [
                    "🎬 Demo 已就绪",
                    "自由创作:",
                    assistant.free_write(self.prompt.get(), paragraphs=1),
                    "",
                    "相似检索:",
                    *lines,
                    "",
                    "灵感提示:",
                    *inspire,
                ]
            )

        self._run_action(handler)

    def free_write(self) -> None:
        def handler() -> str:
            assistant = self._create_assistant()
            return assistant.free_write(self.prompt.get(), paragraphs=2)

        self._run_action(handler)

    def collect_text(self) -> None:
        def handler() -> str:
            assistant = self._create_assistant()
            doc_id, chapter_id, chunks = assistant.collect_text(
                self.document.get(), self.chapter.get(), self.prompt.get(), chunk_size=400
            )
            return (
                "已入库\n"
                f"document_id={doc_id}\nchapter_id={chapter_id}\nchunks={chunks}"
            )

        self._run_action(handler)

    def rebuild_index(self) -> None:
        def handler() -> str:
            store = self._create_store()
            store.rebuild()
            return f"索引已保存至 {self.index_path.get()}"

        self._run_action(handler)

    def search_chunks(self) -> None:
        def handler() -> str:
            store = self._create_store()
            results = store.search(self.search_query.get(), top_k=5)
            lines = store.as_lines(results)
            return "\n".join(lines) if lines else "未找到匹配结果。"

        self._run_action(handler)

    def inspire(self) -> None:
        def handler() -> str:
            assistant = self._create_assistant()
            ideas = assistant.inspire(self.document.get(), hint=self.hint.get())
            return "\n".join(ideas)

        self._run_action(handler)

    def review_chapter(self) -> None:
        def handler() -> str:
            assistant = self._create_assistant()
            feedback = assistant.review_chapter(self.document.get(), self.prompt.get())
            return "\n".join(feedback)

        self._run_action(handler)


def launch(db_path: str = "data/novel.db", index_path: str = "data/vector_store.joblib") -> None:
    root = tk.Tk()
    Application(root, db_path=db_path, index_path=index_path)
    root.mainloop()


if __name__ == "__main__":
    launch()
