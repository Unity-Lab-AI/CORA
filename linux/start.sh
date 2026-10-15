#!/usr/bin/env bash
# C.O.R.A - start (Linux / macOS)
# Python 3.13/3.12 venv, requirements, bootstrap (Ollama + configured models,
# yt-dlp, Playwright, her voice sidecar when a torch Python is available), then
# the boot sequence. Run stop.sh to end everything it started.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
mkdir -p data/run

# interpreter: newest 3.13 / 3.12 on PATH
PY=""
for c in python3.13 python3.12 python3; do
  if command -v "$c" >/dev/null 2>&1; then
    v="$("$c" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
    case "$v" in 3.13|3.12) PY="$c"; break;; esac
  fi
done
if [ -z "$PY" ]; then
  echo "[!] Python 3.12 or 3.13 is required (found: $(python3 --version 2>&1 || echo none))"; exit 1
fi

# venv + requirements (re-installed when requirements.txt changes)
if [ ! -x ".venv/bin/python" ]; then
  echo "[ENV] creating .venv with $PY"; "$PY" -m venv .venv
fi
VPY=".venv/bin/python"
HASH="$(sha256sum requirements.txt | cut -c1-16)"
if [ ! -f "data/run/requirements.sha" ] || [ "$(cat data/run/requirements.sha)" != "$HASH" ]; then
  echo "[ENV] installing requirements"; "$VPY" -m pip install --upgrade pip >/dev/null
  "$VPY" -m pip install -r requirements.txt
  echo "$HASH" > data/run/requirements.sha
fi

# system notes for other machines (tkinter + an audio device are needed)
"$VPY" -c 'import tkinter' 2>/dev/null || echo "[WARN] tkinter missing: sudo apt install python3-tk (Debian/Ubuntu)"

echo "[BOOT] bootstrap (Ollama, models, media tools, voice)"
"$VPY" scripts/bootstrap.py "$@" || echo "[WARN] bootstrap reported problems; booting anyway"

date +"%F %T start.sh" > data/run/started.txt
echo "[BOOT] starting C.O.R.A"
exec "$VPY" -u src/boot_sequence.py
