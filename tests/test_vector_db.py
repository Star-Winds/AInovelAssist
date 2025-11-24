# -*- coding: utf-8 -*-
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.assistant import StoryRepository  # noqa: E402
from scripts.init_db import init_db  # noqa: E402
from scripts.vector_db import VectorStore  # noqa: E402


def test_vector_store_rebuild_and_search(tmp_path: Path):
    db_path = tmp_path / "novel.db"
    index_path = tmp_path / "vector_store.joblib"
    init_db(str(db_path))

    repo = StoryRepository(db_path=str(db_path))
    repo.add_chapter("边城纪事", "第1章", "阿黎在码头等船，陌生人递给她一枚徽章。", chunk_size=50)
    repo.add_chapter("边城纪事", "第2章", "阿黎想起导师的叮嘱，徽章上刻着北方的坐标。", chunk_size=50)

    store = VectorStore(db_path=str(db_path), index_path=str(index_path))
    store.rebuild()

    results = store.search("徽章 北方", top_k=2)
    assert results
    assert results[0].document_title == "边城纪事"
    assert all(r.score >= 0 for r in results)
    # ensure formatted lines contain doc/chapter names
    lines = store.as_lines(results)
    assert any("第1章" in line or "第2章" in line for line in lines)
