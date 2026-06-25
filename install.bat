@echo off
echo ============================================
echo   OllamaFlow - Dependency Installation
echo ============================================
echo.

echo [1/4] Creating Python virtual environment...
cd backend
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment. Make sure Python is installed.
    pause
    exit /b 1
)

echo [2/4] Installing Python dependencies...
call venv\Scripts\activate
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies.
    pause
    exit /b 1
)
cd ..

echo [3/4] Installing frontend dependencies...
cd frontend
call npm install
if errorlevel 1 (
    echo ERROR: Failed to install frontend dependencies. Make sure Node.js is installed.
    pause
    exit /b 1
)
cd ..

echo.
echo ============================================
echo   Installation Complete!
echo ============================================
echo.
echo Run 'start.bat' to launch OllamaFlow.
echo.
pause
