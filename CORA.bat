@echo off
chcp 437 >nul 2>&1
title C.O.R.A - Cognitive Operations & Reasoning Assistant
color 0D

:: Change to the script's directory (handles spaces in path)
cd /d "%~dp0"

:: Find Ollama - check common locations and add to PATH
set "OLLAMA_EXE="

:: Check if already in PATH
where ollama.exe >nul 2>&1
if not errorlevel 1 (
    for /f "delims=" %%i in ('where ollama.exe 2^>nul') do set "OLLAMA_EXE=%%i"
    goto :found_ollama
)

:: Check common install locations
if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
    set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
    set "PATH=%LOCALAPPDATA%\Programs\Ollama;%PATH%"
    goto :found_ollama
)
if exist "%ProgramFiles%\Ollama\ollama.exe" (
    set "OLLAMA_EXE=%ProgramFiles%\Ollama\ollama.exe"
    set "PATH=%ProgramFiles%\Ollama;%PATH%"
    goto :found_ollama
)
if exist "%ProgramFiles(x86)%\Ollama\ollama.exe" (
    set "OLLAMA_EXE=%ProgramFiles(x86)%\Ollama\ollama.exe"
    set "PATH=%ProgramFiles(x86)%\Ollama;%PATH%"
    goto :found_ollama
)
if exist "%USERPROFILE%\Ollama\ollama.exe" (
    set "OLLAMA_EXE=%USERPROFILE%\Ollama\ollama.exe"
    set "PATH=%USERPROFILE%\Ollama;%PATH%"
    goto :found_ollama
)

:found_ollama

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
if "%OLLAMA_EXE%"=="" (
    echo [ERROR] Ollama not found!
    echo.
    echo Please install Ollama from: https://ollama.com
    echo.
    pause
    exit /b 1
)
echo         Found: %OLLAMA_EXE%
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

:: Always check/install yt-dlp for YouTube functionality
echo [CHECK] yt-dlp (YouTube downloader)...
pip show yt-dlp >nul 2>&1
if errorlevel 1 (
    echo         Installing yt-dlp...
    pip install yt-dlp -q
    echo         yt-dlp installed
) else (
    echo         yt-dlp - OK
)

:: Check for mpv (media player for YouTube)
echo [CHECK] mpv media player...
set "MPV_FOUND="

:: First check if mpv is in PATH
where mpv >nul 2>&1
if not errorlevel 1 (
    echo         mpv - OK ^(in PATH^)
    set "MPV_FOUND=1"
    goto :mpv_done
)

:: Check if mpv exists anywhere in tools folder (any subfolder structure)
if exist "tools" (
    for /r "tools" %%f in (mpv.exe) do (
        if exist "%%f" (
            echo         mpv - OK ^(found: %%~dpf^)
            set "PATH=%%~dpf;%PATH%"
            set "MPV_FOUND=1"
            goto :mpv_done
        )
    )
)

:: mpv not found anywhere - set flag for Python modal
if not defined MPV_FOUND (
    echo         [WARN] mpv not found - YouTube playback limited
    set "MPV_MISSING=1"
)

:mpv_done

:: Make sure Ollama is running
echo [CHECK] Ollama service...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo         Starting Ollama service...
    start "" /min "%OLLAMA_EXE%" serve
    timeout /t 5 /nobreak >nul
    :: Verify it started
    curl -s http://localhost:11434/api/tags >nul 2>&1
    if errorlevel 1 (
        echo [WARN] Ollama service may still be starting...
        timeout /t 3 /nobreak >nul
    )
)
echo         Ollama service running
echo.

echo ======================================================
echo.
echo [LAUNCH] Starting C.O.R.A Boot Sequence...
echo.

:: Launch boot sequence with dependency status
python src\boot_sequence.py --mpv-missing=%MPV_MISSING%

if errorlevel 1 (
    echo.
    echo [ERROR] C.O.R.A exited with an error
    pause
)
