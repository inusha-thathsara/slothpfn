@echo off
title SlothPFN - Cloudflare Public Tunnel
echo ========================================================
echo   SlothPFN Public Cloudflare Tunnel Launcher
echo ========================================================
echo.
echo Checking if local SlothPFN server is running on port 8000...
netstat -ano | findstr :8000 >nul
if %ERRORLEVEL% NEQ 0 (
    echo [Notice] SlothPFN backend is not currently running.
    echo Starting SlothPFN backend in the background...
    start /b "" ".venv\Scripts\python.exe" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
    timeout /t 3 /nobreak >nul
)

echo.
echo Launching secure HTTPS tunnel via Cloudflare (0 credit cards, 0 signups)...
echo.
tools\cloudflared.exe tunnel --url http://127.0.0.1:8000
pause
