<div align="center">

# ebbinghaus-reviewer

**基于艾宾浩斯遗忘曲线的 WPF 复习提醒桌面应用**

![Platform](https://img.shields.io/badge/platform-Windows%20WPF-0078D4?logo=windows&logoColor=white)
![Language](https://img.shields.io/badge/language-C%23-239120?logo=csharp&logoColor=white)
![Framework](https://img.shields.io/badge/.NET-Framework%204.x-512BD4)
![License](https://img.shields.io/badge/license-MIT-green)
![Year](https://img.shields.io/badge/year-2021-blue)

[한국어](./README.md) · [English](./README.md#english) · **中文**

</div>

---

## 概览

基于艾宾浩斯遗忘曲线的 Windows WPF 复习提醒应用。德国心理学家赫尔曼·艾宾浩斯 (Hermann Ebbinghaus) 提出过 **遗忘曲线**，描述了学习后记忆随时间衰减的规律。按照该曲线，在学习刚结束后以特定间隔复习，有助于将信息转入长期记忆。

本应用是一款 WPF 桌面程序：用户登记学习内容后，会在与遗忘曲线匹配的时点弹出复习提醒。

## 功能

- 待办 / 学习项录入 (TODO)
- 按艾宾浩斯曲线自动安排复习日程
- 基于 Syncfusion SfScheduler 的日历视图
- 当日复习项目提醒 (ReviewSystem)
- 主页 · 信息页

## 屏幕

| View | 备注 |
| --- | --- |
| HomeView | 仪表盘 |
| ToDoListView | 学习/复习项目录入 |
| CalendarView | 日历 |
| ReviewSystemView | 复习提醒 |
| InformationView | 艾宾浩斯曲线说明 |
| TodolistReminder | 提醒窗口 (Window) |

## 技术栈

- 语言: C#
- 平台: Windows / WPF (.NET Framework 4.x, x86)
- 架构: MVVM
- UI 库: Syncfusion WPF + Microsoft.WindowsAPICodePack

## 仓库结构

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

## 构建

```
dotnet build Review_Reminder.sln
```

或在 Visual Studio 2019+ 中打开 `Review_Reminder.sln`：

1. 还原 NuGet 包（Syncfusion + Microsoft.WindowsAPICodePack）
2. Build → Release

Syncfusion WPF 需要 [Syncfusion Community](https://www.syncfusion.com/products/communitylicense) 或商业许可证。

## 演讲资料

- 演示视频: <https://www.youtube.com/watch?v=J2nf1r5jZrI>
- 演讲幻灯片: [`docs/presentation.pdf`](docs/presentation.pdf)

## 屏幕截图

<img width="80%" src="https://user-images.githubusercontent.com/77545063/200372947-d86dc543-3324-48b2-a711-f35bfa5cd5b2.png" alt="Review Reminder 截图"/>

## 许可证

[MIT License](./LICENSE)。Syncfusion WPF / Microsoft.WindowsAPICodePack 等运行时依赖各自适用自己的许可证。
