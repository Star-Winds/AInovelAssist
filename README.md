
---

```markdown
# 🧠 AI小说助手 AInovelAssist

一个基于 Python 的 AI 小说辅助项目，目标是实现**文本清洗、分章入库、分块检索**，为后续 AI 创作与语义分析打基础。

---

## 🚀 当前进度

| 模块 | 功能 | 状态 |
|------|------|------|
| 环境搭建 | 使用 Python 3.13 + venv 虚拟环境 | ✅ 已完成 |
| 数据库结构 | SQLite (`documents`, `chapters`, `chunks`) | ✅ 已完成 |
| 文本清洗 | 自动换行归一化、空行压缩 | ✅ 已完成 |
| 自动编码识别 | 支持 UTF-8 / GBK / DOCX 自动识别 | ✅ 已完成 |
| 入库逻辑 | 支持命令行参数 `--to-db`、`--chunk-size` 分块存储 | ✅ 已完成 |
| AI 小说助手 | 新增自由创作、文本收纳、人物卡片、章节审阅与灵感提示 | ✅ 已完成 |
| 单元测试 | `pytest` 覆盖文本清洗、编码识别、docx读取、助手功能 | ✅ 已完成 |
| 向量数据库 | 基于 TF-IDF 的中文 2-4gram 向量库，支持相似段落检索 | ✅ 已完成 |
| 全文检索 | （下一阶段：FTS5 实现全文搜索） | 🔜 规划中 |

---

## 🧩 项目结构

```

AInovelAssist/
│
├── data/                  # 数据文件夹
│   ├── novel.db           # 本地 SQLite 数据库（自动生成）
│   ├── utf8.txt           # 测试文本（UTF8）
│   ├── gbk.txt            # 测试文本（GBK）
│   └── sample.docx        # 测试 Word 文件
│
├── scripts/
│   ├── ingest.py          # 核心：读取、清洗、分块、入库
│   └── init_db.py         # 初始化数据库表结构
│
├── tests/
│   └── test_ingest.py     # pytest 测试脚本
│
├── requirements.txt       # 项目依赖
└── README.md              # 项目说明

````

---

## ⚙️ 使用方法

### 🌐 GitHub Pages 前端展示

仓库内新增 `docs/index.html`，可直接在 GitHub Pages 上以静态方式演示“自由创作 / 文本收纳 / 人物卡片 / 审稿与灵感激发”等流程。启用步骤：

1. 推送最新代码到主分支。
2. 仓库 → **Settings** → **Pages**，选择 **Deploy from a branch**。
3. Branch 选择 `main`，目录选择 `/docs`，保存后稍等即可在公开链接访问演示页。

> 演示页为纯前端静态示例，真实效果请在本地运行 Python 脚本。

### 1️⃣ 初始化数据库
```bash
python scripts/init_db.py
````

### 2️⃣ 读取并清洗文本

```bash
python scripts/ingest.py data/utf8.txt --print
```

### 3️⃣ 清洗并入库（自动分块）

```bash
python scripts/ingest.py data/utf8.txt \
    --to-db \
    --doc-title "测试长文" \
    --chapter "第1章" \
    --chunk-size 1200
```

输出示例：

```
🗂 已入库 → document_id=1, chapter_id=1, chunks=1, db=data/novel.db
```

### 4️⃣ 构建向量数据库并相似检索

基于 SQLite 中的 `chunks` 表自动生成 TF-IDF 向量索引，便于粗粒度语义检索：

```bash
# 从已入库的 chunks 重建向量索引
python scripts/vector_db.py --rebuild

# 查询相似段落（top5），默认索引路径 data/vector_store.joblib
python scripts/vector_db.py "徽章 北方" --topk 5
```

输出示例：

```
🔧 正在重建向量索引…
✅ 已保存到 data/vector_store.joblib
[score=0.742] 边城纪事 / 第1章 (chunk#1) -> 阿黎在码头等船，陌生人递给她一枚徽章。
...（其余结果略）
```

### 5️⃣ AI 小说助手模式

无需大纲即可试写、收纳章节并获得人物卡片与审稿提示：

```bash
python - <<'PY'
from scripts.assistant import NovelAssistant

assistant = NovelAssistant()

# 自由创作模式：给出一句 prompt 生成两段草稿
print(assistant.free_write("写段小说来看看吧？", paragraphs=2))

# 文本收纳：将章节存入数据库（自动分块）
assistant.collect_text("边城纪事", "第1章", "阿黎在码头等船，阿黎记下了陌生人的口令。")

# 人物管理：生成人物卡片
for card in assistant.generate_character_cards("边城纪事"):
    print(card)

# 核心编辑：对新章节给出审稿建议
comments = assistant.review_chapter("边城纪事", "陌生人告诉阿黎要去北方。柳青在暗处观察。")
print("\n".join(comments))

# 灵感激发：在卡文时给出续写角度
print(assistant.inspire("边城纪事", hint="雨夜"))
PY
```

### 6️⃣ 运行测试

```bash
pytest -q
```

### 7️⃣ 简易 CLI 应用 + 安装/卸载

> 想快速体验完整流程（入库 → 向量检索 → 灵感提示），可以使用随仓库提供的简易 CLI。

```bash
# 安装：创建 .venv、安装依赖并生成 ./bin/ainovelassist
bash install.sh

# 运行内置示例（自动写入 demo 章节、重建向量索引并展示结果）
./bin/ainovelassist demo

# 常用子命令
./bin/ainovelassist free-write "写段小说来看看吧？" --paragraphs 1
./bin/ainovelassist collect "边城纪事" "第2章" "陌生人让阿黎前往灯塔。" --chunk-size 400
./bin/ainovelassist rebuild
./bin/ainovelassist search "徽章 北方" --topk 3
./bin/ainovelassist inspire "边城纪事" --hint "雨夜"

# 卸载：删除虚拟环境与启动脚本
bash uninstall.sh
```


### 8️⃣ GUI & EXE 打包

* 直接运行 Tkinter 窗口体验常用功能：

```bash
python scripts/gui_app.py
```

* Windows 下可用 PyInstaller 打包单文件 exe（需先 `pip install pyinstaller`）：

```bash
python scripts/exe_builder.py --entry scripts/gui_app.py --name AInovelAssistGUI
```

生成的可执行文件位于 `dist/` 目录，可在无 Python 环境的机器上运行，提供 demo、自由创作、收纳、向量检索、灵感提示等简易交互。



---

## 🧰 依赖环境

在虚拟环境中安装依赖：

```bash
pip install -r requirements.txt
```

当前 `requirements.txt` 包含：

```
charset-normalizer==3.4.0
python-docx==1.1.2
pytest==8.3.3
```

---

## 🔮 下一步规划

* [ ] 增加 `scripts/search.py`，基于 SQLite FTS5 实现全文检索
* [ ] 设计角色卡片与小说知识库表
* [ ] 实现前端交互 Demo（Flask / Streamlit）
* [ ] 支持网页文本爬取与自动入库

---

## ✨ 作者目标

> 本项目主要用于学习和搭建 AI 小说工作流，目标是在理解每一行代码逻辑的基础上，逐步完成自动化文本处理与语义检索系统。

---

*更新日期：2025-10-09*

````

---

## 📘 提交方式

在 PowerShell 中执行：
```powershell
git add README.md
git commit -m "更新 README，整理项目阶段成果与使用说明"
git push origin main
````

---
