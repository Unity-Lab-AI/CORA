@echo off
title C.O.R.A - Cognitive Operations & Reasoning Assistant
color 0A

echo.
echo   ██████╗ ██████╗ ██████╗  █████╗
echo  ██╔════╝██╔═══██╗██╔══██╗██╔══██╗
echo  ██║     ██║   ██║██████╔╝███████║
echo  ██║     ██║   ██║██╔══██╗██╔══██║
echo  ╚██████╗╚██████╔╝██║  ██║██║  ██║
echo   ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝
echo.
echo  Cognitive Operations ^& Reasoning Assistant
echo  Version 2.3.0 - Unity AI Lab
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python 3.10+ from python.org
    pause
    exit /b 1
)

:: Check if first run - install deps
if not exist "data\.setup_complete" (
    echo [SETUP] First run - installing dependencies...
    pip install -r requirements.txt
    echo. > data\.setup_complete
)

echo Starting C.O.R.A...
echo.

:: Launch GUI
python src\gui_launcher.py

if errorlevel 1 (
    echo.
    echo [ERROR] C.O.R.A exited with an error
    pause
)
