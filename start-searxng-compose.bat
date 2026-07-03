@echo off
title SearXNG via Docker Compose
echo Starting SearXNG via Docker Compose...
echo.

REM Check if Docker is installed
where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed or not in PATH.
    echo Please install Docker Desktop from: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Desktop is not running.
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

REM Create config directory if it doesn't exist
if not exist "%~dp0searxng" mkdir "%~dp0searxng"

REM Start with docker-compose
cd /d "%~dp0"
docker-compose -f docker-compose.searxng.yml up -d

echo.
echo SearXNG is starting on http://localhost:8080
echo Wait 10-15 seconds for it to fully start.
echo.
echo To stop: docker-compose -f docker-compose.searxng.yml down
pause
