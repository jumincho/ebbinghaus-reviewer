# Archive — original 2021 WPF app (Review_Reminder)

**한국어** · [English](#english)

---

이 디렉터리는 **원본 2021년 작품의 소스 코드**를 정직한 출처(provenance) 보존용으로 보관합니다.
저장소 루트의 살아있는 코드는 같은 아이디어를 현대적으로 다시 구현한 **Python 클린룸(clean-room) 재구현**입니다.

## 이게 뭔가요?

`Review_Reminder/` 는 전북대학교(JBNU) 재학 중 진행한 2021년 팀/개인 프로젝트의 원본
**Windows WPF / C#** 데스크톱 앱 소스입니다. 에빙하우스 망각 곡선(Ebbinghaus forgetting curve)에
맞춰 복습 시점에 알림을 띄워주는 학습 도우미였습니다.

- 언어/플랫폼: C# · WPF · .NET Framework 4.x (x86)
- 아키텍처: MVVM
- UI 라이브러리: Syncfusion WPF, Microsoft.WindowsAPICodePack

## 왜 여기서 빌드할 수 없나요?

1. **Windows 전용** — WPF / .NET Framework 4.x 데스크톱 스택은 Windows에서만 빌드·실행됩니다.
2. **상용 라이선스 의존성** — UI가 Syncfusion WPF 컴포넌트(상용 제품)에 의존합니다.
   라이선스 키 없이는 컴파일된 바이너리가 정상 동작하지 않습니다.

이 두 가지 이유로, 과거에 배포 폴더(`dist/`)에 들어있던 컴파일된 `.exe` 는 **실행 불가능한
죽은 산출물**이었습니다(필요한 Syncfusion DLL이 누락됨). 그래서 포트폴리오 가치를 위해
바이너리 산출물(`dist/`, `build-artifacts/`)은 삭제하고, **소스 코드만** 정직하게 보존했습니다.

## 보존된 것 / 삭제된 것

| 항목 | 처리 |
| --- | --- |
| `Review_Reminder/` (C# 소스) | 보존 (이 디렉터리) |
| `Review_Reminder.sln` | 보존 |
| `docs/presentation.pdf` (발표 자료) | 보존 (`archive/docs/`) |
| `dist/Review_Reminder.exe`, `*.pdb` | 삭제 (실행 불가 바이너리) |
| `build-artifacts/obj-Release/` (BAML/디컴파일 산출물) | 삭제 (빌드 캐시) |

## 발표 자료

- 발표 영상: <https://www.youtube.com/watch?v=J2nf1r5jZrI>
- 발표 슬라이드: [`docs/presentation.pdf`](docs/presentation.pdf)

## 그래서 지금 동작하는 코드는?

저장소 루트의 `src/ebbinghaus_reviewer/` 에 있는 **Python 재구현**을 보세요. 같은 의도
(학습 항목 등록 → 망각 곡선에 따른 복습 일정 → 회상 채점 → 반복)를 SM-2 간격 반복
알고리즘으로 구현했고, CLI·웹 UI·테스트를 갖추고 있습니다.

---

<a name="english"></a>

## English

This directory preserves the **source code of the original 2021 project** for honest provenance.
The live code at the repository root is a modern **clean-room Python reimplementation** of the
same idea.

### What is this?

`Review_Reminder/` is the original **Windows WPF / C#** desktop app from a 2021 project done at
Jeonbuk National University (JBNU). It was a study helper that surfaced review reminders timed to
the Ebbinghaus forgetting curve.

- Language / platform: C# · WPF · .NET Framework 4.x (x86)
- Architecture: MVVM
- UI libraries: Syncfusion WPF, Microsoft.WindowsAPICodePack

### Why can't it be built here?

1. **Windows-only** — the WPF / .NET Framework 4.x desktop stack builds and runs on Windows only.
2. **Commercial-license dependency** — the UI depends on Syncfusion WPF components (a commercial
   product). Without a license key, the compiled binary does not work.

For those two reasons, the compiled `.exe` that used to live under `dist/` was a **non-runnable,
dead artifact** (it was missing the required Syncfusion DLLs). To keep the portfolio honest and
lean, the binary build outputs (`dist/`, `build-artifacts/`) were deleted and **only the source
code** was preserved.

### Kept vs. deleted

| Item | Disposition |
| --- | --- |
| `Review_Reminder/` (C# source) | Kept (this directory) |
| `Review_Reminder.sln` | Kept |
| `docs/presentation.pdf` (slides) | Kept (`archive/docs/`) |
| `dist/Review_Reminder.exe`, `*.pdb` | Deleted (non-runnable binary) |
| `build-artifacts/obj-Release/` (BAML / decompile output) | Deleted (build cache) |

### Materials

- Demo video: <https://www.youtube.com/watch?v=J2nf1r5jZrI>
- Slides: [`docs/presentation.pdf`](docs/presentation.pdf)

### Where is the code that actually runs?

See the **Python reimplementation** under `src/ebbinghaus_reviewer/` at the repository root. It
implements the same intent (capture study items → schedule reviews along the forgetting curve →
grade recall → repeat) using the SM-2 spaced-repetition algorithm, with a CLI, a web UI, and tests.
