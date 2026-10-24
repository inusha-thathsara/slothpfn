@echo off
title Uninstall SlothPFN Context Menu
cd /d "%~dp0\.."
echo [SlothPFN] Removing Context Menu from Windows Explorer...
.\.venv\Scripts\python.exe tools\install_context_menu.py --uninstall
echo.
pause
