# -*- coding: utf-8 -*-
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.assistant import NovelAssistant, build_character_cards, free_write
from scripts.init_db import init_db


def test_free_write_produces_prompt_and_is_deterministic():
    text = free_write("写段小说来看看吧？", paragraphs=2, seed=7)
    lines = text.split("\n\n")
    assert len(lines) == 2
    assert "写段小说" in text
    again = free_write("写段小说来看看吧？", paragraphs=2, seed=7)
    assert text == again  # deterministic with the same seed


def test_collect_and_character_cards(tmp_path: Path):
    db_path = tmp_path / "novel.db"
    init_db(str(db_path))
    assistant = NovelAssistant(db_path=str(db_path))

    assistant.collect_text(
        document_title="边城纪事",
        chapter_title="第1章",
        content="阿黎在码头等船，阿黎记下了陌生人的口令。",
    )
    assistant.collect_text(
        document_title="边城纪事",
        chapter_title="第2章",
        content="陌生人告诉阿黎要去北方。柳青在暗处观察。",
    )

    cards = assistant.generate_character_cards("边城纪事")
    names = [card.name for card in cards]
    assert "阿黎" in names
    assert any("第1章" in card.timeline for card in cards)

    # build_character_cards should mirror the helper output
    flattened = list(assistant.repo.iter_chapters("边城纪事"))
    direct_cards = build_character_cards(flattened)
    assert direct_cards[0].name == cards[0].name


def test_review_and_inspire(tmp_path: Path):
    db_path = tmp_path / "novel.db"
    assistant = NovelAssistant(db_path=str(db_path))
    assistant.collect_text(
        document_title="灵感测试",
        chapter_title="序章",
        content="苏澜带着罗盘进入废墟。苏澜记得导师的叮嘱。",
    )

    review = assistant.review_chapter(
        document_title="灵感测试",
        new_text="废墟深处出现新的侍者，脚步声骤然靠近。",
        outline="主角需要发现一件遗物",
    )
    assert any("主要角色缺席" in r for r in review)
    assert any("新增角色" in r for r in review)

    hooks = assistant.inspire(document_title="灵感测试", hint="钟声")
    assert any("钟声" in h for h in hooks)
    assert hooks  # not empty
