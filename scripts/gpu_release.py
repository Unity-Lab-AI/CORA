#!/usr/bin/env python3
"""
Release the GPU: ask Ollama to drop every loaded model (keep_alive 0), end her
image engine sidecar when CORA started it, and report VRAM before and after. CORA calls the same unload on every normal exit; the stop
scripts call it too. Run it by hand after anything that talked to her brain:

    python scripts/gpu_release.py
"""
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def vram() -> str:
    try:
        out = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,noheader'],
                             capture_output=True, text=True, timeout=10).stdout.strip()
        return out or 'n/a'
    except Exception:
        return 'n/a'


def main():
    from ai import ollama
    print(f"VRAM before: {vram()}")
    names = ollama.unload_models()
    print("unloaded:", names or 'nothing was loaded')
    time.sleep(3)
    print(f"VRAM after:  {vram()}")


if __name__ == '__main__':
    main()
