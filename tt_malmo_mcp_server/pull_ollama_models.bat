@echo off
echo ============================================
echo Downloading Ollama Models for Malmo AI
echo ============================================
echo.

REM Check if Ollama is installed
where ollama >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Ollama not found in PATH
    echo Please install from: https://ollama.com/download
    echo.
    pause
    exit /b 1
)

echo Available models:
echo   1. qwen2.5-coder:32b  (~20GB) - Recommended for coding/agents
echo   2. qwen2.5:7b         (~4.5GB) - Fast, lightweight
echo   3. deepseek-r1:70b    (~40GB) - Strong reasoning
echo   4. codestral:22b      (~13GB) - Fast coding
echo.

set /p choice="Enter model number to download (1-4): "

if "%choice%"=="1" (
    echo Downloading qwen2.5-coder:32b...
    ollama pull qwen2.5-coder:32b
) else if "%choice%"=="2" (
    echo Downloading qwen2.5:7b...
    ollama pull qwen2.5:7b
) else if "%choice%"=="3" (
    echo Downloading deepseek-r1:70b...
    ollama pull deepseek-r1:70b
) else if "%choice%"=="4" (
    echo Downloading codestral:22b...
    ollama pull codestral:22b
) else (
    echo Invalid choice.
)

echo.
echo Done! Run start_ollama.bat to start the server.
pause
