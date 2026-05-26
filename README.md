# Review Reminder (복습 알림)

> 에빙하우스 망각 곡선에 기반한 Windows WPF 복습 알림 앱 — **소스 코드가 보존되지 않은 아카이브**

> [!WARNING]
> **이 저장소는 빌드도 실행도 불가능한 아카이브입니다.**
> - 원본 `.xaml` / `.xaml.cs` / `.csproj` / `.sln` 소스 파일이 **단 하나도** 커밋되어 있지 않습니다.
> - `dist/Review_Reminder.exe` 도 의존 DLL 7개(Syncfusion 6개 + Microsoft.WindowsAPICodePack 2개)가 **동봉되어 있지 않아** 더블 클릭해도 즉시 크래시합니다.
> - Syncfusion WPF 컴포넌트는 라이선스가 필요한 상용 라이브러리입니다.
>
> 본 저장소는 **발표 자료**(`docs/presentation.pdf`)와 **컴파일 산출물의 흔적**(`build-artifacts/obj-Release/`의 `.baml`·`.g.cs` 등)을 보존하기 위한 용도입니다.
> 실제로 동작하는 코드를 보고 싶다면 [원 작성자](https://github.com/jumincho)에게 직접 문의하세요.

## 원래 어떤 앱이었나

> 아래는 원본 앱이 **제공했던** 기능 설명입니다. 본 저장소의 산출물로는 그 동작을 검증할 수 없습니다.

독일의 심리학자 헤르만 에빙하우스(Hermann Ebbinghaus)는 학습 후 시간이 지남에 따라
기억이 감소하는 **망각 곡선**을 제시했습니다. 이 곡선에 따르면 학습 직후 일정한
간격으로 복습하면 장기 기억으로의 전이가 효과적으로 일어납니다.

원본 앱은 사용자가 학습 내용을 등록하면 망각 곡선에 맞춘 시점에 복습 알림을
띄우는 WPF 기반 데스크톱 프로그램이었습니다.

### 주요 기능 (원본 기준)

- 할 일 / 학습 항목 등록 (TODO)
- 에빙하우스 곡선에 따른 자동 복습 일정 산정
- Syncfusion SfScheduler 기반 캘린더 뷰
- 오늘 복습할 항목 알림 (ReviewSystem)
- 홈 화면 · 정보 화면

### 화면 구성 (BAML 산출물에서 확인 가능한 View)

| View | 비고 |
| --- | --- |
| HomeView | 대시보드 |
| ToDoListView | 학습·복습 항목 등록 |
| CalendarView / CalenderView | 일정 캘린더 (원본에 오타 변종 2개 공존) |
| ReviewSystemView | 복습 알림 |
| InformationView | 에빙하우스 곡선 안내 |
| TodolistReminder | 알림 창 (Window) |
| listboxitemlist | 항목 목록 컨트롤 |

### 기술 스택 (원본 기준)

- 언어: C#
- 플랫폼: Windows / WPF (.NET Framework 4.x, x86)
- 아키텍처: MVVM이라 알려져 있으나, 원본 ViewModel·Model `.cs` 가 부재하여 검증 불가
- UI 라이브러리: Syncfusion WPF + Microsoft.WindowsAPICodePack

## 저장소 구조

```
review_reminder/
├── README.md
├── .gitignore
├── dist/                              # 단독 실행 불가 — 의존 DLL 미동봉
│   ├── Review_Reminder.exe            # PE32 (x86) .NET assembly, 396 KB
│   ├── Review_Reminder.pdb            # 디버깅 심볼
│   └── README.md
├── build-artifacts/                   # obj/Release 중간 산출물 (보존용)
│   ├── obj-Release/
│   │   ├── App.{baml,g.cs,g.i.cs}     # XAML → BAML 컴파일 산출물
│   │   ├── MainWindow.{baml,g.cs,g.i.cs}
│   │   ├── MVVM/View/
│   │   │   ├── HomeView.{baml,g.cs}
│   │   │   ├── ToDoListView.{baml,g.cs}
│   │   │   ├── CalendarView.{baml,g.cs}
│   │   │   ├── CalenderView.g.cs       # 원본의 오타 변종
│   │   │   ├── ReviewSystemView.{baml,g.cs}
│   │   │   ├── InformationView.{baml,g.cs}
│   │   │   ├── TodolistReminder.{baml,g.cs}
│   │   │   └── listboxitemlist.{baml,g.cs}
│   │   ├── Theme/MenuButtonTheme.baml
│   │   ├── TempPE/                     # MSBuild 임시 컴파일 산출물
│   │   ├── GeneratedInternalTypeHelper.g.cs
│   │   ├── Review_Reminder_Content.g.{i.}cs
│   │   ├── *.cache / *.lref            # MSBuild 캐시
│   │   └── Review_Reminder.csproj.FileListAbsolute.txt
│   └── README.md
└── docs/
    └── presentation.pdf               # 발표 자료
```

> `build-artifacts/obj-Release/Review_Reminder.csproj.FileListAbsolute.txt` 는 원 작성자의 로컬 경로(`C:\Users\raich\...`)를 포함하고 있습니다. 보존을 위해 그대로 두었습니다.

## 실행해 보고 싶다면 (현실적 옵션)

`dist/Review_Reminder.exe` 를 실제로 띄우려면 다음 DLL 7개를 같은 폴더에 직접 배치해야 합니다 (모두 NuGet 또는 Syncfusion 인스톨러로 받을 수 있고, Syncfusion 은 라이선스 키도 필요):

```
Microsoft.WindowsAPICodePack.Shell.dll
Microsoft.WindowsAPICodePack.ShellExtensions.dll
Syncfusion.Licensing.dll
Syncfusion.SfScheduler.WPF.dll
Syncfusion.Shared.Wpf.dll
Syncfusion.SfBusyIndicator.WPF.dll
Syncfusion.SfInput.Wpf.dll
Syncfusion.SfSkinManager.WPF.dll
```

필요한 정확한 버전은 `build-artifacts/obj-Release/Review_Reminder.csproj.FileListAbsolute.txt` 에서 확인할 수 있습니다. 모든 DLL을 정확한 버전으로 맞춰 같은 폴더에 두고 .NET Framework 4.x 가 설치된 32-bit 호환 Windows 환경에서 실행해야 합니다.

소스로부터 재컴파일은 **현재 저장소만으로는 불가능**합니다. `.csproj`, `.sln`, `.xaml`, `.xaml.cs`, `packages.config` 가 전부 누락되어 있습니다.

## 발표 자료

- 발표 영상: <https://www.youtube.com/watch?v=J2nf1r5jZrI>
- 발표 슬라이드: [`docs/presentation.pdf`](docs/presentation.pdf)

## 스크린샷

> 원본 앱의 동작 화면입니다.

<img width="80%" src="https://user-images.githubusercontent.com/77545063/200372947-d86dc543-3324-48b2-a711-f35bfa5cd5b2.png" alt="Review Reminder 스크린샷"/>
