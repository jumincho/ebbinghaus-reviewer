<div align="center">

# 🧠 Ebbinghaus Reviewer

**沿艾宾浩斯遗忘曲线的 SM-2 间隔重复学习工具（命令行 + 网页）**
**Spaced-repetition study tool along the Ebbinghaus forgetting curve (SM-2)**

![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-72%20passing-brightgreen)
![Algorithm](https://img.shields.io/badge/algorithm-SM--2-512BD4)
![Year](https://img.shields.io/badge/since-2021-blue)

[한국어](./README.md) · [English](./README.md#english) · **中文**

</div>

---

## 概述

**Ebbinghaus Reviewer** 是一个间隔重复（spaced repetition）学习工具，帮助你沿着**艾宾浩斯遗忘曲线**
复习学习内容。你录入学习条目（卡片），**SM-2 算法**会计算每张卡片下次复习的时间；你对回忆程度
打 0~5 分后，复习计划会自动调整。

本仓库是一个 **用 Python 重新实现的「净室」（clean-room）版本**，与 2021 年在全北大学（JBNU）项目中
开发的 Windows WPF/C# 应用同源、同思路。原始 WPF 源码出于诚实的来源保存，存放于
[`archive/`](./archive)（见下文 [归档](#归档原始-2021-wpf-应用)）。

## 遗忘曲线与 SM-2

德国心理学家赫尔曼·艾宾浩斯（Hermann Ebbinghaus）发现：学习之后记忆会迅速衰退，但在恰当的时间
复习能让遗忘曲线变得平缓，从而把内容转入长期记忆。

**SM-2**（SuperMemo，Woźniak 1990）把这一原理变成了算法。每张卡片保存三个数值——重复次数
`repetitions`、难度系数 `ease factor`、复习间隔 `interval`（天）——每次复习时：

- **回忆成功（质量 ≥ 3）**：增加重复次数并拉长间隔：`1 天 → 6 天 → round(上次间隔 × EF)`。
- **回忆失败（质量 < 3）**：重置重复次数与间隔，使卡片次日再次到期（难度系数保持不变）。

难度系数不会低于 1.3。完整说明与数值示例见 [`docs/algorithm.md`](./docs/algorithm.md)。

## 快速开始

```bash
# 安装（开发模式）
pip install -e .

# 添加卡片
ebbinghaus add "什么是艾宾浩斯遗忘曲线？" --back "记忆随时间衰退的曲线"

# 查看今天要复习的条目
ebbinghaus today

# 复习（先回忆，再给自己打 0~5 分）
ebbinghaus review

# 统计
ebbinghaus stats
```

命令列表：

| 命令 | 说明 |
| --- | --- |
| `ebbinghaus add FRONT [--back ...]` | 添加学习卡片 |
| `ebbinghaus list` | 列出所有卡片及其计划 |
| `ebbinghaus today` | 今天（或已逾期）的复习条目 |
| `ebbinghaus review [--id N]` | 交互式复习 + 打分 |
| `ebbinghaus stats` | 集合统计 |
| `ebbinghaus delete ID` | 删除卡片 |

每个命令都可用 `--help` 查看详细帮助。数据库路径可通过 `--db` 选项或 `EBBINGHAUS_DB` 环境变量
设置（默认：`~/.local/share/ebbinghaus-reviewer/reviews.db`）。

## 演示

```text
$ ebbinghaus add "SM-2 ease-factor floor?" --back "1.3"
Added item #1: SM-2 ease-factor floor? (due 2026-05-29)

$ ebbinghaus today
                             Due today (2)
┏━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━┳━━━━━━┳━━━━━━━━━━┓
┃ ID ┃ Front              ┃ Back   ┃    Due     ┃ Reps ┃   EF ┃ Interval ┃
┡━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━╇━━━━━━╇━━━━━━━━━━┩
│  1 │ SM-2 ease-factor   │ 1.3    │ 2026-05-29 │    0 │ 2.50 │       0d │
│    │ floor?             │        │            │      │      │          │
│  2 │ Interval after 2nd │ 6 days │ 2026-05-29 │    0 │ 2.50 │       0d │
│    │ success?           │        │            │      │      │          │
└────┴────────────────────┴────────┴────────────┴──────┴──────┴──────────┘

$ ebbinghaus stats
           Statistics
┌─────────────────────────┬──────┐
│ Total items             │    2 │
│ Due today               │    2 │
│ Learning (<2 reps)      │    2 │
│ Mature (>=21d interval) │    0 │
│ Average ease factor     │ 2.50 │
└─────────────────────────┴──────┘
```

## 网页界面（可选）

内置一个轻量的 FastAPI + Jinja2 服务，与命令行**共享同一个 SQLite 文件**。

```bash
pip install -e ".[web]"
uvicorn ebbinghaus_reviewer.web:create_app --factory --reload
# 访问 http://127.0.0.1:8000 —— 仪表盘 / 卡片 / 复习 / 健康检查（/healthz）
```

网页层采用延迟导入（import-lazy），因此核心代码与测试无需安装 FastAPI 即可运行。

## 项目结构

```
ebbinghaus-reviewer/
├── src/ebbinghaus_reviewer/
│   ├── algorithm.py     # 纯 SM-2（无 I/O）
│   ├── storage.py       # SQLite 存储库（路径可注入）
│   ├── scheduler.py     # 连接算法 + 存储（用例层）
│   ├── cli.py           # click + rich 命令行
│   └── web/             # FastAPI + Jinja2（可选）
├── tests/               # pytest（algorithm/storage/scheduler/cli/web）
├── docs/
│   ├── algorithm.md     # SM-2 说明 + 数值示例
│   └── architecture.md  # 分层 / 数据模型
├── archive/             # 原始 2021 WPF/C# 源码（诚实保存来源）
├── pyproject.toml
├── README.md · README.zh-CN.md
└── LICENSE
```

分层与数据模型见 [`docs/architecture.md`](./docs/architecture.md)。

## 开发

```bash
pip install -e ".[dev,web]"
pytest          # 72 个测试
ruff check .    # 代码检查
mypy src        # 类型检查
```

## 归档：原始 2021 WPF 应用

[`archive/`](./archive) 保存了本项目最初的 **Windows WPF / C#** 桌面应用源码。该应用仅支持
Windows，并依赖商业的 Syncfusion WPF 许可证，因此无法在当前环境中构建或运行；无法运行的二进制
产物已被删除，仅诚实地保留了源码。详情见 [`archive/README.md`](./archive/README.md)。

- 演示视频（原始 WPF 应用）：<https://www.youtube.com/watch?v=J2nf1r5jZrI>
- 演示幻灯片：[`archive/docs/presentation.pdf`](./archive/docs/presentation.pdf)

## 许可证

[MIT License](./LICENSE)。
