@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py skills\yuntu-media-research\scripts\configure_key.py
) else (
  python skills\yuntu-media-research\scripts\configure_key.py
)
echo.
if %errorlevel%==0 (
  echo Configuration completed. You can now run RedFox collection.
) else (
  echo Configuration failed. Check that Python is installed.
)
pause
