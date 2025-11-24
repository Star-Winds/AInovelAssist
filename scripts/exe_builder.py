"""Helper to package the CLI/GUI into a Windows-friendly executable.

Typical usage on Windows (after installing pyinstaller):

```
python scripts/exe_builder.py --entry scripts/gui_app.py --name AInovelAssistGUI
```

The script simply constructs the PyInstaller arguments and executes them,
so it can also be imported in tests to validate the generated command.
"""
from __future__ import annotations

import argparse
import os
import subprocess
from typing import Iterable, List, Sequence, Tuple


def generate_pyinstaller_command(
    entry_script: str,
    name: str = "AInovelAssist",
    onefile: bool = True,
    icon: str | None = None,
    add_data: Iterable[Tuple[str, str]] | None = None,
) -> List[str]:
    """Return a PyInstaller CLI argument list without executing it."""
    cmd: List[str] = ["pyinstaller", "--noconfirm", "--clean", "--name", name]
    if onefile:
        cmd.append("--onefile")
    if icon:
        cmd.extend(["--icon", icon])
    for src, dest in add_data or []:
        cmd.extend(["--add-data", f"{src}{os.pathsep}{dest}"])
    cmd.append(entry_script)
    return cmd


def run_pyinstaller(cmd: Sequence[str]) -> int:
    """Execute a PyInstaller command and stream output."""
    proc = subprocess.run(cmd, check=False)
    return proc.returncode


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="构建 AInovelAssist 可执行文件")
    parser.add_argument("--entry", default="scripts/gui_app.py", help="入口脚本")
    parser.add_argument("--name", default="AInovelAssist", help="生成的 exe 名称")
    parser.add_argument("--icon", help="可选图标文件 (.ico)")
    parser.add_argument(
        "--no-onefile",
        dest="onefile",
        action="store_false",
        help="禁用单文件模式 (默认启用)",
    )
    parser.add_argument(
        "--add-data",
        action="append",
        nargs=2,
        metavar=("SRC", "DEST"),
        help="附加数据文件或目录，路径分隔符自动根据平台拼接",
    )
    args = parser.parse_args(argv)

    data_pairs: List[Tuple[str, str]] = args.add_data or []
    cmd = generate_pyinstaller_command(
        entry_script=args.entry,
        name=args.name,
        onefile=args.onefile,
        icon=args.icon,
        add_data=data_pairs,
    )

    print("运行命令:", " ".join(cmd))
    code = run_pyinstaller(cmd)
    if code != 0:
        raise SystemExit(code)


if __name__ == "__main__":
    main()
