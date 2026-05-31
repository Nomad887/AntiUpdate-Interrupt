@echo off
>nul 2>&1 net session
if %errorLevel% neq 0 (
    echo Request for administrator rights...
    powershell start -verb runas '%0'
    exit /b
)

cd /d %~dp0
powershell -ExecutionPolicy Bypass -Command "$pause = (Get-Date).AddDays(35); $pause = $pause.ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'); Set-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings' -Name 'PauseUpdatesExpiryTime' -Value $pause"

echo Done! The update pause is set to 35 days.
pause