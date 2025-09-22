# AInovelAssist

一个 **AI 小说辅助写作 Demo** 项目。  
目标是探索如何用 Python + 数据库 + LLM 构建一个能处理 **百万字长文本** 的小说写作助手。  

---

## ✨ 功能概览

当前：
- ✅ 数据库初始化（`documents / chapters / chunks` 三张表）
- ✅ GitHub 仓库搭建，配置 `.gitignore`
- 🚧 章节文本清洗函数（开发中）
	
	目前已完成ingest.py函数，用以清洗UTF-8编码模式的纯文本内容，清洗包括：
		
		- 归一化换行
		- 去除常见页眉/页脚/页码
		- 合并多余空行（最多保留 1 行）
		- 去除行首/尾多余空格
	但达不成预期效果，仍在尝试中······

- 计划：
- ⏳ 长文本导入与分块存储
- ⏳ 支持文本检索与上下文关联
- ⏳ 角色卡片生成与推演
- ⏳ 内容审校（错字、逻辑一致性）
- ⏳ 大纲与内容的双向调整

---

## 📂 项目结构
```text
AInovelAssist/
├── data/              # 数据文件（未纳入版本控制）
├── scripts/           # 脚本
│   ├── init_db.py     # 初始化数据库
│   └── ingest.py      # 文本导入（开发中）
├── .gitignore
└── README.md
```

---

## 🚀 快速开始
1. 克隆仓库
```
1. git clone git@github.com:Star-Winds/AInovelAssist.git
cd AInovelAssist
```

2. 创建并激活虚拟环境
```
1. python -m venv .venv


# Windows
	.venv\Scripts\activate


# macOS / Linux
	source .venv/bin/activate
```

3. 安装依赖

```
（未来会提供 requirements.txt）
pip install -r requirements.txt
```
4. 初始化数据库
```
1. python scripts/init_db.py
```

---

## 🛣️ Roadmap

 文本导入与清洗

 分块存储与检索

 角色卡片生成

 内容审校

 大纲与内容的双向调整
 
 ---

## 🎯 学习目标

本项目同时用于：

系统性学习 Python 脚本编写习惯

理解数据库操作与基本原理

掌握 Git/GitHub 的使用（版本管理、协作与展示）

---

## 📜 License

MIT License