@echo off
echo ============================================
echo   OllamaFlow - Restarting Servers
echo ============================================
echo.

echo Stopping existing servers...
taskkill /FI "WINDOWTITLE eq OllamaFlow Backend" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq OllamaFlow Frontend" /F >nul 2>&1

for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173 ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1

timeout /t 2 /nobreak >nul

echo Starting backend on http://localhost:8000 ...
start "OllamaFlow Backend" cmd /k "cd backend && venv\Scripts\activate && uvicorn main:app --reload --port 8000"

timeout /t 3 /nobreak >nul

echo Starting frontend on http://localhost:5173 ...
start "OllamaFlow Frontend" cmd /k "cd frontend && npm run dev"

timeout /t 3 /nobreak >nul

echo Opening http://localhost:5173 in browser...
start http://localhost:5173

echo.
echo ============================================
echo   OllamaFlow is running!
echo ============================================
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo ============================================
