@echo off
title SearXNG Search Engine Server
echo Starting SearXNG Search Engine...
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

REM Pull and run SearXNG
echo Pulling SearXNG image...
docker pull searxng/searxng:latest

echo Starting SearXNG on port 8080...
docker run -d ^
    --name searxng ^
    -p 8080:8080 ^
    -e SEARXNG_BASE_URL=http://localhost:8080/ ^
    -e SEARXNG_SECRET_KEY=ollamaflow-search-secret ^
    --restart unless-stopped ^
    searxng/searxng:latest

echo.
echo SearXNG is starting...
echo Wait 10-15 seconds, then open: http://localhost:8080
echo.
echo To stop: docker stop searxng
echo To remove: docker rm -f searxng
pause
