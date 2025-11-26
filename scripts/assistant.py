import os
from openai import OpenAI

SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")
if not SILICONFLOW_API_KEY:
    raise RuntimeError("环境变量 SILICONFLOW_API_KEY 未设置，无法调用硅基流动 API。")

client = OpenAI(
    base_url="https://api.siliconflow.cn/v1",
    api_key=SILICONFLOW_API_KEY,
)

# 选一个具体模型（你可以去硅基流动“模型广场”换别的）
MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"
# 或者比如：
# MODEL_NAME = "deepseek-ai/DeepSeek-V2.5"

"""High-level assistant utilities for AI novel workflows.

This module adds:
- Free writing mode for quick inspiration paragraphs.
- Editorial mode with text collection, character cards, and chapter review.
- Inspiration suggestions that build on stored outlines/chapters.
"""

import random
import re
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from scripts.ingest import clean_text, split_into_chunks
from scripts.init_db import init_db


@dataclass
class CharacterCard:
    name: str
    mentions: int
    first_chapter: str
    key_moments: List[str] = field(default_factory=list)
    traits: Dict[str, str] = field(default_factory=dict)
    timeline: List[str] = field(default_factory=list)


class StoryRepository:
    """Small helper around the SQLite schema for storing chapters and chunks."""

    def __init__(self, db_path: str = "data/novel.db"):
        self.db_path = Path(db_path)

    def bootstrap(self) -> None:
        init_db(str(self.db_path))

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def upsert_document(self, title: str, source: str | None = None) -> int:
        self.bootstrap()
        with self._connect() as conn:
            cur = conn.execute("SELECT id FROM documents WHERE title=?", (title,))
            row = cur.fetchone()
            if row:
                return row["id"]
            cur = conn.execute(
                "INSERT INTO documents(title, source, created_at) VALUES (?, ?, ?)",
                (title, source, datetime.now().isoformat(timespec="seconds")),
            )
            return cur.lastrowid

    def _next_chapter_index(self, conn, document_id: int) -> int:
        cur = conn.execute(
            'SELECT COALESCE(MAX("index"), 0) FROM chapters WHERE document_id=?',
            (document_id,),
        )
        return cur.fetchone()[0] + 1

    def add_chapter(
        self,
        document_title: str,
        chapter_title: str,
        raw_text: str,
        chunk_size: int = 1200,
        path: str | None = None,
    ) -> Tuple[int, int, int]:
        """Store a chapter and its chunks. Returns (document_id, chapter_id, chunks)."""
        cleaned = clean_text(raw_text)
        pieces = split_into_chunks(cleaned, chunk_size)

        doc_id = self.upsert_document(document_title)
        with self._connect() as conn:
            chapter_index = self._next_chapter_index(conn, doc_id)
            cur = conn.execute(
                'INSERT INTO chapters(document_id, "index", title, path) VALUES (?, ?, ?, ?)',
                (doc_id, chapter_index, chapter_title, path),
            )
            chapter_id = cur.lastrowid
            for idx, piece in enumerate(pieces, start=1):
                conn.execute(
                    'INSERT INTO chunks(chapter_id, "index", text, char_len) VALUES (?, ?, ?, ?)',
                    (chapter_id, idx, piece, len(piece)),
                )
        return doc_id, chapter_id, len(pieces)

    def iter_chapters(self, document_title: str) -> Iterable[Tuple[str, str]]:
        """Yield chapter title and concatenated text for a document (ordered)."""
        self.bootstrap()
        with self._connect() as conn:
            cur = conn.execute("SELECT id FROM documents WHERE title=?", (document_title,))
            doc_row = cur.fetchone()
            if not doc_row:
                return []
            doc_id = doc_row["id"]
            chapters = conn.execute(
                'SELECT id, "index", title FROM chapters WHERE document_id=? ORDER BY "index"',
                (doc_id,),
            ).fetchall()
            for chap in chapters:
                chunks = conn.execute(
                    'SELECT text FROM chunks WHERE chapter_id=? ORDER BY "index"',
                    (chap["id"],),
                ).fetchall()
                yield chap["title"], "\n".join(c["text"] for c in chunks)

    def flatten_document(self, document_title: str) -> str:
        parts = [text for _, text in self.iter_chapters(document_title)]
        return "\n".join(parts)


def free_write(prompt: str, paragraphs: int = 2, seed: int = 2025) -> str:
    """Generate a short narrative draft without requiring an outline.

    The function is intentionally lightweight and deterministic to make
    tests reliable while still giving users a creative nudge.
    """
    random.seed(seed)
    moods = [
        "雾气弥漫的黎明",
        "落日映红的旧城",
        "暴雨前压抑的空气",
        "雪夜里安静的边境",
    ]
    hooks = [
        "一封无人署名的信件",
        "一盏闪烁的路灯",
        "一段被遗忘的旋律",
        "一枚带血的徽章",
    ]
    beats = [
        "让主角意识到故事已经偏离日常。",
        "迫使角色做出与性格吻合的选择。",
        "抛出一个和过去有关的伏笔。",
        "留下可以在后续章节回收的意象。",
    ]

    paragraphs = max(1, paragraphs)
    opening = random.choice(moods)
    clue = random.choice(hooks)
    output = []
    for _ in range(paragraphs):
        beat = random.choice(beats)
        line = (
            f"{opening}里，{prompt}。{clue}引出了新的视角，"
            f"而叙述刻意放缓，{beat}"
        )
        output.append(line)
        opening = random.choice(moods)
        clue = random.choice(hooks)
    return "\n\n".join(output)


