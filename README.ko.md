<div align="center">

🇺🇸 [English](README.md) | 🇨🇳 [简体中文](README.zh-CN.md) | 🇭🇰 [繁體中文](README.zh-HK.md) | 🇯🇵 [日本語](README.ja.md) | 🇰🇷 **한국어**

<img src="src/ebbinghaus_reviewer/web/static/icon.svg" width="64" height="64" alt="">

# Ebbinghaus Reviewer

**공부한 내용을 망각 곡선에 따라 복습하는 간격 반복 명령줄 도구이자 로컬 웹 앱입니다.**

[![CI](https://github.com/jumincho/ebbinghaus-reviewer/actions/workflows/ci.yml/badge.svg)](https://github.com/jumincho/ebbinghaus-reviewer/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%E2%80%933.14-3776AB?logo=python&logoColor=white)
![Typed](https://img.shields.io/badge/typing-mypy%20strict-2A6DB2)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

<img src="docs/screenshots/today.png" width="49%" alt="오늘(Today) 페이지: 컬렉션 전체의 플럼밥, 통계, 복습할 항목">
<img src="docs/screenshots/review.png" width="49%" alt="항목의 플럼밥과 네 가지 평가 버튼이 있는 다크 모드의 복습(Review) 페이지">

</div>

## 개요

무언가를 공부했다면 바로 기록해 둡니다. Ebbinghaus Reviewer는 그 내용을 막 잊어버리려 할 때쯤 다시 복습하도록 불러옵니다. 처음에는 **10분** 뒤, 그다음에는 **1일**, **1주**, **1개월** 뒤에 복습하게 되며, 날마다 복습할 항목을 알려 줍니다. 복습할 때마다 다시(*again*), 어려움(*hard*), 좋음(*good*), 쉬움(*easy*) 중 하나로 평가하면 일정이 그에 맞게 조정됩니다. 모든 항목에는 심즈(The Sims)식 **플럼밥**이 붙어 있어 상태를 한눈에 보여 줍니다. 기억이 생생할 때는 초록, 복습할 때가 되면 노랑, 기억이 흐려지고 있으면 빨강입니다.

## 기능

- **두 가지 스케줄링 전략.** 고정된 *에빙하우스 사다리*(10분 → 1일 → 1주 → 1개월, 이후 숙달)와 적응형 *SM-2* 중 하나를 항목마다 고를 수 있습니다.
- **항목마다 플럼밥.** 심즈 캐릭터의 기분처럼 항목의 플럼밥도 색과 표정이 바뀝니다. 기억이 생생할 때는 웃는 초록, 복습할 때가 되면 노랑, 기한을 한참 넘겨 기억이 흐려지고 있으면 걱정하는 빨강입니다. 오늘 페이지와 `stats`에서는 컬렉션 전체의 플럼밥을 보여 줍니다.
- **터미널 워크플로.** `add`, `due`, 대화형 `review`, `agenda`, `stats`, `show`, `edit`, `restart` 등의 명령을 쓸 수 있고, 결과는 읽기 쉬운 표로 보여 줍니다.
- **로컬 웹 앱.** 대시보드, 직접 떠올려 보기 전까지 메모를 가려 두는 복습 화면, 복습 기록과 망각 곡선 차트가 있는 항목 페이지, 일정표를 제공합니다. JavaScript 없이도 동작하며 다크 모드를 지원합니다.
- **복습 기록.** 모든 복습은 평가 결과와 함께, 예정보다 일찍 했는지 늦게 했는지도 기록됩니다. 이 기록을 바탕으로 연속 복습 일수와 30일 회상률을 계산합니다.
- **로컬 우선.** 데이터는 사용자 데이터 디렉터리에 있는 SQLite 파일 하나에 모두 저장됩니다. 백업하거나 다른 컴퓨터로 옮길 때는 버전이 지정된 JSON 내보내기/가져오기를 쓸 수 있습니다.
- **오래 쓸 수 있는 설계.** 스케줄링 규칙은 순수 함수이며 속성 기반 테스트로 검증합니다. 스키마는 마이그레이션으로 버전을 관리하고, 타입은 mypy strict 검사를 통과하며, CI는 Python 3.10–3.14를 모두 검사합니다.

## 빠른 시작

```bash
pip install "ebbinghaus-reviewer[web] @ git+https://github.com/jumincho/ebbinghaus-reviewer"

ebbinghaus demo      # 선택 사항: 둘러볼 샘플 컬렉션 불러오기
ebbinghaus due       # 지금 무엇을 복습해야 할까?
ebbinghaus review    # 복습하기
ebbinghaus serve     # 웹 앱: http://127.0.0.1:8000
```

명령줄만 쓰려면 `[web]`을 빼면 됩니다. `demo` 명령은 `--force`를 붙이지 않으면 빈 컬렉션에서만 실행됩니다. 별도 파일에서 시험해 보려면 `--db demo.sqlite3`를 지정하면 됩니다.

## 명령줄

샘플 컬렉션에서 진행한 세션 예시입니다.

```text
$ ebbinghaus add "Pythagorean theorem" --notes "a² + b² = c²" --subject Math
Added #9 Pythagorean theorem - first review in 10 min.

$ ebbinghaus due
Due now (3)
┏━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ ID ┃ Item                                       ┃ Schedule   ┃ Next review ┃ Recall* ┃
┡━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━┩
│  7 │ Korean spelling: 되 vs 돼  Korean          │ ladder 2/4 │ 2 days ago  │   ◆ 73% │
│  2 │ Krebs cycle: the eight intermediates in    │ ladder 3/4 │ 1 day ago   │   ◆ 89% │
│    │ order  Biology                             │            │             │         │
│  3 │ Binary heap: cost of push and pop          │ SM-2 rep 2 │ 2 h ago     │   ◆ 90% │
│    │ Algorithms                                 │            │             │         │
└────┴────────────────────────────────────────────┴────────────┴─────────────┴─────────┘
*estimated probability of recall right now
◆ plumbob: green = fresh, yellow = due, red = fading

$ ebbinghaus review --limit 1
1 to review. Grades: [a]gain  [h]ard  [g]ood  [e]asy; [s]kip, [q]uit.
╭─────────────────────────────────── ◆ #7 · Korean ────────────────────────────────────╮
│ Korean spelling: 되 vs 돼                                                            │
╰──────────────────── 1/1 · ladder · step 2 of 4 · due 2 days ago ─────────────────────╯
Recall it, then press Enter to see your notes:
╭─────────────────────────────────────── Notes ────────────────────────────────────────╮
│ 돼 is the contraction of 되어 - if 되어 fits, write 돼.                              │
╰──────────────────────────────────────────────────────────────────────────────────────╯
Grade: g
good - next review in 1 week (Thu 01 Oct 19:15).
Reviewed 1 item.

$ ebbinghaus agenda --days 7
Today 2026-09-24
  ◆ overdue  #2 Krebs cycle: the eight intermediates in order Biology
  ◆ overdue  #3 Binary heap: cost of push and pop Algorithms
  ◆   19:20  #8 French: 'être' in the passé simple French
  ◆   19:25  #9 Pythagorean theorem Math
Saturday 2026-09-26
  ◆   19:15  #5 Treaty of Westphalia History
...
```

| 명령 | 설명 |
| --- | --- |
| `ebbinghaus add TITLE [-n NOTES] [-s SUBJECT] [--strategy ladder\|sm2] [--studied WHEN]` | 공부한 내용을 기록합니다(지난 학습은 `--studied "2h ago"`처럼 소급해 기록할 수 있습니다). |
| `ebbinghaus due [-s SUBJECT] [--limit N]` | 지금 복습할 항목을 기한이 가장 많이 지난 것부터 보여 줍니다. |
| `ebbinghaus review [ID] [-s SUBJECT] [--limit N]` | 복습할 항목을 하나씩 복습하며, 각 항목을 a / h / g / e로 평가합니다. |
| `ebbinghaus grade ID {again,hard,good,easy}` | 대화형 프롬프트 없이 복습 결과를 기록합니다. |
| `ebbinghaus list [-s SUBJECT] [--active]` | 모든 항목과 각 항목의 일정을 보여 줍니다. |
| `ebbinghaus show ID` | 항목 하나를 전체 복습 기록과 함께 보여 줍니다. |
| `ebbinghaus agenda [--days N]` | 앞으로의 복습을 날짜별로 보여 줍니다. |
| `ebbinghaus stats` | 전체 개수, 복습할 항목 수, 연속 복습 일수, 30일 회상률을 보여 줍니다. |
| `ebbinghaus edit ID [--title] [--notes] [--subject \| --clear-subject]` | 항목의 텍스트를 바꿉니다. 일정은 그대로 유지됩니다. |
| `ebbinghaus restart ID [--strategy ...]` | 항목의 일정을 처음부터 다시 시작하며, 원하면 전략도 바꿀 수 있습니다. |
| `ebbinghaus delete ID [-y]` | 항목과 그 기록을 삭제합니다. |
| `ebbinghaus export [-o FILE]` / `ebbinghaus import FILE` | 컬렉션을 JSON으로 백업하거나 복원합니다. |
| `ebbinghaus demo [--force]` | 샘플 컬렉션을 불러옵니다. `--force`를 붙이면 데이터베이스가 비어 있지 않아도 추가합니다. |
| `ebbinghaus serve [--host] [--port]` | 웹 앱을 실행합니다(`web` extra가 필요합니다). |

모든 명령에는 `--help`가 있습니다. 컬렉션은 플랫폼별 사용자 데이터 디렉터리(예: Linux에서는 `~/.local/share/ebbinghaus-reviewer/`)에 저장됩니다. 여러 컬렉션을 쓰려면 `--db` 옵션이나 `EBBINGHAUS_DB` 환경 변수로 다른 파일을 지정하면 됩니다.

## 웹 앱

`ebbinghaus serve`는 명령줄과 같은 SQLite 파일을 사용하는 로컬 웹 앱을 실행합니다. 그래서 터미널에서 기록하고 브라우저에서 복습할 수 있습니다. 페이지는 컬렉션 전체의 플럼밥과 통계, 복습할 항목을 보여 주고 빠른 추가도 할 수 있는 **오늘**(*Today*), 카드를 한 장씩 보여 주고 메모는 펼치기 전까지 숨겨 두는 **복습**(*Review*), 과목별로 필터링할 수 있는 **항목**(*Items*), 플럼밥·일정·기록·편집·다시 시작을 다루는 **항목 페이지**, 그리고 **일정표**(*Agenda*)로 이루어져 있습니다.

<p align="center">
  <img src="docs/screenshots/item.png" width="80%" alt="플럼밥, 일정 정보, 망각 곡선 차트가 표시된 항목 페이지">
</p>

이 앱은 자신의 컴퓨터에서 쓰도록 만들어졌습니다. `127.0.0.1`에서 수신 대기하고 계정 기능이 없으므로, 신뢰할 수 없는 네트워크에는 노출하지 마십시오.

## 스케줄링 방식

```text
ladder:  studied ─10 min─▶ ✓ ─1 day─▶ ✓ ─1 week─▶ ✓ ─1 month─▶ ✓ ─▶ mastered
```

| 평가 | 사다리 | SM-2 |
| --- | --- | --- |
| 다시(*again*) | 첫 번째 칸으로 돌아감 | 1일 간격으로 다시 시작, 용이도 계수(ease factor)는 유지 |
| 어려움(*hard*) | 현재 칸을 반복 | 통과, 용이도 계수 −0.14 |
| 좋음(*good*) | 한 칸 올라감 | 통과, 용이도 계수 변화 없음 |
| 쉬움(*easy*) | 두 칸 올라감 | 통과, 용이도 계수 +0.10 |

SM-2의 간격은 1일, 6일 순이고, 그다음부터는 이전 간격 × 용이도 계수를 올림한 값입니다. 회상 확률 추정치는 항목의 복습 기한이 되는 순간 정확히 90%에 이르는 지수형 망각 곡선을 가정합니다. 이 추정치가 80% 아래로 떨어지면 플럼밥이 빨강으로 바뀌는데, 보통 기한이 지나고 복습 간격 하나만큼 더 지났을 때입니다. [`docs/algorithm.md`](docs/algorithm.md)에는 전체 규칙과 계산 예시, 참고 문헌이 있고, [`docs/architecture.md`](docs/architecture.md)에서는 계층 구조, 데이터 모델, 시간 처리를 설명합니다.

## 프로젝트 구조

```text
ebbinghaus-reviewer/
├── src/ebbinghaus_reviewer/
│   ├── scheduling.py     # 평가, 사다리 및 SM-2 전략(순수 함수)
│   ├── retention.py      # 망각 곡선 추정
│   ├── plumbob.py        # 심즈식 플럼밥(fresh, due, fading)
│   ├── models.py         # Item, Review, Stats, AgendaDay
│   ├── storage.py        # 스키마 마이그레이션을 지원하는 SQLite 저장소
│   ├── service.py        # Reviewer: CLI와 웹이 함께 쓰는 유스케이스
│   ├── transfer.py       # 버전이 지정된 JSON 내보내기/가져오기
│   ├── presentation.py   # 공용 표시 레이블
│   ├── cli.py            # `ebbinghaus` 명령
│   ├── demo.py           # 샘플 컬렉션
│   └── web/              # FastAPI 앱, Jinja2 템플릿, CSS
├── tests/                # pytest + Hypothesis, 계층마다 모듈 하나
├── docs/                 # 알고리즘, 아키텍처, 스크린샷, 발표 슬라이드
└── pyproject.toml
```

## 개발

```bash
git clone https://github.com/jumincho/ebbinghaus-reviewer
cd ebbinghaus-reviewer
python -m pip install -e ".[web]" --group dev   # pip >= 25.1 필요(의존성 그룹)

pytest --cov        # 테스트
ruff check .        # 린트
ruff format .       # 포맷
mypy                # 엄격한 타입 검사
```

## 라이선스

[MIT](LICENSE) © 2021 jumincho
