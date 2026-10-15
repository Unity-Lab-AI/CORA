#!/usr/bin/env bash
# C.O.R.A - stop (Linux / macOS)
# Ends every process CORA started from THIS project folder (boot sequence, GUI,
# CLI, stats server), her voice sidecar when CORA launched it (data/run/
# voice-sidecar.pid; one started by something else is left alone), and unloads
# her models from the GPU (Ollama keep_alive 0). Ollama itself stays up.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
echo "[CORA] stopping..."

# 1. CORA's own Python processes: command line holds this folder AND an entry point
for pid in $(pgrep -f "boot_sequence.py|gui_launcher.py|stats_server.py|src/cora.py|ui/app.py|voice/converse.py" 2>/dev/null); do
  if tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null | grep -q -F "$ROOT"; then
    echo "  killing $pid $(tr '\0' ' ' < /proc/$pid/cmdline | cut -c1-90)"
    kill "$pid" 2>/dev/null
  fi
done
sleep 2
for pid in $(pgrep -f "boot_sequence.py|gui_launcher.py|stats_server.py|src/cora.py|ui/app.py|voice/converse.py" 2>/dev/null); do
  if tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null | grep -q -F "$ROOT"; then
    kill -9 "$pid" 2>/dev/null && echo "  force-killed $pid"
  fi
done

# 2. her voice sidecar, only if CORA started it
if [ -f data/run/voice-sidecar.pid ]; then
  VPID="$(cat data/run/voice-sidecar.pid)"
  if [ -n "$VPID" ] && kill -0 "$VPID" 2>/dev/null && tr '\0' ' ' < "/proc/$VPID/cmdline" 2>/dev/null | grep -q "serve.py"; then
    echo "  stopping voice sidecar pid $VPID"; kill "$VPID" 2>/dev/null
  fi
  rm -f data/run/voice-sidecar.pid
fi

# 3. unload her models from the GPU (Ollama stays running)
if command -v curl >/dev/null 2>&1; then
  for m in $(curl -s --max-time 3 http://127.0.0.1:11434/api/ps | python3 -c 'import sys,json
try:
    print(" ".join(x["name"] for x in json.load(sys.stdin).get("models", [])))
except Exception:
    pass' 2>/dev/null); do
    curl -s --max-time 10 http://127.0.0.1:11434/api/generate -d "{\"model\":\"$m\",\"keep_alive\":0}" >/dev/null && echo "  unloaded $m"
  done
fi

rm -f data/run/started.txt
echo "[CORA] stopped."
