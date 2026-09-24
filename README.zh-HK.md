<div align="center">

🇺🇸 [English](README.md) | 🇨🇳 [简体中文](README.zh-CN.md) | 🇭🇰 **繁體中文** | 🇯🇵 [日本語](README.ja.md) | 🇰🇷 [한국어](README.ko.md)

<img src="src/ebbinghaus_reviewer/web/static/icon.svg" width="64" height="64" alt="">

# Ebbinghaus Reviewer

**沿着遺忘曲線溫習所學：間隔重複命令列工具及本機網頁應用程式。**

[![CI](https://github.com/jumincho/ebbinghaus-reviewer/actions/workflows/ci.yml/badge.svg)](https://github.com/jumincho/ebbinghaus-reviewer/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%E2%80%933.14-3776AB?logo=python&logoColor=white)
![Typed](https://img.shields.io/badge/typing-mypy%20strict-2A6DB2)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

<img src="docs/screenshots/today.png" width="49%" alt="今日（Today）頁面：統計數據及待溫習的條目">
<img src="docs/screenshots/review.png" width="49%" alt="深色模式下的溫習（Review）頁面，附有四個評分按鈕">

</div>

## 概覽

剛學完一樣東西，就立即把它記錄下來。Ebbinghaus Reviewer 會在你快要忘記的時候，再把它拿出來讓你溫習：先在 **10 分鐘**後，然後是 **1 日**、**1 星期**及 **1 個月**後。它亦會告訴你每日有哪些內容到期。每次溫習後，從「重來」（*again*）、「困難」（*hard*）、「良好」（*good*）及「簡單」（*easy*）中選擇一個評分，排程便會隨之調整。

## 功能

- **兩種排程策略。** 每個條目都可選用固定的 *Ebbinghaus 階梯*（10 分鐘 → 1 日 → 1 星期 → 1 個月，之後即視為已掌握）或自適應的 *SM-2*。
- **終端機工作流程。** 提供 `add`、`due`、互動式的 `review`、`agenda`、`stats`、`show`、`edit`、`restart` 等指令，並以易讀的表格顯示結果。
- **本機網頁應用程式。** 設有儀表板、在你嘗試回想之前會隱藏筆記的溫習介面、附有溫習紀錄及遺忘曲線圖表的條目頁面，以及日程表。毋須 JavaScript 亦能運作，並支援深色模式。
- **溫習日誌。** 每次溫習都會連同評分記錄下來，並註明是提早還是逾期完成；連續溫習日數及 30 日回想率均據此計算。
- **本機優先。** 你的所有數據都儲存在用戶數據目錄中的一個 SQLite 檔案內，並支援附有版本號的 JSON 匯出／匯入，方便備份或轉用另一部電腦。
- **為長遠維護而打造。** 排程規則均為純函數，並經過基於屬性的測試。數據庫 schema 設有版本號並透過遷移升級，類型註解通過 mypy 嚴格模式檢查，CI 涵蓋 Python 3.10–3.14。

## 快速開始

```bash
pip install "ebbinghaus-reviewer[web] @ git+https://github.com/jumincho/ebbinghaus-reviewer"

ebbinghaus demo      # 可選：載入範例集合，先試用一下
ebbinghaus due       # 現在要溫習甚麼？
ebbinghaus review    # 開始溫習
ebbinghaus serve     # 網頁應用程式：http://127.0.0.1:8000
```

如只需要命令列，可略去 `[web]`。`demo` 指令只能在空集合上執行；加上 `--db demo.sqlite3` 便可在另一個檔案中試用。

## 命令列

在範例集合上的一次操作：

```text
$ ebbinghaus add "Pythagorean theorem" --notes "a² + b² = c²" --subject Math
Added #9 Pythagorean theorem - first review in 10 min.

$ ebbinghaus due
Due now (3)
┏━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ ID ┃ Item                                       ┃ Schedule   ┃ Next review ┃ Recall* ┃
┡━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━┩
│  2 │ Krebs cycle: the eight intermediates in    │ ladder 3/4 │ 1 day ago   │     89% │
│    │ order  Biology                             │            │             │         │
│  3 │ Binary heap: cost of push and pop          │ SM-2 rep 2 │ 2 h ago     │     90% │
│    │ Algorithms                                 │            │             │         │
│  7 │ Korean spelling: 되 vs 돼  Korean          │ ladder 2/4 │ 50 min ago  │     90% │
└────┴────────────────────────────────────────────┴────────────┴─────────────┴─────────┘
*estimated probability of recall right now

$ ebbinghaus review --limit 1
1 to review. Grades: [a]gain  [h]ard  [g]ood  [e]asy; [s]kip, [q]uit.
╭──────────────────────────────────── #2 · Biology ────────────────────────────────────╮
│ Krebs cycle: the eight intermediates in order                                        │
╰───────────────────── 1/1 · ladder · step 3 of 4 · due 1 day ago ─────────────────────╯
Recall it, then press Enter to see your notes:
╭─────────────────────────────────────── Notes ────────────────────────────────────────╮
│ Citrate, isocitrate, alpha-ketoglutarate, succinyl-CoA, succinate, fumarate, malate, │
│ oxaloacetate.                                                                        │
╰──────────────────────────────────────────────────────────────────────────────────────╯
Grade: g
good - next review in 1 month (Fri 23 Oct 16:49).
Reviewed 1 item.

$ ebbinghaus agenda --days 7
Today 2026-09-23
  overdue  #3 Binary heap: cost of push and pop Algorithms
  overdue  #7 Korean spelling: 되 vs 돼 Korean
    16:54  #8 French: 'être' in the passé simple French
    16:59  #9 Pythagorean theorem Math
Friday 2026-09-25
    16:49  #5 Treaty of Westphalia History
...
```

| 指令 | 用途 |
| --- | --- |
| `ebbinghaus add TITLE [-n NOTES] [-s SUBJECT] [--strategy ladder\|sm2] [--studied WHEN]` | 記錄學過的內容（可用 `--studied "2h ago"` 補記較早前的學習）。 |
| `ebbinghaus due [-s SUBJECT] [--limit N]` | 列出現時到期的條目，逾期最久的排在最前。 |
| `ebbinghaus review [ID] [-s SUBJECT] [--limit N]` | 逐一溫習到期條目，每項以 a / h / g / e 評分。 |
| `ebbinghaus grade ID {again,hard,good,easy}` | 毋須經過互動提示，直接記錄一次溫習。 |
| `ebbinghaus list [-s SUBJECT] [--active]` | 列出所有條目及其排程。 |
| `ebbinghaus show ID` | 顯示單一條目及其完整溫習紀錄。 |
| `ebbinghaus agenda [--days N]` | 按日列出即將進行的溫習。 |
| `ebbinghaus stats` | 顯示總數、到期數量、連續溫習日數及 30 日回想率。 |
| `ebbinghaus edit ID [--title] [--notes] [--subject \| --clear-subject]` | 修改條目的文字；排程維持不變。 |
| `ebbinghaus restart ID [--strategy ...]` | 讓條目的排程從頭開始，並可同時切換策略。 |
| `ebbinghaus delete ID [-y]` | 刪除條目及其紀錄。 |
| `ebbinghaus export [-o FILE]` / `ebbinghaus import FILE` | 以 JSON 格式備份或還原集合。 |
| `ebbinghaus demo` | 把範例集合載入空的數據庫。 |
| `ebbinghaus serve [--host] [--port]` | 執行網頁應用程式（需要 `web` 可選依賴）。 |

每個指令都有 `--help`。集合儲存在你所用平台的用戶數據目錄中（例如 Linux 上的 `~/.local/share/ebbinghaus-reviewer/`）；如要使用多個集合，可透過 `--db` 或 `EBBINGHAUS_DB` 環境變數指向另一個檔案。

## 網頁應用程式

`ebbinghaus serve` 會啟動一個本機網頁應用程式，與命令列共用同一個 SQLite 檔案，因此你可以在終端機記錄、在瀏覽器溫習。頁面包括：**今日**（*Today*），顯示統計數據及到期條目，並可快速新增；**溫習**（*Review*），每次顯示一張卡片，筆記在你打開之前會一直隱藏；**條目**（*Items*），可按科目篩選；**條目頁面**，包括排程、紀錄、編輯及重新開始；還有**日程表**（*Agenda*）。

<p align="center">
  <img src="docs/screenshots/item.png" width="80%" alt="條目頁面，顯示排程資料及遺忘曲線圖表">
</p>

此應用程式是為你自己的電腦而設。它監聽 `127.0.0.1`，亦沒有帳戶系統，所以切勿把它暴露在你不信任的網絡上。

## 排程運作方式

```text
ladder:  studied ─10 min─▶ ✓ ─1 day─▶ ✓ ─1 week─▶ ✓ ─1 month─▶ ✓ ─▶ mastered
```

| 評分 | 階梯 | SM-2 |
| --- | --- | --- |
| 重來（*again*） | 返回第一級 | 以 1 日的間隔重新開始，容易度因子（ease factor）維持不變 |
| 困難（*hard*） | 重複目前這一級 | 通過；容易度因子 −0.14 |
| 良好（*good*） | 上升一級 | 通過；容易度因子不變 |
| 簡單（*easy*） | 上升兩級 | 通過；容易度因子 +0.10 |

SM-2 的間隔依次為 1 日、6 日，其後為上一次的間隔 × 容易度因子，並向上取整。回想機率的估算假設遺忘曲線呈指數形式，並在條目到期時剛好降至 90%。[`docs/algorithm.md`](docs/algorithm.md) 載有完整規則、一個計算示例及參考文獻，[`docs/architecture.md`](docs/architecture.md) 則說明分層結構、數據模型及時間處理。

## 項目結構

```text
ebbinghaus-reviewer/
├── src/ebbinghaus_reviewer/
│   ├── scheduling.py     # 評分、階梯及 SM-2 策略（純函數）
│   ├── retention.py      # 遺忘曲線估算
│   ├── models.py         # Item, Review, Stats, AgendaDay
│   ├── storage.py        # SQLite 儲存庫，支援 schema 遷移
│   ├── service.py        # Reviewer：CLI 與網頁版共用的使用案例
│   ├── transfer.py       # 附版本號的 JSON 匯出／匯入
│   ├── presentation.py   # 共用的顯示標籤
│   ├── cli.py            # `ebbinghaus` 指令
│   ├── demo.py           # 範例集合
│   └── web/              # FastAPI 應用程式、Jinja2 模板、CSS
├── tests/                # pytest + Hypothesis，每層一個模組
├── docs/                 # 演算法、架構、截圖、簡報投影片
└── pyproject.toml
```

## 開發

```bash
git clone https://github.com/jumincho/ebbinghaus-reviewer
cd ebbinghaus-reviewer
python -m pip install -e ".[web]" --group dev   # 需要 pip >= 25.1（支援依賴組）

pytest --cov        # 測試
ruff check .        # 程式碼檢查
ruff format .       # 格式化
mypy                # 嚴格類型檢查
```

## 授權條款

[MIT](LICENSE) © 2021 jumincho
