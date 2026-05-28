<div align="center">

# ebbinghaus-reviewer

**基于艾宾浩斯遗忘曲线的 WPF 复习提醒桌面应用 —— 源码未保留的归档仓库**

![Platform](https://img.shields.io/badge/platform-Windows%20WPF-0078D4?logo=windows&logoColor=white)
![Language](https://img.shields.io/badge/language-C%23-239120?logo=csharp&logoColor=white)
![Framework](https://img.shields.io/badge/.NET-Framework%204.x-512BD4)
![Status](https://img.shields.io/badge/status-archive--only-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)
![Year](https://img.shields.io/badge/year-2021-blue)

[한국어](./README.md) · [English](./README.md#english) · **中文**

</div>

---

## 概览

> 基于艾宾浩斯遗忘曲线的 Windows WPF 复习提醒应用 —— **源码未保留的归档仓库**

> [!WARNING]
> **本仓库无法构建、也无法运行。**
> - 原始的 `.xaml` / `.xaml.cs` / `.csproj` / `.sln` 源文件 **一个都没有** 被提交。
> - `dist/Review_Reminder.exe` 缺少 7 个运行时 DLL (Syncfusion 6 个 + Microsoft.WindowsAPICodePack 2 个),
>   **未一同打包**,因此双击会立即崩溃。
> - Syncfusion WPF 组件是需要许可证的商业库。
>
> 本仓库的用途是保留 **演讲资料** (`docs/presentation.pdf`) 和
> **编译产物的痕迹** (`build-artifacts/obj-Release/` 下的 `.baml`、`.g.cs` 等)。
> 如果想看真正能运行的代码,请直接联系 [原作者](https://github.com/jumincho)。

## 原本是什么样的应用

> 以下是原应用 **曾经提供的** 功能说明。本仓库的产物无法验证这些行为。

德国心理学家赫尔曼·艾宾浩斯 (Hermann Ebbinghaus) 提出过 **遗忘曲线**,
描述了学习后记忆随时间衰减的规律。按照该曲线,在学习刚结束后以特定间隔
复习,有助于将信息转入长期记忆。

原应用是一款 WPF 桌面程序:用户登记学习内容后,会在与遗忘曲线匹配的时点
弹出复习提醒。

### 功能 (依据原版)

- 待办 / 学习项录入 (TODO)
- 按艾宾浩斯曲线自动安排复习日程
- 基于 Syncfusion SfScheduler 的日历视图
- 当日复习项目提醒 (ReviewSystem)
- 主页 · 信息页

### 屏幕 (从 BAML 产物可见的 View)

| View | 备注 |
| --- | --- |
| HomeView | 仪表盘 |
| ToDoListView | 学习/复习项目录入 |
| CalendarView / CalenderView | 日历 (原版同时存在两种拼写) |
| ReviewSystemView | 复习提醒 |
| InformationView | 艾宾浩斯曲线说明 |
| TodolistReminder | 提醒窗口 (Window) |
| listboxitemlist | 项目列表控件 |

### 技术栈 (依据原版)

- 语言: C#
- 平台: Windows / WPF (.NET Framework 4.x, x86)
- 架构: 据称为 MVVM,但原版的 ViewModel · Model `.cs` 缺失,无从验证
- UI 库: Syncfusion WPF + Microsoft.WindowsAPICodePack

## 仓库结构

```
ebbinghaus-reviewer/
├── README.md
├── LICENSE
├── .gitignore
├── dist/                              # 单独无法运行 —— 缺运行时 DLL
│   ├── Review_Reminder.exe            # PE32 (x86) .NET assembly, 396 KB
│   ├── Review_Reminder.pdb            # 调试符号
│   └── README.md
├── build-artifacts/                   # obj/Release 中间产物 (保存用)
│   ├── obj-Release/
│   │   ├── App.{baml,g.cs,g.i.cs}     # XAML → BAML 编译产物
│   │   ├── MainWindow.{baml,g.cs,g.i.cs}
│   │   ├── MVVM/View/                 # 上面 7 个 View 的 BAML / g.cs
│   │   ├── Theme/MenuButtonTheme.baml
│   │   ├── TempPE/                    # MSBuild 临时编译产物
│   │   ├── GeneratedInternalTypeHelper.g.cs
│   │   ├── Review_Reminder_Content.g.{i.}cs
│   │   ├── *.cache / *.lref           # MSBuild 缓存
│   │   └── Review_Reminder.csproj.FileListAbsolute.txt
│   └── README.md
└── docs/
    └── presentation.pdf               # 演讲资料
```

> `build-artifacts/obj-Release/Review_Reminder.csproj.FileListAbsolute.txt`
> 原本包含原作者的本地绝对路径 (`C:\Users\raich\Desktop\reminderrr\...`),
> 这是一份 MSBuild 产物。为避免个人信息泄露,本仓库已将其改写为以 csproj 为
> 基准的相对路径 (`bin\Release\...`、`obj\Release\...`)。

## 如果想尝试运行

要实际启动 `dist/Review_Reminder.exe`,需要把下列 7 个 DLL 放到同一目录下
(都可通过 NuGet 或 Syncfusion 安装包获取;Syncfusion 还需要 license key):

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

所需的精确版本可以在
`build-artifacts/obj-Release/Review_Reminder.csproj.FileListAbsolute.txt` 中查到。
准备好所有匹配版本的 DLL 后,在已安装 .NET Framework 4.x 的 32 位兼容 Windows
环境下运行即可。

**仅靠本仓库无法从源码重新编译** ——
`.csproj`、`.sln`、`.xaml`、`.xaml.cs`、`packages.config` 全部缺失。

## 演讲资料

- 演示视频: <https://www.youtube.com/watch?v=J2nf1r5jZrI>
- 演讲幻灯片: [`docs/presentation.pdf`](docs/presentation.pdf)

## 屏幕截图

> 原应用的运行画面。

<img width="80%" src="https://user-images.githubusercontent.com/77545063/200372947-d86dc543-3324-48b2-a711-f35bfa5cd5b2.png" alt="Review Reminder 截图"/>

## 许可证

[MIT License](./LICENSE) —— 只适用于原产物 (演讲资料、编译后的二进制)。
Syncfusion WPF / Microsoft.WindowsAPICodePack 等运行时依赖各自适用自己的许可证。
