@echo off
title Install SlothPFN Context Menu
cd /d "%~dp0\.."
echo [SlothPFN] Installing Right-Click 'Analyze with SlothPFN' to Windows Explorer...
.\.venv\Scripts\python.exe tools\install_context_menu.py
echo.
pause
