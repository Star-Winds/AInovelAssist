"""DearPyGUI UI for AInovelAssist.

The interface surfaces the same workflows as the original Tkinter version but
uses DearPyGUI widgets for a modern, responsive look:
- Run the demo pipeline (seed, rebuild vectors, search, inspire).
- Free write paragraphs from a prompt.
- Collect chapter text into SQLite.
- Rebuild and search the TF-IDF vector index.
- Generate inspiration or review feedback for a document.
"""
from __future__ import annotations

from typing import Callable

import dearpygui.dearpygui as dpg

from scripts.app import DEMO_CHAPTER, DEMO_TEXT, DEMO_TITLE
from scripts.assistant import NovelAssistant
from scripts.vector_db import VectorStore


class Application:
    def __init__(self, db_path: str, index_path: str):
        self.db_path = db_path
        self.index_path = index_path

        self.prompt = "写段小说来看看吧？"
        self.document = DEMO_TITLE
        self.chapter = DEMO_CHAPTER
        self.search_query = "徽章 北方"
        self.hint = "雨夜"

        self.output_tag = "output_text"
        self._build_layout()

    # --------------------- layout ---------------------
    def _build_layout(self) -> None:
        dpg.create_context()
        with dpg.font_registry():
            pass  # placeholder in case custom fonts are added later

        with dpg.window(tag="MainWindow", label="AInovelAssist UI", width=980, height=720):
            dpg.add_text("存储位置", color=(180, 180, 255))
            with dpg.group(horizontal=True):
                dpg.add_input_text(label="数据库", default_value=self.db_path, tag="db_path", width=320)
                dpg.add_spacer(width=12)
                dpg.add_input_text(label="向量索引", default_value=self.index_path, tag="index_path", width=320)

            dpg.add_separator()
            dpg.add_text("创作与检索", color=(180, 180, 255))
            dpg.add_input_text(label="自由创作提示", default_value=self.prompt, tag="prompt", width=-1)
            dpg.add_input_text(label="检索关键词", default_value=self.search_query, tag="search_query", width=-1)
            dpg.add_input_text(label="灵感提示词", default_value=self.hint, tag="hint", width=-1)

            dpg.add_separator()
            dpg.add_text("作品信息", color=(180, 180, 255))
            with dpg.group(horizontal=True):
                dpg.add_input_text(label="作品标题", default_value=self.document, tag="document", width=300)
                dpg.add_spacer(width=12)
                dpg.add_input_text(label="章节标题", default_value=self.chapter, tag="chapter", width=300)

            dpg.add_separator()
            dpg.add_text("操作", color=(180, 180, 255))
            with dpg.group(horizontal=True):
                actions = [
                    ("运行 Demo", self.run_demo),
                    ("自由创作", self.free_write),
                    ("收纳章节", self.collect_text),
                    ("重建向量", self.rebuild_index),
                    ("相似检索", self.search_chunks),
                    ("灵感提示", self.inspire),
                    ("章节审阅", self.review_chapter),
                ]
                for label, func in actions:
                    dpg.add_button(label=label, callback=func, width=110)

            dpg.add_separator()
            dpg.add_text("输出", color=(180, 180, 255))
            dpg.add_input_text(
                tag=self.output_tag,
                multiline=True,
                readonly=True,
                height=360,
                width=-1,
                default_value="点击上方按钮开始吧！",
            )

        dpg.create_viewport(title="AInovelAssist", width=1000, height=760)
        dpg.setup_dearpygui()
        dpg.show_viewport()

    # --------------------- helpers ---------------------
    def _show_text(self, text: str) -> None:
        dpg.set_value(self.output_tag, text)

    def _run_action(self, handler: Callable[[], str]) -> None:
        try:
            result = handler()
        except Exception as exc:  # surface error to UI
            result = f"❌ 操作失败：{exc}"
        self._show_text(result)

    def _create_assistant(self) -> NovelAssistant:
        db_path = dpg.get_value("db_path")
        return NovelAssistant(db_path)

    def _create_store(self) -> VectorStore:
        db_path = dpg.get_value("db_path")
        index_path = dpg.get_value("index_path")
        return VectorStore(db_path, index_path)

    # --------------------- actions ---------------------
    def run_demo(self, sender=None, app_data=None) -> None:  # type: ignore[override]
        def handler() -> str:
            assistant = self._create_assistant()
            store = self._create_store()
            assistant.collect_text(DEMO_TITLE, DEMO_CHAPTER, DEMO_TEXT, chunk_size=400)
            store.rebuild()
            results = store.search(dpg.get_value("search_query"), top_k=3)
            lines = store.as_lines(results)
            inspire = assistant.inspire(DEMO_TITLE, hint=dpg.get_value("hint"))
            return "\n".join(
                [
                    "🎬 Demo 已就绪",
                    "自由创作:",
                    assistant.free_write(dpg.get_value("prompt"), paragraphs=1),
                    "",
                    "相似检索:",
                    *lines,
                    "",
                    "灵感提示:",
                    *inspire,
                ]
            )

        self._run_action(handler)

    def free_write(self, sender=None, app_data=None) -> None:  # type: ignore[override]
        def handler() -> str:
            assistant = self._create_assistant()
            return assistant.free_write(dpg.get_value("prompt"), paragraphs=2)

        self._run_action(handler)

    def collect_text(self, sender=None, app_data=None) -> None:  # type: ignore[override]
        def handler() -> str:
            assistant = self._create_assistant()
            doc_id, chapter_id, chunks = assistant.collect_text(
                dpg.get_value("document"),
                dpg.get_value("chapter"),
                dpg.get_value("prompt"),
                chunk_size=400,
            )
            return (
                "已入库\n"
                f"document_id={doc_id}\nchapter_id={chapter_id}\nchunks={chunks}"
            )

        self._run_action(handler)

    def rebuild_index(self, sender=None, app_data=None) -> None:  # type: ignore[override]
        def handler() -> str:
            store = self._create_store()
            store.rebuild()
            return f"索引已保存至 {dpg.get_value('index_path')}"

        self._run_action(handler)

    def search_chunks(self, sender=None, app_data=None) -> None:  # type: ignore[override]
        def handler() -> str:
            store = self._create_store()
            results = store.search(dpg.get_value("search_query"), top_k=5)
            lines = store.as_lines(results)
            return "\n".join(lines) if lines else "未找到匹配结果。"

        self._run_action(handler)

    def inspire(self, sender=None, app_data=None) -> None:  # type: ignore[override]
        def handler() -> str:
            assistant = self._create_assistant()
            ideas = assistant.inspire(dpg.get_value("document"), hint=dpg.get_value("hint"))
            return "\n".join(ideas)

        self._run_action(handler)

    def review_chapter(self, sender=None, app_data=None) -> None:  # type: ignore[override]
        def handler() -> str:
            assistant = self._create_assistant()
            feedback = assistant.review_chapter(dpg.get_value("document"), dpg.get_value("prompt"))
            return "\n".join(feedback)

        self._run_action(handler)


def launch(db_path: str = "data/novel.db", index_path: str = "data/vector_store.joblib") -> None:
    app = Application(db_path=db_path, index_path=index_path)
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    launch()
