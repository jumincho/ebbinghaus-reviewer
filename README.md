<div align="center">

# ebbinghaus-reviewer

**에빙하우스 망각곡선 기반 WPF 복습 알림 앱**
**Ebbinghaus-curve WPF review-reminder app**

![Platform](https://img.shields.io/badge/platform-Windows%20WPF-0078D4?logo=windows&logoColor=white)
![Language](https://img.shields.io/badge/language-C%23-239120?logo=csharp&logoColor=white)
![Framework](https://img.shields.io/badge/.NET-Framework%204.x-512BD4)
![License](https://img.shields.io/badge/license-MIT-green)
![Year](https://img.shields.io/badge/year-2021-blue)

**한국어** · [English](#english) · [中文](./README.zh-CN.md)

</div>

---

## 개요

에빙하우스 망각 곡선에 기반한 Windows WPF 복습 알림 앱입니다. 독일의 심리학자 헤르만 에빙하우스(Hermann Ebbinghaus)는 학습 후 시간이 지남에 따라 기억이 감소하는 **망각 곡선**을 제시했습니다. 이 곡선에 따르면 학습 직후 일정한 간격으로 복습하면 장기 기억으로의 전이가 효과적으로 일어납니다.

이 앱은 사용자가 학습 내용을 등록하면 망각 곡선에 맞춘 시점에 복습 알림을 띄워주는 WPF 기반 데스크톱 프로그램입니다.

## 주요 기능

- 할 일 / 학습 항목 등록 (TODO)
- 에빙하우스 곡선에 따른 자동 복습 일정 산정
- Syncfusion SfScheduler 기반 캘린더 뷰
- 오늘 복습할 항목 알림 (ReviewSystem)
- 홈 화면 · 정보 화면

## 화면 구성

| View | 비고 |
| --- | --- |
| HomeView | 대시보드 |
| ToDoListView | 학습·복습 항목 등록 |
| CalendarView | 일정 캘린더 |
| ReviewSystemView | 복습 알림 |
| InformationView | 에빙하우스 곡선 안내 |
| TodolistReminder | 알림 창 (Window) |

## 기술 스택

- 언어: C#
- 플랫폼: Windows / WPF (.NET Framework 4.x, x86)
- 아키텍처: MVVM
- UI 라이브러리: Syncfusion WPF + Microsoft.WindowsAPICodePack

## 저장소 구조

```
ebbinghaus-reviewer/
├── README.md
├── LICENSE
├── .gitignore
├── Review_Reminder.sln
├── Review_Reminder/
│   ├── Review_Reminder.csproj
│   ├── App.{xaml,xaml.cs}
│   ├── MainWindow.{xaml,xaml.cs}
│   ├── MVVM/
│   │   ├── Model/
│   │   │   ├── EbbinghausCurve.cs
│   │   │   ├── ReviewItem.cs
│   │   │   └── ReviewSchedule.cs
│   │   ├── ViewModel/
│   │   │   ├── BaseViewModel.cs
│   │   │   ├── MainViewModel.cs
│   │   │   ├── HomeViewModel.cs
│   │   │   ├── ToDoListViewModel.cs
│   │   │   ├── CalendarViewModel.cs
│   │   │   ├── ReviewSystemViewModel.cs
│   │   │   └── InformationViewModel.cs
│   │   └── View/
│   │       ├── HomeView.{xaml,xaml.cs}
│   │       ├── ToDoListView.{xaml,xaml.cs}
│   │       ├── CalendarView.{xaml,xaml.cs}
│   │       ├── ReviewSystemView.{xaml,xaml.cs}
│   │       ├── InformationView.{xaml,xaml.cs}
│   │       └── TodolistReminder.{xaml,xaml.cs}
│   ├── Services/
│   │   ├── IReviewScheduler.cs
│   │   ├── ReviewScheduler.cs
│   │   ├── INotificationService.cs
│   │   └── NotificationService.cs
│   └── Theme/
│       └── MenuButtonTheme.xaml
├── dist/
│   ├── Review_Reminder.exe
│   └── Review_Reminder.pdb
├── build-artifacts/
│   └── obj-Release/
└── docs/
    └── presentation.pdf
```

## 빌드

```
dotnet build Review_Reminder.sln
```

또는 Visual Studio 2019 이상에서 `Review_Reminder.sln` 을 열고:

1. NuGet 패키지 복원 (Syncfusion + Microsoft.WindowsAPICodePack)
2. Build → Release

Syncfusion WPF 컴포넌트는 라이선스 키가 필요합니다 ([Syncfusion Community](https://www.syncfusion.com/products/communitylicense) 또는 상용 라이선스).

## 발표 자료

- 발표 영상: <https://www.youtube.com/watch?v=J2nf1r5jZrI>
- 발표 슬라이드: [`docs/presentation.pdf`](docs/presentation.pdf)

## 스크린샷

<img width="80%" src="https://user-images.githubusercontent.com/77545063/200372947-d86dc543-3324-48b2-a711-f35bfa5cd5b2.png" alt="Review Reminder 스크린샷"/>

## 라이선스

[MIT License](./LICENSE). Syncfusion WPF / Microsoft.WindowsAPICodePack 같은 런타임 의존 라이브러리는 각자의 라이선스가 별도로 적용됩니다.

---

<a name="english"></a>

## English

Ebbinghaus-curve based WPF review-reminder app for Windows. Hermann Ebbinghaus's **forgetting curve** describes how memory decays over time after learning; reviewing at well-chosen intervals shortly after learning helps transfer information into long-term memory.

The app lets you register study items and then surfaces review reminders at curve-aligned times as a WPF desktop program.

### Features

- Register study / TODO items
- Auto-scheduled review reminders along the Ebbinghaus curve
- Calendar view via Syncfusion SfScheduler
- Today's review-item notifications (ReviewSystem)
- Home and Information screens

### Views

| View | Notes |
| --- | --- |
| HomeView | Dashboard |
| ToDoListView | Study / review item entry |
| CalendarView | Schedule calendar |
| ReviewSystemView | Review notifications |
| InformationView | Ebbinghaus-curve explainer |
| TodolistReminder | Notification window |

### Stack

- Language: C#
- Platform: Windows / WPF (.NET Framework 4.x, x86)
- Architecture: MVVM
- UI: Syncfusion WPF + Microsoft.WindowsAPICodePack

### Project structure

```
ebbinghaus-reviewer/
├── README.md
├── LICENSE
├── .gitignore
├── Review_Reminder.sln
├── Review_Reminder/
│   ├── Review_Reminder.csproj
│   ├── App.{xaml,xaml.cs}
│   ├── MainWindow.{xaml,xaml.cs}
│   ├── MVVM/{Model,ViewModel,View}/
│   ├── Services/
│   └── Theme/MenuButtonTheme.xaml
├── dist/
│   ├── Review_Reminder.exe
│   └── Review_Reminder.pdb
├── build-artifacts/
│   └── obj-Release/
└── docs/
    └── presentation.pdf
```

### Build

```
dotnet build Review_Reminder.sln
```

Or in Visual Studio 2019+:

1. Open `Review_Reminder.sln`
2. Restore NuGet packages (Syncfusion + Microsoft.WindowsAPICodePack)
3. Build → Release

Syncfusion WPF requires a [Syncfusion Community](https://www.syncfusion.com/products/communitylicense) or Commercial license.

### Materials

- Demo video: <https://www.youtube.com/watch?v=J2nf1r5jZrI>
- Slides: [`docs/presentation.pdf`](docs/presentation.pdf)

### Screenshot

<img width="80%" src="https://user-images.githubusercontent.com/77545063/200372947-d86dc543-3324-48b2-a711-f35bfa5cd5b2.png" alt="Review Reminder screenshot"/>

### License

[MIT License](./LICENSE). Runtime dependencies (Syncfusion WPF, Microsoft.WindowsAPICodePack) remain under their respective licenses.
