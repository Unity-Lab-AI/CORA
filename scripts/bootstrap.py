#!/usr/bin/env python3
"""
C.O.R.A bootstrap — run by CORA.bat (inside the venv) before the boot sequence.

Does the environment work that used to be hardcoded in the batch file:
  1. Ollama reachable (starts it if the executable is found and it is down)
  2. The CONFIGURED models (ai.settings: chat, vision, code) are pulled
  3. yt-dlp is current
  4. The unity-voice-v2 sidecar is reachable (starts it if configured)
  5. Playwright browsers are installed (best effort)

Exit code 0 always: a missing optional piece is reported, never fatal, so the
boot sequence can still run and narrate what is missing.

    python scripts/bootstrap.py [--no-pull] [--no-voice] [--quiet]
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from ai import settings  # noqa: E402

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_DIR / '.env')
except Exception:
    pass


def say(msg: str, quiet: bool = False):
    if not quiet:
        print(msg, flush=True)


# --------------------------------------------------------------------------- ollama
def find_ollama() -> str:
    exe = shutil.which('ollama')
    if exe:
        return exe
    for loc in (
        os.path.expandvars(r'%LOCALAPPDATA%\Programs\Ollama\ollama.exe'),
        os.path.expandvars(r'%ProgramFiles%\Ollama\ollama.exe'),
        os.path.expandvars(r'%ProgramFiles(x86)%\Ollama\ollama.exe'),
        os.path.expandvars(r'%USERPROFILE%\Ollama\ollama.exe'),
    ):
        if os.path.exists(loc):
            return loc
    return ''


def ensure_ollama(quiet: bool) -> bool:
    from ai import ollama
    if ollama.check_ollama()['connected']:
        say(f"[OK] Ollama running at {settings.ollama_url()}", quiet)
        return True
    exe = find_ollama()
    if not exe:
        say("[WARN] Ollama not installed - https://ollama.com", quiet)
        return False
    say("[..] Starting Ollama service...", quiet)
    try:
        flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        subprocess.Popen([exe, 'serve'], creationflags=flags,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        say(f"[WARN] Could not start Ollama: {e}", quiet)
        return False
    for _ in range(20):
        time.sleep(0.5)
        if ollama.check_ollama()['connected']:
            say("[OK] Ollama started", quiet)
            return True
    say("[WARN] Ollama did not answer in 10 s", quiet)
    return False


def ensure_models(quiet: bool, pull: bool = True):
    from ai import ollama
    wanted = []
    for name in (settings.chat_model(), settings.vision_model(), settings.code_model()):
        if name and name not in wanted:
            wanted.append(name)
    present = [m['name'] for m in ollama.list_models()]
    for name in wanted:
        base = name.split(':')[0]
        have = name in present or any(p.split(':')[0] == base for p in present)
        if have:
            say(f"[OK] model {name}", quiet)
            continue
        if not pull:
            say(f"[WARN] model {name} missing (pull skipped)", quiet)
            continue
        say(f"[..] Pulling {name} (this can take several minutes)...", quiet)
        last = ['']

        def cb(status, done, total):
            if total and not quiet:
                pct = int(done * 100 / total)
                line = f"      {status} {pct}%"
                if line != last[0]:
                    print(line, end='\r', flush=True)
                    last[0] = line
        ok = ollama.pull_model(name, cb)
        print()
        say(f"[{'OK' if ok else 'WARN'}] {name} {'ready' if ok else 'failed to pull'}", quiet)


# --------------------------------------------------------------------------- tools
def ensure_ytdlp(quiet: bool):
    try:
        r = subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--upgrade', 'yt-dlp'],
                           capture_output=True, text=True, timeout=300)
        say("[OK] yt-dlp current" if r.returncode == 0 else f"[WARN] yt-dlp upgrade: {r.stderr[-200:]}", quiet)
    except Exception as e:
        say(f"[WARN] yt-dlp: {e}", quiet)


def ensure_playwright(quiet: bool):
    try:
        import playwright  # noqa: F401
    except ImportError:
        return
    marker = PROJECT_DIR / 'data' / '.playwright_ok'
    if marker.exists():
        return
    try:
        r = subprocess.run([sys.executable, '-m', 'playwright', 'install', 'chromium'],
                           capture_output=True, text=True, timeout=900)
        if r.returncode == 0:
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text('ok')
            say("[OK] Playwright chromium installed", quiet)
        else:
            say(f"[WARN] playwright install: {r.stderr[-200:]}", quiet)
    except Exception as e:
        say(f"[WARN] playwright: {e}", quiet)


# --------------------------------------------------------------------------- voice
def ensure_voice(quiet: bool):
    try:
        from voice.unity_voice import ensure_sidecar, VOICE_URL
    except Exception as e:
        say(f"[WARN] voice client unavailable: {e}", quiet)
        return
    ok, msg = ensure_sidecar(timeout=45)
    say(f"[{'OK' if ok else 'WARN'}] unity-voice-v2 {VOICE_URL}: {msg}", quiet)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--no-pull', action='store_true')
    ap.add_argument('--no-voice', action='store_true')
    ap.add_argument('--quiet', action='store_true')
    a = ap.parse_args()
    q = a.quiet
    say(f"[ENV] python {sys.version.split()[0]} at {sys.executable}", q)
    say(f"[ENV] chat={settings.chat_model()} vision={settings.vision_model()} num_ctx={settings.num_ctx()}", q)
    if ensure_ollama(q):
        ensure_models(q, pull=not a.no_pull)
    ensure_ytdlp(q)
    ensure_playwright(q)
    if not a.no_voice:
        ensure_voice(q)
    return 0


if __name__ == '__main__':
    sys.exit(main())