def _extract_names(text: str) -> Counter:
    """Lightweight name guesser based on repeated bigrams/trigrams.

    Without a tokenizer we approximate names by counting overlapping windows
    of Chinese characters. Repeated windows are treated as higher-confidence
    candidates. If nothing repeats, we still return the top few tokens so the
    assistant can surface at least one lead character.
    """
    stopwords = {"但是", "然而", "于是", "因为", "所以", "虽然", "甚至"}
    cleaned = re.sub(r"[^\u4e00-\u9fff]", "", text)
    counts: Counter = Counter()
    for size in (2, 3):
        for idx in range(len(cleaned) - size + 1):
            token = cleaned[idx : idx + size]
            if token in stopwords:
                continue
            counts[token] += 1

    repeated = {name: cnt for name, cnt in counts.items() if cnt > 1}
    if repeated:
        return Counter(repeated)
    # Fallback: keep the most likely few names
    return Counter({name: counts[name] for name, _ in counts.most_common(3)})


def build_character_cards(chapters: Iterable[Tuple[str, str]]) -> List[CharacterCard]:
    name_totals: Counter = Counter()
    first_seen: Dict[str, str] = {}
    timelines: Dict[str, List[str]] = defaultdict(list)
    key_lines: Dict[str, List[str]] = defaultdict(list)

    for chapter_title, text in chapters:
        for name, count in _extract_names(text).items():
            name_totals[name] += count
            if name not in first_seen:
                first_seen[name] = chapter_title
            timelines[name].append(chapter_title)
            sentences = re.split(r"[。！？]", text)
            for sentence in sentences:
                if name in sentence and sentence.strip():
                    key_lines[name].append(sentence.strip())

    cards: List[CharacterCard] = []
    for name, mentions in name_totals.most_common():
        cards.append(
            CharacterCard(
                name=name,
                mentions=mentions,
                first_chapter=first_seen.get(name, ""),
                key_moments=key_lines.get(name, [])[:3],
                traits={
                    "戏份": "主角" if mentions == name_totals.most_common(1)[0][1] else "配角",
                    "稳定度": "性格保持稳定" if mentions > 1 else "需要进一步观察",
                },
                timeline=timelines.get(name, []),
            )
        )
    return cards


class NovelAssistant:
    """Facade that bundles free writing, text collection, and editing helpers."""

    def __init__(self, db_path: str = "data/novel.db"):
        self.repo = StoryRepository(db_path)

    def _chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        """调用硅基流动 chat.completions，返回一段文本。"""
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
        )
        # OpenAI 风格：choices[0].message.content
        return resp.choices[0].message.content.strip()

    def free_write(self, prompt: str, paragraphs: int = 2) -> str:
        """根据提示自由创作若干段文本。"""
        system = (
            "你是一名中文小说作者，擅长人物内心和细节描写。"
            "写作风格可以偏文学，但必须清晰、可读，不要解释自己的写作意图。"
        )
        user = (
            f"请根据下面的提示写一个短篇片段，大约 {paragraphs} 段自然段：\n\n"
            f"【创作提示】\n{prompt}\n\n"
            "不要写分析、不要写提纲，直接给出完整小说片段。"
        )
        return self._chat(system, user, temperature=0.9)

    def collect_text(
        self,
        document_title: str,
        chapter_title: str,
        content: str,
        chunk_size: int = 1200,
        path: str | None = None,
    ) -> Tuple[int, int, int]:
        return self.repo.add_chapter(document_title, chapter_title, content, chunk_size, path)

    def generate_character_cards(self, document_title: str) -> List[CharacterCard]:
        chapters = list(self.repo.iter_chapters(document_title))
        return build_character_cards(chapters)

    def review_chapter(self, document_title: str, chapter_text: str) -> list[str]:
        """对章节进行编辑式审阅，给出具体修改建议。"""
        system = (
            "你是一名严格但真诚的中文小说编辑，会从结构、节奏、人物塑造、语言风格几个方面给出具体建议。"
            "请注意：不要空洞夸赞，要指出可以修改的地方，并给出简短示例或替代思路。"
        )
        user = (
            f"作品标题：{document_title}\n\n"
            f"下面是一段章节内容，请你进行审阅：\n"
            f"{chapter_text}\n\n"
            "请分条给出建议，每条一行，前面可以带【结构】【节奏】【人物】【语言】【世界观】等标签。"
        )
        text = self._chat(system, user, temperature=0.6)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return lines

    def inspire(self, document_title: str, hint: str) -> list[str]:
        """围绕作品标题和提示词，生成几条不同方向的情节灵感。"""
        system = (
            "你是一名资深小说策划编辑，擅长给出简洁有力的剧情方向和桥段点子。"
            "回答时使用条目形式，每条是一句话，不要写长篇大论。"
        )
        user = (
            f"作品标题：{document_title}\n"
            f"灵感提示词：{hint}\n\n"
            "请给出 3~5 条不同方向的剧情灵感，每条一行："
            "可以是冲突设定、角色抉择、场景设计或叙事结构上的点子。"
        )
        text = self._chat(system, user, temperature=0.85)
        lines = [line.strip(" \n-•\t") for line in text.splitlines() if line.strip()]
        return lines
