# 빌드 중간 산출물 (build-artifacts)

이 디렉터리는 Visual Studio가 WPF 프로젝트를 컴파일할 때 생성한 중간 산출물
(`obj/Release/` 폴더의 내용)을 보존한 것입니다. 원본 저장소 구조를 보존하기 위해
삭제하지 않고 옮겨 두었습니다.

## 포함된 파일 종류

- `*.baml` — XAML이 컴파일된 바이너리 마크업
- `*.g.cs`, `*.g.i.cs` — XAML로부터 자동 생성된 C# 코드 (partial class)
- `*.cache`, `*.lref` — MSBuild가 사용하는 캐시
- `Review_Reminder.g.resources` — 임베디드 리소스
- `TempPE/` — 디자인 타임에 사용되는 임시 어셈블리

## 참고

원본 `.xaml` / `.xaml.cs` 소스 파일은 이 저장소에 커밋되어 있지 않습니다.
재컴파일이 필요한 경우, `*.g.cs` 파일의 `#pragma checksum` 헤더에서 원본 파일 경로를
확인할 수 있습니다 (예: `App.xaml`, `MVVM/View/HomeView.xaml`).
