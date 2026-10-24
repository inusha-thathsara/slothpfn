@echo off
title Stop SlothPFN Ambient Processes
cd /d "%~dp0\.."

echo [SlothPFN] Stopping background Sloth services...

:: Stop python processes running backend/tray_agent.py or uvicorn
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*tray_agent.py*' -or ($_.CommandLine -like '*uvicorn*' -and $_.CommandLine -like '*backend.main:app*') } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue; Write-Host ('Stopped PID: ' + $_.ProcessId) }"

echo [SlothPFN] Done! Sloth is taking a well-deserved nap.
timeout /t 2 /nobreak >nul
