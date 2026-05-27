# archive/ — original 2021 WPF artifacts (not used by the modern app)

This folder holds what survived from the **original 2021 project**: a Windows
WPF / .NET Framework C# app whose `.cs` / `.xaml` / `.csproj` / `.sln` source
files were never committed.

The modern Python rewrite at the repository root is a **clean-room
reimplementation**, not a port. None of the code in this folder is executed
or imported by the current package. It is kept here purely as historical
record of what existed before.

## What's here

```
archive/
├── dist/                              # compiled binary (cannot run standalone)
│   ├── Review_Reminder.exe            # PE32 (x86) .NET assembly, 396 KB
│   ├── Review_Reminder.pdb            # debug symbols
│   └── README.md
└── build-artifacts/
    └── obj-Release/                   # XAML → BAML compile output + MSBuild cache
        ├── App.{baml,g.cs,g.i.cs}
        ├── MainWindow.{baml,g.cs,g.i.cs}
        ├── MVVM/View/*.{baml,g.cs}
        ├── Theme/MenuButtonTheme.baml
        ├── TempPE/Properties.Resources.Designer.cs.dll
        ├── *.cache / *.lref           # MSBuild caches
        └── Review_Reminder.csproj.FileListAbsolute.txt
```

## Why it can't be run as-is

`dist/Review_Reminder.exe` is missing its seven runtime DLLs:

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

Syncfusion is a commercial library that also requires a license key. Without
all seven DLLs at matching versions in the same folder, the binary crashes
immediately on launch.

## What the original app was meant to do

A Windows desktop reminder app organized around the Ebbinghaus forgetting
curve: register a study item, get review notifications at curve-aligned
intervals. The modern Python rewrite covers the same intent without the
Windows / Syncfusion lock-in — see the repository root `README.md`.

The original demo lives at: <https://www.youtube.com/watch?v=J2nf1r5jZrI>
