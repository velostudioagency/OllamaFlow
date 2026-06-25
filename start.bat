@echo off
echo ============================================
echo   OllamaFlow - Starting Servers
echo ============================================
echo.

:: Check if dependencies are installed
if not exist "backend\venv" (
    echo Virtual environment not found. Run install.bat first.
    pause
    exit /b 1
)

echo Starting backend on http://localhost:8000 ...
start "OllamaFlow Backend" cmd /k "cd backend && venv\Scripts\activate && uvicorn main:app --reload --port 8000"

timeout /t 3 /nobreak >nul

echo Starting frontend on http://localhost:5173 ...
start "OllamaFlow Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ============================================
echo   OllamaFlow is running!
echo ============================================
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo ============================================
echo.
echo Close this window or press Ctrl+C to stop.
pause
