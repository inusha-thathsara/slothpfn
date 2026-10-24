@echo off
title SlothPFN - Zero-Effort Ambient AI Suite
cd /d "%~dp0"

echo =====================================================================
echo           ^|  \__  ^|  ^|   _ \__  ^| ^| ^|
echo           ^|  / _` ^|  ^|  (   / _` ^| ^|_^|
echo          \__/\__,_/__/ \___/\__,_/\__^|   SlothPFN Ambient Suite
echo =====================================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found at .venv!
    echo Please run: python -m venv .venv ^&^& .\.venv\Scripts\pip.exe install -r requirements.txt
    pause
    exit /b 1
)

:: Ensure drop_data directory exists
if not exist "drop_data" (
    mkdir drop_data
)

:: Check if server is already running on port 8000
netstat -ano | findstr :8000 >nul 2>&1
if %errorlevel% neq 0 (
    echo [SlothPFN] Launching FastAPI backend server on http://127.0.0.1:8000 ...
    start "SlothPFN Server" /min .\.venv\Scripts\python.exe -m uvicorn backend.main:app --port 8000
    timeout /t 2 /nobreak >nul
) else (
    echo [SlothPFN] Web server is already active on http://127.0.0.1:8000.
)

:: Start Tray Agent & Ambient Watcher in background
echo [SlothPFN] Launching System Tray Agent & Ambient Folder Watchdog...
start "Sloth Tray Agent" /min .\.venv\Scripts\python.exe backend\tray_agent.py

:: Open browser
echo [SlothPFN] Opening dashboard in your default browser...
start http://127.0.0.1:8000

echo.
echo =====================================================================
echo   [OK] SlothPFN is running quietly in the background!
echo   * System Tray: Look for the sloth icon in your Windows taskbar tray.
echo   * Auto-Watch: Drop any CSV into "%~dp0drop_data" for zero-click AI.
echo   * Right-Click: Right-click any .csv in Explorer -> "Analyze with SlothPFN"
echo   * Voice AI: Toggle 'Hey Sloth' Wake on http://127.0.0.1:8000
echo =====================================================================
echo.
echo Press any key to close this launcher window (Sloth will stay alive in tray).
pause >nul
