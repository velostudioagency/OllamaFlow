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

echo Starting Firecrawl on http://localhost:3001 ...
where docker >nul 2>&1
if %errorlevel% equ 0 (
    echo Using Docker for Firecrawl...
    docker compose --profile firecrawl up -d redis firecrawl
    timeout /t 5 /nobreak >nul
) else (
    echo.
    echo [WARNING] Docker not found. Firecrawl requires Docker to run.
    echo Install Docker Desktop: https://www.docker.com/products/docker-desktop/
    echo.
    echo Workflows using Firecrawl will fail until Docker is installed.
    echo.
)

echo Starting backend on http://localhost:8000 ...
start "OllamaFlow Backend" cmd /k "cd backend && venv\Scripts\activate && python ..\ollamaflow_cli.py serve --port 8000"

timeout /t 3 /nobreak >nul

echo Starting frontend on http://localhost:5173 ...
start "OllamaFlow Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ============================================
echo   OllamaFlow is running!
echo ============================================
echo   Backend:   http://localhost:8000
echo   Frontend:  http://localhost:5173
echo   Firecrawl: http://localhost:3001
echo ============================================
echo.
echo   CLI Usage:
echo     python ollamaflow_cli.py list
echo     python ollamaflow_cli.py run "Workflow Name" --input "text"
echo     python ollamaflow_cli.py models
echo     python ollamaflow_cli.py tools
echo.
echo Close this window or press Ctrl+C to stop.
pause
