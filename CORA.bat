@echo off
chcp 437 >nul 2>&1
title C.O.R.A - Cognitive Operations & Reasoning Assistant
color 0D
setlocal EnableExtensions EnableDelayedExpansion

:: Change to the script's directory (handles spaces in path)
cd /d "%~dp0"

echo.
echo   +=========================================+
echo   :   ____  ___  ____   _                   :
echo   :  / ___]/ _ \[  _ \ / \                  :
echo   : [ [__ [ [ ] ][ ][_][ o ]                :
echo   : [ [__ [ [ ] ][ _ / /   \                :
echo   :  \___] \___/[_] [_]_] [_]               :
echo   :                                         :
echo   :  Cognitive Operations and Reasoning      :
echo   :  Assistant - v3.0.0 - Unity AI Lab      :
echo   +=========================================+
echo.

:: ---------------------------------------------------------------------------
:: Python: 3.13 preferred (installed 2026-10-14), then 3.12, then whatever
:: `python` is on PATH (with a warning; 3.10 is end-of-life).
:: ---------------------------------------------------------------------------
echo [CHECK] Python...
set "BASE_PY="
py -3.13 -c "import sys" >nul 2>&1
if not errorlevel 1 (
    set "BASE_PY=py -3.13"
    goto :py_found
)
py -3.12 -c "import sys" >nul 2>&1
if not errorlevel 1 (
    set "BASE_PY=py -3.12"
    goto :py_found
)
if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    set "BASE_PY=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    goto :py_found
)
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "BASE_PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    goto :py_found
)
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.13 from https://www.python.org/downloads/
    pause
    exit /b 1
)
set "BASE_PY=python"
echo         [WARN] Python 3.13/3.12 not found - using default python ^(may be end-of-life 3.10^)
:py_found
for /f "tokens=2" %%i in ('%BASE_PY% --version 2^>^&1') do echo         Found Python %%i
echo.

:: ---------------------------------------------------------------------------
:: Virtual environment in .venv (created once, re-used). Dependencies are
:: (re)installed whenever requirements.txt changes (hash stored in .venv).
:: ---------------------------------------------------------------------------
set "VENV_PY=%~dp0.venv\Scripts\python.exe"
if not exist "%VENV_PY%" (
    echo [SETUP] Creating virtual environment in .venv ...
    %BASE_PY% -m venv ".venv"
    if errorlevel 1 (
        echo [ERROR] Could not create the virtual environment.
        pause
        exit /b 1
    )
    "%VENV_PY%" -m pip install -q --upgrade pip
)

set "REQ_HASH="
for /f "skip=1 tokens=1" %%h in ('certutil -hashfile requirements.txt SHA256 2^>nul') do (
    if not defined REQ_HASH set "REQ_HASH=%%h"
)
set "OLD_HASH="
if exist ".venv\requirements.sha256" set /p OLD_HASH=<".venv\requirements.sha256"
if /i not "%REQ_HASH%"=="%OLD_HASH%" (
    echo [SETUP] Installing / updating Python dependencies ^(requirements.txt changed^)...
    "%VENV_PY%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [WARN] Some dependencies failed to install. CORA will run with reduced features.
    ) else (
        >".venv\requirements.sha256" echo %REQ_HASH%
        echo [OK] Dependencies installed
    )
    echo.
)

:: ---------------------------------------------------------------------------
:: .env (API keys). Weather and news are keyless; only Pollinations + GitHub
:: are read by the code.
:: ---------------------------------------------------------------------------
echo [CHECK] Environment Configuration...
if not exist ".env" (
    echo         [WARN] .env not found - copy env.example to .env for image generation + GitHub features
) else (
    findstr /i "POLLINATIONS_API_KEY=" ".env" | findstr /v "your_" >nul 2>&1
    if errorlevel 1 (echo         [WARN] Pollinations API key missing - image generation limited) else (echo         Pollinations API - OK)
    findstr /i "GITHUB_TOKEN=" ".env" | findstr /v "your_" >nul 2>&1
    if errorlevel 1 (echo         [WARN] GitHub token missing - git features limited) else (echo         GitHub Token - OK)
)
echo.

:: ---------------------------------------------------------------------------
:: Ollama + configured models + yt-dlp + Playwright + unity-voice-v2 sidecar.
:: All model names come from config/config.json (ai.settings).
:: ---------------------------------------------------------------------------
echo [CHECK] Ollama, models, media tools, voice...
"%VENV_PY%" scripts\bootstrap.py
echo.

:: ---------------------------------------------------------------------------
:: mpv (YouTube playback): PATH or anywhere under tools\
:: ---------------------------------------------------------------------------
echo [CHECK] mpv media player...
set "MPV_MISSING="
where mpv >nul 2>&1
if not errorlevel 1 (
    echo         mpv - OK ^(in PATH^)
    goto :mpv_done
)
if exist "tools" (
    for /r "tools" %%f in (mpv.exe) do (
        if exist "%%f" (
            echo         mpv - OK ^(found: %%~dpf^)
            set "PATH=%%~dpf;!PATH!"
            goto :mpv_done
        )
    )
)
echo         [WARN] mpv not found - YouTube playback limited
set "MPV_MISSING=1"
:mpv_done
echo.

echo ======================================================
echo.
echo [LAUNCH] Starting C.O.R.A Boot Sequence...
echo          Web UI is served by CORA at http://127.0.0.1:11435/ once booted.
echo.

"%VENV_PY%" src\boot_sequence.py --mpv-missing=%MPV_MISSING%

if errorlevel 1 (
    echo.
    echo [ERROR] C.O.R.A exited with an error
    pause
)
endlocal
