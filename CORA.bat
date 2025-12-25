@echo off
chcp 437 >nul
title C.O.R.A - Cognitive Operations & Reasoning Assistant
color 0D

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

:: Check dolphin-mistral (main chat model - uncensored, follows instructions)
ollama list | findstr /i "dolphin-mistral" >nul 2>&1
if errorlevel 1 (
    echo [DOWNLOAD] dolphin-mistral:7b ^(main chat model - ~4.1GB^)...
    echo          This is CORA's brain - may take several minutes...
    ollama pull dolphin-mistral:7b
    if errorlevel 1 (
        echo [WARN] Failed to download dolphin-mistral:7b
    ) else (
        echo [OK] dolphin-mistral:7b ready
    )
) else (
    echo         dolphin-mistral - OK
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

:: Check qwen2.5-coder (coding model - best for 2024)
ollama list | findstr /i "qwen2.5-coder" >nul 2>&1
if errorlevel 1 (
    echo [DOWNLOAD] qwen2.5-coder:7b ^(coding model - ~4.4GB^)...
    echo          This is for code writing/editing...
    ollama pull qwen2.5-coder:7b
    if errorlevel 1 (
        echo [WARN] Failed to download qwen2.5-coder
    ) else (
        echo [OK] qwen2.5-coder ready
    )
) else (
    echo         qwen2.5-coder - OK
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
