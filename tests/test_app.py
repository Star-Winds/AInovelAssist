import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.app import build_parser, handle_command, run_demo  # noqa: E402


def test_run_demo_creates_sample_index(tmp_path):
    db_path = tmp_path / "novel.db"
    index_path = tmp_path / "vector.joblib"

    output = run_demo(str(db_path), str(index_path))

    assert "AInovelAssist" in output
    assert index_path.exists()


def test_collect_search_flow(tmp_path):
    db_path = tmp_path / "novel.db"
    index_path = tmp_path / "vector.joblib"

    parser = build_parser()

    collect_args = parser.parse_args(
        [
            "--db",
            str(db_path),
            "--index",
            str(index_path),
            "collect",
            "测试作品",
            "第1章",
            "主角来到灯塔，拾起一枚徽章。",
        ]
    )
    collect_result = handle_command(collect_args)
    assert "document_id" in collect_result

    rebuild_args = parser.parse_args(
        ["--db", str(db_path), "--index", str(index_path), "rebuild", "--silent"]
    )
    handle_command(rebuild_args)

    search_args = parser.parse_args(
        ["--db", str(db_path), "--index", str(index_path), "search", "徽章"]
    )
    search_output = handle_command(search_args)

    assert "测试作品" in search_output
