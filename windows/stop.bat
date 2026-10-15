@echo off
setlocal
:: C.O.R.A - stop (Windows)
:: Ends every process CORA started from THIS project folder (boot sequence, GUI,
:: CLI, stats server), her voice sidecar when CORA launched it (data\run\
:: voice-sidecar.pid; a sidecar started by something else is left alone), and
:: unloads her models from the GPU (Ollama keep_alive 0). Ollama itself stays up.
set "ROOT=%~dp0.."
pushd "%ROOT%" || (echo [!] project root not found & exit /b 1)
echo [CORA] stopping...

:: 1. CORA's own Python processes: command line holds this folder AND one of the entry points
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$root = (Resolve-Path '.').Path;" ^
  "Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe'\" | Where-Object { $c = $_.CommandLine; $c -and $c.Contains($root) -and ($c -match 'boot_sequence\.py|gui_launcher\.py|stats_server\.py|src\\cora\.py|ui\\app\.py|voice\\converse\.py') } | ForEach-Object { Write-Host ('  killing ' + $_.ProcessId + ' ' + $_.CommandLine.Substring(0, [Math]::Min(90, $_.CommandLine.Length))); Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"

:: 2. her voice sidecar, only if CORA started it
if exist "data\run\voice-sidecar.pid" (
  set /p VPID=<"data\run\voice-sidecar.pid"
  powershell -NoProfile -Command "$p = Get-Process -Id %VPID% -ErrorAction SilentlyContinue; if ($p -and $p.ProcessName -like 'python*') { Write-Host ('  stopping voice sidecar pid ' + $p.Id); Stop-Process -Id $p.Id -Force }"
  del /q "data\run\voice-sidecar.pid" 2>nul
)

:: 3. unload her models from the GPU (Ollama stays running)
powershell -NoProfile -Command ^
  "try { $ps = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/ps' -TimeoutSec 3; foreach ($m in $ps.models) { Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:11434/api/generate' -Body (@{model=$m.name; keep_alive=0} | ConvertTo-Json) -ContentType 'application/json' -TimeoutSec 10 | Out-Null; Write-Host ('  unloaded ' + $m.name) } } catch { Write-Host '  ollama not reachable (nothing to unload)' }"

del /q "data\run\started.txt" 2>nul
echo [CORA] stopped.
popd
endlocal
