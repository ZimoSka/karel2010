@echo off
cd /d "%~dp0"
python karel2010.py
if errorlevel 1 (
    echo.
    echo Chyba! Je nainstalovany Python?
    echo Stiahni ho z: https://python.org
    pause
)
