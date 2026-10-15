#!/usr/bin/env python3
"""
C.O.R.A logging — one call at startup and everything printed anywhere lands in
a dated file too, so a hang or a crash can be read after the fact.

    from ai.log import setup, get_logger
    setup()                          # data/logs/cora-YYYYMMDD.log, tee of stdout+stderr
    log = get_logger('voice')        # logging.Logger writing to the same file
    log.info("sidecar up")

Why a tee and not only `logging`: the codebase prints its boot phases and tool
traces with print(); rewriting hundreds of prints was not worth it. The tee
keeps the console exactly as it was and copies every line to the file. Files
older than `keep_days` are removed at setup.
"""

import io
import logging
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

PROJECT_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_DIR / 'data' / 'logs'

_setup_done = False
_lock = threading.Lock()
_file: Optional[io.TextIOWrapper] = None
_log_path: Optional[Path] = None


class _Tee(io.TextIOBase):
    """Writes to the original stream and to the log file; never raises."""

    def __init__(self, original, name: str):
        self._orig = original
        self._name = name

    def write(self, s):
        try:
            if self._orig is not None:
                self._orig.write(s)
        except Exception:
            pass
        try:
            if _file is not None and s:
                with _lock:
                    _file.write(s)
                    if '\n' in s:
                        _file.flush()
        except Exception:
            pass
        return len(s) if s else 0

    def flush(self):
        try:
            if self._orig is not None:
                self._orig.flush()
        except Exception:
            pass
        try:
            if _file is not None:
                _file.flush()
        except Exception:
            pass

    # the rest of the file-like surface some libraries poke at
    def isatty(self):
        try:
            return bool(self._orig and self._orig.isatty())
        except Exception:
            return False

    @property
    def encoding(self):
        return getattr(self._orig, 'encoding', 'utf-8')

    def fileno(self):
        if self._orig is None:
            raise io.UnsupportedOperation('fileno')
        return self._orig.fileno()

    @property
    def errors(self):
        return getattr(self._orig, 'errors', 'replace')


def setup(name: str = 'cora', keep_days: int = 14, tee: bool = True) -> Optional[Path]:
    """Open today's log file, attach a logging handler, tee stdout/stderr. Idempotent."""
    global _setup_done, _file, _log_path
    with _lock:
        if _setup_done:
            return _log_path
        _setup_done = True
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        _log_path = LOG_DIR / f"{name}-{datetime.now().strftime('%Y%m%d')}.log"
        _file = open(_log_path, 'a', encoding='utf-8', errors='replace')
        _file.write(f"\n===== {name} started {datetime.now().isoformat(timespec='seconds')} pid={os.getpid()} =====\n")
        _file.flush()
        # prune old files
        cutoff = time.time() - keep_days * 86400
        for old in LOG_DIR.glob(f"{name}-*.log"):
            try:
                if old.stat().st_mtime < cutoff and old != _log_path:
                    old.unlink()
            except OSError:
                pass
    except Exception as e:
        print(f"[log] file logging unavailable: {e}")
        _file = None
        return None
    handler = logging.StreamHandler(_file)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s', '%H:%M:%S'))
    root = logging.getLogger()
    root.addHandler(handler)
    if root.level == logging.WARNING:      # the default; keep user-set levels
        root.setLevel(logging.INFO)
    if tee:
        if not isinstance(sys.stdout, _Tee):
            sys.stdout = _Tee(sys.stdout, 'stdout')
        if not isinstance(sys.stderr, _Tee):
            sys.stderr = _Tee(sys.stderr, 'stderr')
    return _log_path


def get_logger(name: str = 'cora') -> logging.Logger:
    return logging.getLogger(name)


def log_path() -> Optional[Path]:
    return _log_path


if __name__ == '__main__':
    print('log file:', setup('cora-selftest'))
    get_logger('selftest').info('hello from logging')
    print('hello from print')
