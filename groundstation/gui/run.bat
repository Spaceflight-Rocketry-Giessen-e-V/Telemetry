@echo off
echo === Python Project Setup ===

REM Define the fallback Python 3.12 path (generic for any user)
set PYTHON312=%LOCALAPPDATA%\Programs\Python\Python312\python.exe

REM Check if Python in PATH is version 3.12
set PYTHON_CMD=python
python --version >nul 2>&1
if errorlevel 1 goto try_fallback

REM Get version string and check for 3.12
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo Found in PATH: Python %PY_VER%

REM Check if version starts with 3.12
echo %PY_VER% | findstr /b "3.12" >nul
if errorlevel 1 goto try_fallback
echo Python 3.12 confirmed in PATH.
goto setup

:try_fallback
echo Python 3.12 not found in PATH. Trying fallback location...
if exist "%PYTHON312%" (
    set PYTHON_CMD=%PYTHON312%
    for /f "tokens=2" %%v in ('"%PYTHON312%" --version 2^>^&1') do set PY_VER=%%v
    echo Found fallback: Python %PY_VER%
    goto setup
)

echo [ERROR] Python 3.12 not found in PATH or at:
echo         %LOCALAPPDATA%\Programs\Python\Python312\python.exe
echo Please install Python 3.12 and try again.
pause
exit /b 1

:setup
REM Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    "%PYTHON_CMD%" -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo Virtual environment already exists.
)

REM Activate venv
echo Activating virtual environment...
call venv\Scripts\activate

REM Upgrade pip inside venv
echo Upgrading pip...
python -m pip install --upgrade pip --quiet

REM Install requirements if file exists
if exist requirements.txt (
    echo Installing requirements...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install requirements.
        pause
        exit /b 1
    )
) else (
    echo [WARNING] No requirements.txt found, skipping install.
)

REM Run the script
echo.
echo === Running main.py ===
python main.py
if errorlevel 1 (
    echo.
    echo [ERROR] Script exited with an error.
)

pause