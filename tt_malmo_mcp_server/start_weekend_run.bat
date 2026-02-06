@echo off
REM ================================================================
REM Weekend Supervisor Launcher
REM ================================================================
REM Starts the autonomous benchmark watchdog that monitors and
REM auto-restarts Ollama, MCP server, and agent missions.
REM
REM Prerequisites:
REM   - Minecraft instances running on ports 9000, 9001, 9002
REM   - Ollama installed with qwen2.5-coder:32b model pulled
REM   - Windows Update auto-restart disabled on the VM
REM ================================================================

echo.
echo ================================================================
echo         Weekend Supervisor - Autonomous Benchmark Watchdog
echo ================================================================
echo.
echo Configuration:
echo   - Speed:          2x
echo   - Agents:         3
echo   - Time limit:     60 hours
echo   - Check interval: 60 seconds
echo.
echo Press Ctrl+C to stop gracefully.
echo.

REM Activate virtual environment
if exist "%~dp0venv_win\Scripts\activate.bat" (
    call "%~dp0venv_win\Scripts\activate.bat"
) else if exist "%~dp0venv\Scripts\activate.bat" (
    call "%~dp0venv\Scripts\activate.bat"
)

REM Run the weekend supervisor
python weekend_supervisor.py --speed 2x --agents 3 --time-limit 60 --check-interval 60

echo.
echo Weekend supervisor ended.
pause
