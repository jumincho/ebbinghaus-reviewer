# Archive — original 2021 WPF app (Review_Reminder)

This directory preserves the **source code of the original 2021 project** for honest provenance.
The live code at the repository root is a modern **clean-room Python reimplementation** of the
same idea.

## What is this?

`Review_Reminder/` is the original **Windows WPF / C#** desktop app from a 2021 project done at
Jeonbuk National University (JBNU). It was a study helper that surfaced review reminders timed to
the Ebbinghaus forgetting curve.

- Language / platform: C# · WPF · .NET Framework 4.x (x86)
- Architecture: MVVM
- UI libraries: Syncfusion WPF, Microsoft.WindowsAPICodePack

## Why can't it be built here?

1. **Windows-only** — the WPF / .NET Framework 4.x desktop stack builds and runs on Windows only.
2. **Commercial-license dependency** — the UI depends on Syncfusion WPF components (a commercial
   product). Without a license key, the compiled binary does not work.

For those two reasons, the compiled `.exe` that used to live under `dist/` was a **non-runnable,
dead artifact** (it was missing the required Syncfusion DLLs). To keep the portfolio honest and
lean, the binary build outputs (`dist/`, `build-artifacts/`) were deleted and **only the source
code** was preserved.

## Kept vs. deleted

| Item | Disposition |
| --- | --- |
| `Review_Reminder/` (C# source) | Kept (this directory) |
| `Review_Reminder.sln` | Kept |
| `docs/presentation.pdf` (slides) | Kept (`archive/docs/`) |
| `dist/Review_Reminder.exe`, `*.pdb` | Deleted (non-runnable binary) |
| `build-artifacts/obj-Release/` (BAML / decompile output) | Deleted (build cache) |

## Materials

- Demo video: <https://www.youtube.com/watch?v=J2nf1r5jZrI>
- Slides: [`docs/presentation.pdf`](docs/presentation.pdf)

## Where is the code that actually runs?

See the **Python reimplementation** under `src/ebbinghaus_reviewer/` at the repository root. It
implements the same intent (capture study items → schedule reviews along the forgetting curve →
grade recall → repeat) using the SM-2 spaced-repetition algorithm, with a CLI, a web UI, and tests.
