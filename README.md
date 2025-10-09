
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
| 单元测试 | `pytest` 覆盖文本清洗、编码识别、docx读取 | ✅ 已完成 |
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

### 4️⃣ 运行测试

```bash
pytest -q
```

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
