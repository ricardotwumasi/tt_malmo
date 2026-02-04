@echo off
REM ================================================================
REM PIANO Mission Stopper
REM Stops the current Malmo mission and disconnects agents
REM ================================================================

echo ================================================================
echo    Stopping PIANO Minecraft Mission
echo ================================================================
echo.

set MCP_SERVER=http://localhost:8080

echo Sending stop request to MCP server...
curl -X POST %MCP_SERVER%/mission/stop
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to stop mission
    echo Server may not be running or no mission is active
) else (
    echo.
    echo [OK] Mission stopped
    echo Agents are now in thinking-only mode
)

echo.
pause
