# Review Reminder (복습 알림)

> 에빙하우스 망각 곡선에 기반해 복습 시점을 자동으로 알려주는 Windows 데스크톱 앱

독일의 심리학자 헤르만 에빙하우스(Hermann Ebbinghaus)는 학습 후 시간이 지남에 따라
기억이 감소하는 **망각 곡선**을 제시했습니다. 이 곡선에 따르면 학습 직후 일정한
간격으로 복습하면 장기 기억으로의 전이가 효과적으로 일어납니다.

본 프로그램은 사용자가 학습한 내용을 등록하면 망각 곡선에 맞춘 시점에 복습 알림을
띄워, 잊어버리기 전에 다시 떠올릴 수 있도록 돕는 WPF 기반 데스크톱 앱입니다.

## 주요 기능

- **할 일 / 학습 항목 등록** — 복습할 내용을 TODO 형식으로 추가
- **자동 복습 일정 산정** — 에빙하우스 곡선에 따라 다음 복습 시점을 자동 계산
- **달력 뷰** — 등록된 복습 일정을 캘린더에서 한눈에 확인 (Syncfusion SfScheduler)
- **복습 시스템 뷰** — 오늘 복습해야 할 항목 목록 및 알림
- **홈 화면** — 진행 상황 요약 및 빠른 진입
- **정보 화면** — 망각 곡선 및 사용법 안내

## 화면 구성

좌측 메뉴를 통해 전환되는 다섯 개의 주요 화면:

| 화면 | 설명 |
| --- | --- |
| Home | 사용자 대시보드 / 진입점 |
| ToDoList | 학습 · 복습 항목 등록 및 관리 |
| Calendar | 복습 일정 캘린더 뷰 |
| ReviewSystem | 망각 곡선 기반 복습 알림 |
| Information | 에빙하우스 망각 곡선 및 사용 안내 |

## 기술 스택

- **언어**: C#
- **플랫폼**: Windows / WPF (.NET Framework 4.x)
- **아키텍처**: MVVM (Model-View-ViewModel)
- **UI 라이브러리**:
  - Syncfusion WPF (SfScheduler, SfInput, SfBusyIndicator, SfSkinManager, Shared)
  - Microsoft.WindowsAPICodePack (Shell / ShellExtensions)
- **빌드 도구**: MSBuild / Visual Studio

## 프로젝트 구조

```
review_reminder/
├── README.md
├── .gitignore
├── dist/                              # 배포용 빌드 결과물
│   ├── Review_Reminder.exe            # WPF 실행 파일 (PE32, .NET assembly)
│   ├── Review_Reminder.pdb            # 디버깅 심볼
│   └── README.md                      # 실행 방법
├── build-artifacts/                   # obj/Release 중간 산출물 (보존용)
│   ├── App.baml, App.g.cs             # XAML 컴파일 결과
│   ├── MainWindow.baml, MainWindow.g.cs
│   ├── MVVM/View/                     # 각 View의 컴파일 산출물
│   │   ├── HomeView.{baml,g.cs}
│   │   ├── ToDoListView.{baml,g.cs}
│   │   ├── CalendarView.{baml,g.cs}
│   │   ├── ReviewSystemView.{baml,g.cs}
│   │   ├── InformationView.{baml,g.cs}
│   │   ├── TodolistReminder.{baml,g.cs}
│   │   └── listboxitemlist.{baml,g.cs}
│   ├── Theme/MenuButtonTheme.baml     # 메뉴 버튼 테마
│   └── README.md
└── docs/
    └── presentation.pdf               # 발표 자료 ("배운 걸 기억 못 하는 사람도 있나요")
```

> 참고: 원본 `.xaml` / `.xaml.cs` 소스 파일은 현재 저장소에 커밋되어 있지 않으며,
> 이 저장소는 컴파일 산출물과 발표 자료를 보존하는 용도로 정리되어 있습니다.
> 원본 소스가 필요한 경우 [원 작성자](https://github.com/jumincho)에게 문의하세요.

## 실행 방법

릴리스 전용 저장소이므로 별도의 빌드 없이 바로 실행할 수 있습니다.

1. [`dist/Review_Reminder.exe`](dist/Review_Reminder.exe) 를 다운로드합니다.
2. Windows 환경에서 .NET Framework 4.x 가 설치되어 있는지 확인합니다.
3. 실행 파일을 더블 클릭하여 시작합니다.

원본 소스로부터 다시 빌드하려는 경우:

```text
Visual Studio 2019 이상에서 Review_Reminder.csproj 열기 → Release 구성으로 빌드
```

필요 패키지(NuGet):

- Syncfusion.SfScheduler.WPF, Syncfusion.SfInput.Wpf, Syncfusion.Shared.Wpf,
  Syncfusion.SfBusyIndicator.WPF, Syncfusion.SfSkinManager.WPF, Syncfusion.Licensing
- Microsoft.WindowsAPICodePack(.Shell / .ShellExtensions)

## 발표 자료

- 발표 영상: <https://www.youtube.com/watch?v=J2nf1r5jZrI>
- 발표 슬라이드: [`docs/presentation.pdf`](docs/presentation.pdf)

## 스크린샷

<img width="80%" src="https://user-images.githubusercontent.com/77545063/200372947-d86dc543-3324-48b2-a711-f35bfa5cd5b2.png" alt="Review Reminder 스크린샷"/>
