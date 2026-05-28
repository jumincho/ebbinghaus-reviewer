# source-reconstruction/

> [!WARNING]
> **This is a hypothetical reconstruction.** The original `.xaml` / `.xaml.cs` /
> `.csproj` / `.sln` source files are not preserved. The files below are what
> the source would have *plausibly* looked like, inferred from the BAML output
> under `build-artifacts/obj-Release/`. They are a teaching skeleton, **not**
> the original implementation.

## What this directory is

A best-effort sketch of the source code that *would* have produced the BAML /
`.g.cs` artifacts under `../build-artifacts/obj-Release/`. The intent is to
make the MVVM wiring legible to a reader — view names, ViewModel responsibilities,
the Ebbinghaus-curve schedule, the Syncfusion `SfScheduler` host — without
pretending to be the lost original.

## What this directory is *not*

- **Not the original source.** The original `.xaml`, `.xaml.cs`, `.csproj`,
  `.sln` and `packages.config` are not in this repository and never were
  committed.
- **Not buildable as-is.** The Syncfusion WPF and Microsoft.WindowsAPICodePack
  DLLs are commercial / external dependencies that are not pinned to specific
  versions here. Even if you fixed the references, the placeholder XAML below
  is too thin to produce the original UI.
- **Not a verification of the original behaviour.** Where the inferred shape
  was ambiguous (e.g. exactly which Ebbinghaus offsets the original used), the
  code below makes a *reasonable* choice and labels it as such. The compiled
  `dist/Review_Reminder.exe` is the only authoritative behavioural record, and
  this directory does not claim to match it byte-for-byte.

## How it was inferred

| Signal in `build-artifacts/obj-Release/` | What it told us |
| --- | --- |
| `App.g.cs` | Root namespace is `Review_Reminder`, StartupUri is `MainWindow.xaml` |
| `MainWindow.g.cs` | `Close_Click` + `Mimimize_Click` (sic) handlers on connection IDs 1 + 2 |
| `MVVM/View/*.g.cs` namespace | `Review_Reminder.MVVM.View` |
| `MVVM/View/CalendarView.g.cs` field `CVM` of type `Review_Reminder.MVVM.ViewModel.CalendarViewModel` | ViewModel namespace + class name |
| `MVVM/View/CalendarView.g.cs` field `Schedule` of type `Syncfusion.UI.Xaml.Scheduler.SfScheduler` | Syncfusion `SfScheduler` is the calendar host |
| `MVVM/View/ToDoListView.g.cs` fields `PageListBox` + `inputtextbox` + `listclicked` + `btnclick` | Item list + add-input form on the ToDoList |
| `MVVM/View/TodolistReminder.g.cs` fields `first` / `snd` / `thd` / `forth` (4 TextBlocks) | The Ebbinghaus reminder has **4** interval slots |
| `Review_Reminder.csproj.FileListAbsolute.txt` | The seven runtime DLLs + file layout |
| `MVVM/View/CalenderView.g.cs` (no `.baml`) | The original ships a typo variant `CalenderView` alongside the real `CalendarView` |

The four-TextBlock layout (`first`, `snd`, `thd`, `forth`) of `TodolistReminder`
is the strongest single clue about the schedule shape: the original schedules
**four** Ebbinghaus reminders per study item. The exact intervals are not
recoverable from BAML, so this reconstruction uses the textbook offsets
(10 min, 1 day, 1 week, 1 month).

## Layout

```
source-reconstruction/
├── README.md                          # this file
├── Review_Reminder.sln
├── Review_Reminder.csproj
├── App.xaml
├── App.xaml.cs
├── MainWindow.xaml
├── MainWindow.xaml.cs
├── MVVM/
│   ├── Model/
│   │   ├── EbbinghausCurve.cs
│   │   ├── ReviewItem.cs
│   │   └── ReviewSchedule.cs
│   ├── ViewModel/
│   │   ├── BaseViewModel.cs           # INotifyPropertyChanged + RelayCommand
│   │   ├── MainViewModel.cs
│   │   ├── HomeViewModel.cs
│   │   ├── ToDoListViewModel.cs
│   │   ├── CalendarViewModel.cs
│   │   ├── ReviewSystemViewModel.cs
│   │   └── InformationViewModel.cs
│   └── View/
│       ├── HomeView.{xaml,xaml.cs}
│       ├── ToDoListView.{xaml,xaml.cs}
│       ├── CalendarView.{xaml,xaml.cs}
│       ├── ReviewSystemView.{xaml,xaml.cs}
│       ├── InformationView.{xaml,xaml.cs}
│       └── TodolistReminder.{xaml,xaml.cs}
├── Services/
│   ├── IReviewScheduler.cs
│   ├── ReviewScheduler.cs
│   ├── INotificationService.cs
│   └── NotificationService.cs
└── Theme/
    └── MenuButtonTheme.xaml
```

## Reading guide

Start at `App.xaml.cs` → `MainWindow.xaml.cs` (which hosts a `Frame` driven by
`MainViewModel`). Then read `MVVM/Model/EbbinghausCurve.cs` — that is the
heart of the app. The path from a user adding a study item to a popup
notification is:

```
ToDoListView (XAML button) ─▶ ToDoListViewModel.AddItemCommand
  └─▶ ReviewScheduler.Schedule(item)
        └─▶ EbbinghausCurve.OffsetsFrom(StudiedAt)  // 10m, 1d, 1w, 1m
              └─▶ NotificationService.Schedule(at, item)
                    └─▶ (when fired) opens TodolistReminder window
```

`ReviewSystemViewModel` filters `ReviewItem`s whose next due time is *today*
and feeds them into the `ReviewSystemView` list. `CalendarViewModel` maps
the same set of due times onto Syncfusion `SfScheduler` appointments.

## License

The reconstruction is provided under the same [MIT License](../LICENSE) as
the rest of the archive — a teaching aid, not the original implementation.
