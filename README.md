<div align="center">

# 🧠 Ebbinghaus Reviewer

**에빙하우스 망각곡선 · SM-2 간격 반복 학습 도구 (CLI + 웹)**
**Spaced-repetition study tool along the Ebbinghaus forgetting curve (SM-2), with a CLI and web UI**

![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-72%20passing-brightgreen)
![Algorithm](https://img.shields.io/badge/algorithm-SM--2-512BD4)
![Year](https://img.shields.io/badge/since-2021-blue)

**한국어** · [English](#english) · [中文](./README.zh-CN.md)

</div>

---

## 개요

**Ebbinghaus Reviewer** 는 에빙하우스 망각 곡선(Ebbinghaus forgetting curve)에 맞춰 학습 내용을
복습하도록 도와주는 간격 반복(spaced repetition) 학습 도구입니다. 학습 항목(카드)을 등록하면
**SM-2 알고리즘**이 다음 복습 시점을 계산하고, 회상 정도를 0~5점으로 채점하면 일정이 자동으로
조정됩니다.

이 저장소는 2021년 전북대학교(JBNU) 프로젝트로 만든 Windows WPF/C# 앱의 **같은 아이디어를
Python으로 다시 구현한 클린룸(clean-room) 버전**입니다. 원본 WPF 소스는 정직한 출처 보존을 위해
[`archive/`](./archive) 에 보관되어 있습니다(아래 [아카이브](#아카이브-원본-2021-wpf-앱) 참고).

## 망각 곡선과 SM-2

독일의 심리학자 헤르만 에빙하우스는 학습 직후 기억이 빠르게 사라지지만, 적절한 시점에 복습하면
망각 곡선이 완만해져 장기 기억으로 넘어간다는 사실을 보였습니다.

**SM-2**(SuperMemo, Woźniak 1990)는 이 원리를 알고리즘으로 옮긴 것입니다. 각 카드는 세 가지 상태
값(반복 횟수 `repetitions`, 난이도 계수 `ease factor`, 복습 간격 `interval`)을 가지며, 복습할 때마다:

- **회상 성공(품질 ≥ 3)**: 반복 횟수를 늘리고 간격을 키웁니다. `1일 → 6일 → round(이전 간격 × EF)`.
- **회상 실패(품질 < 3)**: 반복 횟수와 간격을 초기화해 다음 날 다시 복습합니다(난이도 계수는 유지).

난이도 계수는 1.3 미만으로 내려가지 않습니다. 자세한 설명과 계산 예시는
[`docs/algorithm.md`](./docs/algorithm.md) 에 있습니다.

## 빠른 시작

```bash
# 설치 (개발 모드)
pip install -e .

# 카드 추가
ebbinghaus add "에빙하우스 망각 곡선이란?" --back "시간에 따른 기억 감소 곡선"

# 오늘 복습할 항목 보기
ebbinghaus today

# 복습하기 (회상 후 0~5점으로 채점)
ebbinghaus review

# 통계
ebbinghaus stats
```

명령어 목록:

| 명령어 | 설명 |
| --- | --- |
| `ebbinghaus add FRONT [--back ...]` | 학습 카드 추가 |
| `ebbinghaus list` | 모든 카드와 일정 보기 |
| `ebbinghaus today` | 오늘(또는 지난) 복습 항목 |
| `ebbinghaus review [--id N]` | 대화형 복습 + 채점 |
| `ebbinghaus stats` | 컬렉션 통계 |
| `ebbinghaus delete ID` | 카드 삭제 |

각 명령은 `--help` 로 상세 도움말을 볼 수 있습니다. 데이터베이스 경로는 `--db` 옵션이나
`EBBINGHAUS_DB` 환경 변수로 바꿀 수 있습니다(기본값: `~/.local/share/ebbinghaus-reviewer/reviews.db`).

## 웹 UI (선택)

CLI와 **같은 SQLite 파일**을 공유하는 가벼운 FastAPI + Jinja2 서버가 포함되어 있습니다.

```bash
pip install -e ".[web]"
uvicorn ebbinghaus_reviewer.web:create_app --factory --reload
# http://127.0.0.1:8000 접속 — 대시보드 / 카드 / 복습 / 상태(/healthz)
```

웹 계층은 지연 임포트(import-lazy)로 되어 있어, 핵심 코드와 테스트는 FastAPI 없이도 동작합니다.

## 프로젝트 구조

```
ebbinghaus-reviewer/
├── src/ebbinghaus_reviewer/
│   ├── algorithm.py     # 순수 SM-2 (I/O 없음)
│   ├── storage.py       # SQLite 저장소 (경로 주입 가능)
│   ├── scheduler.py     # 알고리즘 + 저장소 연결 (유스케이스)
│   ├── cli.py           # click + rich CLI
│   └── web/             # FastAPI + Jinja2 (선택)
├── tests/               # pytest (algorithm/storage/scheduler/cli/web)
├── docs/
│   ├── algorithm.md     # SM-2 설명 + 계산 예시
│   └── architecture.md  # 레이어링 / 데이터 모델
├── archive/             # 원본 2021 WPF/C# 소스 (정직한 출처 보존)
├── pyproject.toml
├── README.md · README.zh-CN.md
└── LICENSE
```

레이어링과 데이터 모델은 [`docs/architecture.md`](./docs/architecture.md) 참고.

## 개발

```bash
pip install -e ".[dev,web]"
pytest          # 72개 테스트
ruff check .    # 린트
mypy src        # 타입 체크
```

## 아카이브: 원본 2021 WPF 앱

[`archive/`](./archive) 에는 이 프로젝트의 원본인 **Windows WPF / C#** 데스크톱 앱 소스가 그대로
보관되어 있습니다. 해당 앱은 Windows 전용이며 상용 Syncfusion WPF 라이선스에 의존하기 때문에 이
환경에서는 빌드/실행할 수 없습니다. 실행 불가능했던 바이너리 산출물은 삭제하고 소스만 정직하게
남겼습니다. 자세한 내용은 [`archive/README.md`](./archive/README.md) 를 참고하세요.

- 발표 영상: <https://www.youtube.com/watch?v=J2nf1r5jZrI>
- 발표 슬라이드: [`archive/docs/presentation.pdf`](./archive/docs/presentation.pdf)

## 라이선스

[MIT License](./LICENSE).

---

<a name="english"></a>

## English

### Overview

**Ebbinghaus Reviewer** is a spaced-repetition study tool that helps you review
material along the **Ebbinghaus forgetting curve**. You capture study items
(cards); the **SM-2 algorithm** computes when each is next due, you grade your
recall from 0–5, and the schedule adapts automatically.

This repository is a **clean-room Python reimplementation of the same idea** as
a 2021 Windows WPF/C# app built for a Jeonbuk National University (JBNU)
project. The original WPF source is preserved for honest provenance under
[`archive/`](./archive) (see [Archive](#archive-the-original-2021-wpf-app) below).

### How spaced repetition / SM-2 works

Hermann Ebbinghaus showed that memory fades quickly after learning, but
reviewing at well-chosen moments flattens the *forgetting curve* and moves
material into long-term memory.

**SM-2** (SuperMemo, Woźniak 1990) turns that into an algorithm. Each card keeps
three numbers — `repetitions`, an `ease factor`, and the `interval` in days — and
on every review:

- **Successful recall (quality ≥ 3):** increment repetitions and grow the
  interval: `1 day → 6 days → round(previous interval × EF)`.
- **Failed recall (quality < 3):** reset repetitions and the interval so the
  card is due again tomorrow (the ease factor is preserved).

The ease factor is floored at 1.3. A full explanation with a worked numeric
example is in [`docs/algorithm.md`](./docs/algorithm.md).

### Quickstart

```bash
# install (editable)
pip install -e .

# add a card
ebbinghaus add "What is the Ebbinghaus forgetting curve?" --back "Memory decay over time"

# see what's due today
ebbinghaus today

# review (recall, then grade yourself 0–5)
ebbinghaus review

# stats
ebbinghaus stats
```

Commands:

| Command | Description |
| --- | --- |
| `ebbinghaus add FRONT [--back ...]` | Add a study card |
| `ebbinghaus list` | List all cards and their schedule |
| `ebbinghaus today` | Items due today (or overdue) |
| `ebbinghaus review [--id N]` | Interactive review + grading |
| `ebbinghaus stats` | Collection statistics |
| `ebbinghaus delete ID` | Delete a card |

Every command has detailed `--help`. The database path can be set with `--db`
or the `EBBINGHAUS_DB` environment variable (default:
`~/.local/share/ebbinghaus-reviewer/reviews.db`).

### Web UI (optional)

A lightweight FastAPI + Jinja2 server shares the **same SQLite file** as the CLI.

```bash
pip install -e ".[web]"
uvicorn ebbinghaus_reviewer.web:create_app --factory --reload
# visit http://127.0.0.1:8000 — dashboard / cards / review / health (/healthz)
```

The web layer is import-lazy, so the core code and tests run without FastAPI.

### Project layout

```
ebbinghaus-reviewer/
├── src/ebbinghaus_reviewer/
│   ├── algorithm.py     # pure SM-2 (no I/O)
│   ├── storage.py       # SQLite repository (injectable path)
│   ├── scheduler.py     # ties algorithm + storage (use cases)
│   ├── cli.py           # click + rich CLI
│   └── web/             # FastAPI + Jinja2 (optional)
├── tests/               # pytest (algorithm/storage/scheduler/cli/web)
├── docs/                # algorithm.md, architecture.md
├── archive/             # original 2021 WPF/C# source (honest provenance)
├── pyproject.toml
├── README.md · README.zh-CN.md
└── LICENSE
```

See [`docs/architecture.md`](./docs/architecture.md) for the layering and data model.

### Development

```bash
pip install -e ".[dev,web]"
pytest          # 72 tests
ruff check .    # lint
mypy src        # type check
```

### Archive: the original 2021 WPF app

[`archive/`](./archive) preserves the source of the original **Windows WPF / C#**
desktop app this project grew from. That app is Windows-only and depends on a
commercial Syncfusion WPF license, so it cannot be built or run in this
environment; the non-runnable binary outputs were deleted and only the source
was kept, honestly. See [`archive/README.md`](./archive/README.md) for details.

- Demo video: <https://www.youtube.com/watch?v=J2nf1r5jZrI>
- Slides: [`archive/docs/presentation.pdf`](./archive/docs/presentation.pdf)

### License

[MIT License](./LICENSE).
