from scripts.exe_builder import generate_pyinstaller_command


def test_generate_pyinstaller_command_defaults():
    cmd = generate_pyinstaller_command("scripts/gui_app.py")
    assert cmd[:5] == ["pyinstaller", "--noconfirm", "--clean", "--name", "AInovelAssist"]
    assert "--onefile" in cmd
    assert cmd[-1] == "scripts/gui_app.py"


def test_generate_pyinstaller_command_customization():
    cmd = generate_pyinstaller_command(
        "main.py", name="StoryTool", onefile=False, icon="icon.ico", add_data=[("a.txt", "b")]
    )
    assert "--onefile" not in cmd
    assert "--icon" in cmd and "icon.ico" in cmd
    assert any(item.startswith("--add-data") or item.startswith("a.txt") for item in cmd)
    assert cmd[-1] == "main.py"
