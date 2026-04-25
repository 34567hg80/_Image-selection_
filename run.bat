@echo off
setlocal

:: Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found. 
    echo Please ensure you are in the project root and venv is installed.
    pause
    exit /b 1
)

echo [SYSTEM] Activating virtual environment...
call venv\Scripts\activate.bat

echo [SYSTEM] Launching Image Selector...
python app.py

echo.
echo [SYSTEM] Application finished.
pause
