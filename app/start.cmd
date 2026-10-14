@echo off
setlocal
set "PYTHONDONTWRITEBYTECODE=1"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-simulation.ps1" %*
set "APP_EXIT=%ERRORLEVEL%"
if not "%APP_EXIT%"=="0" (
  echo.
  echo The app could not start or exited with an error. See the details above.
  pause
)
exit /b %APP_EXIT%
