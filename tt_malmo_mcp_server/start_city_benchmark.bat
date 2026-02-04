@echo off
REM ================================================================
REM City Building Benchmark Launcher
REM ================================================================
REM Launches 3 Qwen agents to build a city in Minecraft
REM with accelerated game speed and spectator mode
REM ================================================================

echo.
echo ================================================================
echo         City Building Benchmark - PIANO Agents
echo ================================================================
echo.

REM Configuration - Edit these as needed
set SPEED=2x
set NUM_AGENTS=3
set MCP_SERVER=http://localhost:8080
set BASE_PORT=9000

echo Configuration:
echo   - Speed: %SPEED% (options: 1x, 2x, 5x, 10x)
echo   - Agents: %NUM_AGENTS%
echo   - Server: %MCP_SERVER%
echo   - Malmo Port: %BASE_PORT%
echo.

REM Activate virtual environment if it exists
if exist "venv_win\Scripts\activate.bat" (
    call venv_win\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Run the benchmark script
python run_city_benchmark.py --speed %SPEED% --agents %NUM_AGENTS% --server %MCP_SERVER% --base-port %BASE_PORT%

echo.
echo Benchmark ended.
pause
