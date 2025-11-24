# -*- coding: utf-8 -*-
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.repository import StoryRepository
from scripts.vector_store import VectorStore


def test_index_and_search(tmp_path: Path):
    db_path = tmp_path / "novel.db"
    repo = StoryRepository(db_path=str(db_path))
    repo.add_chapter(
        document_title="向量测试",
        chapter_title="第1章",
        raw_text="阿黎在码头等船，听见海雾里的汽笛。",
        chunk_size=16,
    )
    repo.add_chapter(
        document_title="向量测试",
        chapter_title="第2章",
        raw_text="柳青在北方的站台写信，车站广播回响。",
        chunk_size=16,
    )

    store = VectorStore(db_path=str(db_path))
    count = store.index_document("向量测试", dim=64)
    assert count >= 2  # chunks generated from both chapters

    hits = store.similarity_search("码头的汽笛声", top_k=2, dim=64)
    assert hits
    assert any("码头" in hit.text for hit in hits)

    payload = store.dump_for_api("写信", top_k=1)
    assert payload["context"][0]["text"]
    assert payload["query"] == "写信"
