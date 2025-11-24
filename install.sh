#!/usr/bin/env bash
# 安装简易版 AInovelAssist：创建虚拟环境并生成可执行脚本
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
BIN_DIR="$ROOT_DIR/bin"
LAUNCHER="$BIN_DIR/ainovelassist"

if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ 未找到 python3，请先安装 Python 3.11+。"
  exit 1
fi

python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r "$ROOT_DIR/requirements.txt"

mkdir -p "$BIN_DIR"
cat > "$LAUNCHER" <<'EOF'
#!/usr/bin/env bash
DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "$DIR/.venv/bin/activate"
python "$DIR/scripts/app.py" "$@"
EOF
chmod +x "$LAUNCHER"

echo "安装完成！使用 $LAUNCHER 运行示例："
echo "  $LAUNCHER demo"
