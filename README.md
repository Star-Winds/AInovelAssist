# 🧠 AInovelAssist · AI 小说助手

> 更新日期：2025.11.26

AInovelAssist 是一个面向中文网文的轻量级创作助手，核心能力包括：

- **文本清洗与入库**：自动检测 UTF-8/GBK/DOCX 编码，统一换行与空行压缩后写入 SQLite，按「文档-章节-分块」结构存储。
- **分块检索**：基于纯 Python 的 2–4 字符 n-gram TF-IDF 向量库，支持相似段落检索与预览。
- **创作辅助**：提供自由创作草稿、章节收纳、人物卡片、审稿建议与灵感提示等高阶功能。
- **多种入口**：命令行脚本、简易 GUI（Dear PyGui）以及静态演示页（`docs/index.html`）。

---

## 🛠 技术栈
- Python 3.13
- SQLite（`documents` / `chapters` / `chunks` 三表结构）
- 纯 Python TF-IDF（无需分词，内置持久化索引）
- OpenAI SDK 连接硅基流动模型（需环境变量 `SILICONFLOW_API_KEY`）
- Dear PyGui 轻量桌面界面

---

## 🗂 目录速览
```
AInovelAssist/
├── data/                 # 示例数据与本地数据库（运行后生成 novel.db）
├── scripts/              # 核心脚本：ingest、assistant、vector_db、gui_app、search 等
├── docs/index.html       # GitHub Pages 静态演示页
├── tests/test_ingest.py  # 文本清洗与编码识别单测
├── install.sh|.ps1       # 安装脚本，生成命令行启动器
└── requirements.txt      # 运行依赖
```

---

## ⚡ 快速开始
1) **安装依赖**（建议使用虚拟环境）
```bash
pip install -r requirements.txt
```

2) **初始化数据库**
```bash
python scripts/init_db.py
```

3) **清洗并写入示例文本**
```bash
python scripts/ingest.py data/utf8.txt --to-db --doc-title "示例长文" --chapter "第1章" --chunk-size 1200
```

4) **重建向量索引并检索**
```bash
python scripts/vector_db.py --rebuild
python scripts/vector_db.py "徽章 北方" --topk 5
```

5) **体验创作助手 API**（需 `SILICONFLOW_API_KEY`）
```bash
python - <<'PY'
from scripts.assistant import NovelAssistant

assistant = NovelAssistant()
print(assistant.free_write("写段小说来看看吧？", paragraphs=2))
PY
```

6) **命令行封装 / GUI**
- Windows：`powershell -ExecutionPolicy Bypass -File install.ps1` 生成 `bin\ainovelassist.cmd`，支持 `demo`、`free-write`、`collect`、`rebuild`、`search` 等子命令。
- Linux/macOS：`bash install.sh` 生成 `./bin/ainovelassist`，参数与上类似。
- 桌面界面：`python scripts/gui_app.py`，提供基础收纳与检索入口。

7) **运行测试**
```bash
pytest -q
```

---

## 📌 适用场景
- 处理长篇网文草稿的清洗、分章、备份与检索
- 以段落相似度为基础的剧情回溯或伏笔查找
- 在既有章节之上获取灵感、审稿提示与人物卡片

欢迎按需扩展模型接口或替换向量算法，保持最小依赖即可快速落地。
