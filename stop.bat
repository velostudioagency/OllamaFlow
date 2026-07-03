@echo off
echo Stopping OllamaFlow servers...
taskkill /FI "WINDOWTITLE eq OllamaFlow Backend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq OllamaFlow Frontend*" /F >nul 2>&1
echo Stopping Firecrawl...
docker compose --profile firecrawl down
echo All servers stopped.
pause
