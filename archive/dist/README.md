# 실행 파일 (dist)

> [!WARNING]
> **이 폴더만으로는 실행되지 않습니다.** 의존 DLL 7개가 동봉되어 있지 않습니다.

## 파일

- `Review_Reminder.exe` — WPF 데스크톱 애플리케이션 (PE32 x86, .NET Framework 4.x assembly, 396 KB)
- `Review_Reminder.pdb` — 디버깅 심볼

## 직접 실행을 시도하려면

`Review_Reminder.exe` 를 더블 클릭하면 즉시 `FileNotFoundException` 으로 죽습니다. 다음 DLL 7개를 같은 폴더에 직접 가져와야 합니다:

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

- **Microsoft.WindowsAPICodePack.\*** 은 NuGet 또는 [archive.codeplex.com](https://archive.codeplex.com/) 에서 받을 수 있습니다.
- **Syncfusion.\*** 은 [Syncfusion Community License](https://www.syncfusion.com/products/communitylicense) (개인/소규모는 무료) 또는 유료 라이선스가 필요하고, NuGet 으로 설치합니다. 라이선스 키 등록(`SfSkinManager`/`Licensing`) 없이는 워터마크가 표시됩니다.

정확한 버전은 상위 폴더의 `build-artifacts/obj-Release/Review_Reminder.csproj.FileListAbsolute.txt` 에서 확인하세요.

## 호환성

- 아키텍처: x86 (32-bit). 64-bit only 환경에서는 32-bit 호환 모드가 필요합니다.
- 런타임: .NET Framework 4.x (대부분의 Windows 10 이상에 기본 포함).

## 재컴파일

`.csproj` / `.cs` / `.xaml` 원본 소스가 본 저장소에 보존되어 있지 않아 재컴파일은 불가능합니다. 원본은 [작성자](https://github.com/jumincho)에게 문의하세요.
