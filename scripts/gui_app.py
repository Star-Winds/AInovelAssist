# scripts/gui_app.py

"""
DearPyGUI UI for AInovelAssist.
"""

from pathlib import Path
from typing import Callable

import dearpygui.dearpygui as dpg

from scripts.app import DEMO_CHAPTER, DEMO_TEXT, DEMO_TITLE
from scripts.assistant import NovelAssistant
from scripts.vector_db import VectorStore
OUTPUT_TAG = "output_text"


class Application:
    def __init__(self, db_path: str, index_path: str):
        self.db_path = db_path
        self.index_path = index_path

        self.prompt = "写段小说来看看吧？"
        self.document = DEMO_TITLE
        self.chapter = DEMO_CHAPTER
        self.search_query = "徽章 北方"
        self.hint = "雨夜"

        self._build_layout()

    # --------------------- layout ---------------------
    def _build_layout(self) -> None:
        dpg.create_context()

        # -------- 注册中文字体 --------
        with dpg.font_registry():
            candidates = [
                Path(r"C:\Windows\Fonts\msyh.ttc"),
                Path(r"C:\Windows\Fonts\simhei.ttf"),
            ]
            font_path = next((p for p in candidates if p.exists()), None)

            if font_path is not None:
                with dpg.font(str(font_path), 18, tag="default_font"):
                    dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
                    dpg.add_font_range_hint(dpg.mvFontRangeHint_Chinese_Full)
                dpg.bind_font("default_font")
            else:
                print("[字体警告] 未找到系统中文字体，将使用默认字体。")

        # ---------------- UI 界面 ----------------
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
            dpg.add_text("章节内容", color=(180, 180, 255))
            dpg.add_input_text(
                label="",
                tag="chapter_body",
                multiline=True,
                height=260,
                width=-1,
                hint="在这里粘贴或编写你的章节正文……",
            )

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
                tag=OUTPUT_TAG,
                multiline=True,
                 readonly=True,
                height=200,
                width=-1,
                default_value="点击上方按钮开始吧！\n推荐流程：先粘贴章节 → 收纳章节 → 重建向量 → 相似检索。",
            )

        dpg.create_viewport(title="AInovelAssist", width=1000, height=760)
        dpg.setup_dearpygui()
        dpg.show_viewport()

    # --------------------- helpers ---------------------
    def _show_text(self, text: str) -> None:
            # 防御性检查，避免传入不存在的 item id
        if not dpg.does_item_exist(OUTPUT_TAG):
            print("[UI警告] 输出控件不存在，准备输出的内容为：")
            print(text[:200])
            return
        dpg.set_value(OUTPUT_TAG, text)

    def _run_action(self, handler: Callable[[], str]) -> None:
        try:
            result = handler()
        except Exception as exc:
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
    def run_demo(self, sender=None, app_data=None) -> None:
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

    def free_write(self, sender=None, app_data=None) -> None:
        def handler() -> str:
            assistant = self._create_assistant()
            return assistant.free_write(dpg.get_value("prompt"), paragraphs=2)

        self._run_action(handler)

    def collect_text(self, sender=None, app_data=None) -> None:
        def handler() -> str:
            assistant = self._create_assistant()
            chapter_body = dpg.get_value("chapter_body")
            if not chapter_body.strip():
                return "⚠️ 章节内容为空，请先在「章节内容」里粘贴或输入文本。"

            doc_id, chapter_id, chunks = assistant.collect_text(
                dpg.get_value("document"),
                dpg.get_value("chapter"),
                chapter_body,
                chunk_size=400,
            )
            return (
                "✅ 已入库\n"
                f"document_id={doc_id}\nchapter_id={chapter_id}\nchunks={chunks}"
            )

        self._run_action(handler)

    def rebuild_index(self, sender=None, app_data=None) -> None:
        def handler() -> str:
            store = self._create_store()
            store.rebuild()
            return f"✅ 索引已重建并保存至 {dpg.get_value('index_path')}"

        self._run_action(handler)

    def search_chunks(self, sender=None, app_data=None) -> None:
        def handler() -> str:
            store = self._create_store()
            results = store.search(dpg.get_value("search_query"), top_k=5)
            lines = store.as_lines(results)
            return "\n".join(lines) if lines else "未找到匹配结果，请尝试换个关键词。"

        self._run_action(handler)

    def inspire(self, sender=None, app_data=None) -> None:
        def handler() -> str:
            assistant = self._create_assistant()
            ideas = assistant.inspire(dpg.get_value("document"), hint=dpg.get_value("hint"))
            return "\n".join(ideas)

        self._run_action(handler)

    def review_chapter(self, sender=None, app_data=None) -> None:
        def handler() -> str:
            assistant = self._create_assistant()
            chapter_body = dpg.get_value("chapter_body")
            if not chapter_body.strip():
                return "⚠️ 章节内容为空，请先在「章节内容」里粘贴或输入文本。"

            feedback = assistant.review_chapter(dpg.get_value("document"), chapter_body)
            return "\n".join(feedback)

        self._run_action(handler)


def launch(db_path: str = "data/novel.db", index_path: str = "data/vector_store.joblib") -> None:
    app = Application(db_path=db_path, index_path=index_path)
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    launch()
