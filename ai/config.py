#!/usr/bin/env python3
"""
C.O.R.A config loader — the ONE way config/config.json is read and written.

    from ai import config
    cfg = config.load()                       # cached; re-read when the file changes
    config.get('tts.unity_voice.url')         # dotted path, default None
    config.get('camera.open_timeout', 4.0)
    config.save(cfg)                          # atomic: tmp file + os.replace
    config.update(lambda c: c.setdefault('boot', {}).update(demo_phases=False))
    config.version()                          # "3.0.0"

Reads are cached on the file's mtime so a hot loop never re-parses, and every
writer goes through save(): a crash mid-write can never leave a half file.
Modules that need typed accessors (models, timeouts) keep using ai.settings,
which reads through here.
"""

import json
import os
import threading
from pathlib import Path
from typing import Any, Callable, Dict, Optional

PROJECT_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_DIR / 'config' / 'config.json'

_lock = threading.RLock()
_cache: Optional[Dict[str, Any]] = None
_cache_mtime: float = -1.0


def path() -> Path:
    return CONFIG_PATH


def load(force: bool = False) -> Dict[str, Any]:
    """The config dict (a copy is NOT made: treat it as read-only, use update() to change it)."""
    global _cache, _cache_mtime
    with _lock:
        try:
            mtime = CONFIG_PATH.stat().st_mtime
        except OSError:
            mtime = -1.0
        if force or _cache is None or mtime != _cache_mtime:
            try:
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                _cache = data if isinstance(data, dict) else {}
            except FileNotFoundError:
                _cache = {}
            except Exception as e:
                print(f"[config] {CONFIG_PATH.name} unreadable ({e}); keeping the last good copy")
                _cache = _cache or {}
            _cache_mtime = mtime
        return _cache


def get(dotted: str, default: Any = None) -> Any:
    """Value at a dotted path ('tts.unity_voice.url'), or default."""
    node: Any = load()
    for part in dotted.split('.'):
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node


def section(name: str) -> Dict[str, Any]:
    """A top-level block as a dict ({} when missing)."""
    v = load().get(name)
    return v if isinstance(v, dict) else {}


def save(cfg: Dict[str, Any]):
    """Atomic write; the cache is refreshed from what was written."""
    global _cache, _cache_mtime
    with _lock:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = CONFIG_PATH.with_suffix('.json.tmp')
        with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
            f.write('\n')
        os.replace(tmp, CONFIG_PATH)
        _cache = cfg
        try:
            _cache_mtime = CONFIG_PATH.stat().st_mtime
        except OSError:
            _cache_mtime = -1.0
        try:
            from ai import settings as _settings
            _settings.reload()
        except Exception:
            pass


def update(mutator: Callable[[Dict[str, Any]], Any]) -> Dict[str, Any]:
    """Load, let `mutator` change the dict in place, save. Returns the dict."""
    with _lock:
        cfg = json.loads(json.dumps(load(force=True)))   # work on a copy
        mutator(cfg)
        save(cfg)
        return cfg


def version() -> str:
    return str(load().get('version') or '3.0.0')


if __name__ == '__main__':
    c = load()
    print(CONFIG_PATH, '->', len(c), 'top-level keys; version', version())
    print('chat model:', get('models.primary'), '| camera timeout:', get('camera.open_timeout', 4.0))
