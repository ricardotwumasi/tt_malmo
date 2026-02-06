@echo off
echo ============================================
echo Starting Malmo AI Benchmark MCP Server
echo ============================================

REM Activate virtual environment
call "%~dp0venv_win\Scripts\activate.bat"

REM Load environment variables from .env
for /f "tokens=1,2 delims==" %%a in ('type "%~dp0.env" ^| findstr /v "^#" ^| findstr /v "^$"') do (
    set "%%a=%%b"
)

echo.
echo Starting server on port %MCP_SERVER_PORT%...
echo.

python -m uvicorn mcp_server.server:app --host %MCP_SERVER_HOST% --port %MCP_SERVER_PORT%

pause
