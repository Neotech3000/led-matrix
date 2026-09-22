@echo off
setlocal
cd /d "%~dp0\.."
where py >nul 2>&1
if %ERRORLEVEL%==0 (
  py -3 -m matrix_deck --gui --host 127.0.0.1 --port 43173 %*
  exit /b %ERRORLEVEL%
)
python -m matrix_deck --gui --host 127.0.0.1 --port 43173 %*
