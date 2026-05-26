# 실행 파일 (dist)

이 디렉터리에는 빌드된 Windows 실행 파일이 포함되어 있습니다.

## 파일

- `Review_Reminder.exe` — WPF 기반 데스크톱 애플리케이션 (PE32, .NET Framework)
- `Review_Reminder.pdb` — 디버깅 심볼

## 실행 방법

1. Windows 환경에서 `Review_Reminder.exe`를 다운로드합니다.
2. .NET Framework 4.x 런타임이 설치되어 있어야 합니다 (대부분의 Windows에 기본 포함).
3. 더블 클릭하여 실행합니다.

> 참고: 원본 프로젝트는 Syncfusion WPF 컨트롤과 Microsoft.WindowsAPICodePack 라이브러리에
> 의존합니다. 실행 시 누락된 DLL 오류가 발생하면 해당 런타임 패키지를 추가로 설치해야 할 수 있습니다.
