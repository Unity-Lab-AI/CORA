@echo off
chcp 437 >nul
title C.O.R.A - Cognitive Operations & Reasoning Assistant
color 0D

echo.
echo   +=========================================+
echo   :   ____  ___  ____   _                   :
echo   :  / ___]/ _ \[  _ \ / \                  :
echo   : [ [__ [ [ ] ][ ][_][ o ]                :
echo   : [ [__ [ [ ] ][ _ / /   \                :
echo   :  \___] \___/[_] [_]_] [_]               :
echo   :                                         :
echo   :  Cognitive Operations ^& Reasoning       :
echo   :  Assistant - v2.4.0 - Unity AI Lab      :
echo   +=========================================+
echo.

:: Check Python
echo [CHECK] Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python 3.10+ from python.org
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo         Found Python %%i
echo.

:: Check Ollama
echo [CHECK] Ollama...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Ollama not found!
    echo.
    echo Installing Ollama...
    winget install Ollama.Ollama
    if errorlevel 1 (
        echo [ERROR] Failed to install Ollama
        echo Please install manually from: https://ollama.com
        pause
        exit /b 1
    )
    echo [OK] Ollama installed. Starting service...
    start "" ollama serve
    timeout /t 5 /nobreak >nul
)
echo         Ollama is installed
echo.

:: Check/Pull required models
echo [CHECK] AI Models...
echo.

:: Check llama3.2 (chat model)
ollama list | findstr /i "llama3.2" >nul 2>&1
if errorlevel 1 (
    echo [DOWNLOAD] llama3.2 ^(chat model - ~2GB^)...
    echo          This may take a few minutes...
    ollama pull llama3.2
    if errorlevel 1 (
        echo [WARN] Failed to download llama3.2
    ) else (
        echo [OK] llama3.2 ready
    )
) else (
    echo         llama3.2 - OK
)

:: Check llava (vision model)
ollama list | findstr /i "llava" >nul 2>&1
if errorlevel 1 (
    echo [DOWNLOAD] llava ^(vision model - ~4.7GB^)...
    echo          This may take several minutes...
    ollama pull llava
    if errorlevel 1 (
        echo [WARN] Failed to download llava
    ) else (
        echo [OK] llava ready
    )
) else (
    echo         llava - OK
)
echo.

:: Check if first run - install Python deps
if not exist "data\.setup_complete" (
    echo [SETUP] First run - installing Python dependencies...
    echo.
    pip install -r requirements.txt
    if not exist "data" mkdir data
    echo. > data\.setup_complete
    echo.
    echo [OK] Dependencies installed
    echo.
)

:: Make sure Ollama is running
echo [CHECK] Ollama service...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo         Starting Ollama service...
    start "" /min ollama serve
    timeout /t 3 /nobreak >nul
)
echo         Ollama service running
echo.

echo ======================================================
echo.
echo [LAUNCH] Starting C.O.R.A Boot Sequence...
echo.

:: Launch boot sequence (not GUI launcher)
python src\boot_sequence.py

if errorlevel 1 (
    echo.
    echo [ERROR] C.O.R.A exited with an error
    pause
)
