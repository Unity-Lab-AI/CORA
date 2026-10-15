@echo off
setlocal
:: C.O.R.A - start (Windows)
:: Same job as CORA.bat at the project root: Python 3.13/3.12 venv, requirements,
:: bootstrap (Ollama + configured models, yt-dlp, Playwright, her voice sidecar),
:: then the boot sequence. Run stop.bat to end everything it started.
set "ROOT=%~dp0.."
pushd "%ROOT%" || (echo [!] project root not found & exit /b 1)
if not exist "data\run" mkdir "data\run"
echo %DATE% %TIME% start.bat > "data\run\started.txt"
call "%ROOT%\CORA.bat" %*
set "RC=%ERRORLEVEL%"
popd
endlocal & exit /b %RC%
