@echo off
REM ================================================================
REM PIANO Multi-Agent Minecraft Mission Launcher
REM ================================================================
REM This script:
REM 1. Verifies MCP server is running
REM 2. Verifies Minecraft is ready on port 9000
REM 3. Calls /mission/start endpoint
REM 4. Opens dashboard for monitoring
REM ================================================================

echo ================================================================
echo    PIANO Multi-Agent Minecraft Mission Launcher
echo ================================================================
echo.

REM Configuration
set MCP_SERVER=http://localhost:8080
set BASE_PORT=9000
set DASHBOARD_URL=http://localhost:8501

REM Step 1: Check if MCP server is running
echo [1/4] Checking MCP Server...
curl -s %MCP_SERVER%/health >nul 2>&1
if errorlevel 1 (
    echo      [ERROR] MCP Server is not running at %MCP_SERVER%
    echo      Please start it first: start_server.bat
    pause
    exit /b 1
)
echo      [OK] MCP Server is running

REM Step 2: Check for running agents
echo.
echo [2/4] Checking for running agents...
curl -s %MCP_SERVER%/agents > temp_agents.json 2>nul
findstr /c:"running" temp_agents.json >nul 2>&1
if errorlevel 1 (
    echo      [WARNING] No running agents found
    echo      Agents may be created but not started
    echo      Start agents via dashboard or API first
    del temp_agents.json 2>nul
    pause
    exit /b 1
)
del temp_agents.json 2>nul
echo      [OK] Running agents found

REM Step 3: Check if Minecraft/Malmo is running
echo.
echo [3/4] Checking Minecraft/Malmo on port %BASE_PORT%...
echo      NOTE: Minecraft must be running with Malmo mod
echo      Command: cd malmo\Minecraft ^&^& launchClient.bat -port %BASE_PORT% -env
echo.

REM Try to connect to Malmo port
powershell -Command "try { $tcp = New-Object System.Net.Sockets.TcpClient('127.0.0.1', %BASE_PORT%); $tcp.Close(); exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    echo      [WARNING] Cannot connect to Malmo on port %BASE_PORT%
    echo.
    echo      Make sure Minecraft is:
    echo        1. Running with the Malmo mod
    echo        2. In a world (not main menu)
    echo        3. Listening on port %BASE_PORT%
    echo.
    set /p CONTINUE="Continue anyway? (y/n): "
    if /i not "%CONTINUE%"=="y" (
        exit /b 1
    )
) else (
    echo      [OK] Malmo port %BASE_PORT% is accessible
)

REM Step 4: Start the mission
echo.
echo [4/4] Starting mission...
echo.

curl -X POST "%MCP_SERVER%/mission/start?base_port=%BASE_PORT%" -H "Content-Type: application/json"
if errorlevel 1 (
    echo.
    echo      [ERROR] Failed to start mission
    pause
    exit /b 1
)

echo.
echo ================================================================
echo    Mission Started!
echo ================================================================
echo.
echo Monitor your agents:
echo   - Dashboard: %DASHBOARD_URL%
echo   - API Status: %MCP_SERVER%/mission/status
echo.
echo To stop the mission:
echo   curl -X POST %MCP_SERVER%/mission/stop
echo   or run: stop_mission.bat
echo.

REM Open dashboard in browser
echo Opening dashboard...
start "" %DASHBOARD_URL%

echo.
echo Press any key to close this window...
pause >nul
