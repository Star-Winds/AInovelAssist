#!/usr/bin/env bash
# 卸载简易版 AInovelAssist：移除虚拟环境与启动脚本
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
BIN_DIR="$ROOT_DIR/bin"
LAUNCHER="$BIN_DIR/ainovelassist"

if [ -d "$VENV_DIR" ]; then
  rm -rf "$VENV_DIR"
  echo "已删除虚拟环境 $VENV_DIR"
else
  echo "未找到虚拟环境，跳过。"
fi

if [ -f "$LAUNCHER" ]; then
  rm -f "$LAUNCHER"
  echo "已删除启动脚本 $LAUNCHER"
fi

rmdir "$BIN_DIR" 2>/dev/null || true
