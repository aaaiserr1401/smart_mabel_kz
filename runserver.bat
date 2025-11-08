@echo off
setlocal

REM Change to the directory of this script (project root)
cd /d %~dp0

REM Path to your user-level virtual environment Python
set "VENV_PY=C:\Users\aiser\.venv\Scripts\python.exe"

if not exist "%VENV_PY%" (
  echo [ERROR] Python in virtual environment not found at: %VENV_PY%
  echo Please create/repair venv or update path inside runserver.bat
  exit /b 1
)

REM Optional: ensure dependencies are installed/updated
"%VENV_PY%" -m pip install -r requirements.txt >NUL 2>&1

REM Run the Flask app
"%VENV_PY%" app.py

endlocal
