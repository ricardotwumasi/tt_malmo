@echo off
echo ============================================
echo Starting Ollama Local LLM Server
echo ============================================
echo.
echo NOTE: Ollama must be installed first from https://ollama.com/download
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

echo Starting Ollama server...
echo.

REM Start Ollama server
ollama serve

pause
