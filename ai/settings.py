#!/usr/bin/env python3
"""
C.O.R.A AI/runtime settings — the ONE place model names, Ollama URL, context
size and timeouts come from.

Precedence (highest first):
  1. Environment variables  (OLLAMA_URL / OLLAMA_HOST, CORA_CHAT_MODEL, ...)
  2. config/config.json     ("ollama" and "models" blocks)
  3. Built-in defaults below

Every module that talks to Ollama imports from here instead of hardcoding a
model name or URL. Call reload() after editing config.json at runtime.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

PROJECT_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_DIR / 'config' / 'config.json'

# Built-in defaults — overridden by config.json / env. Chosen 2026-10-14:
# dolphin3 is the current uncensored Llama-3.1 line with a tool-calling template,
# qwen3-vl replaces llava, the chat model doubles as the code model.
_DEFAULTS: Dict[str, Any] = {
    'ollama_url': 'http://127.0.0.1:11434',
    'chat_model': 'dolphin3:8b',
    'vision_model': 'qwen3-vl:4b',
    'code_model': None,          # None -> chat_model
    'think_model': None,         # None -> chat_model
    'num_ctx': 16384,            # Ollama silently clips at 4096 if unset
    'keep_alive': '30m',         # keep the model warm between turns
    'timeout': 120,              # seconds for a full chat completion
    'think_timeout': 30,
    'vision_timeout': 90,
    'temperature': 0.7,
    'max_tokens': 500,
    'history_turns': 40,         # user+assistant messages kept in context
}

_cache: Optional[Dict[str, Any]] = None


def _read_config() -> Dict[str, Any]:
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _normalize_url(url: str) -> str:
    url = (url or '').strip().rstrip('/')
    if not url:
        return ''
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    return url


def _build() -> Dict[str, Any]:
    cfg = _read_config()
    ollama = cfg.get('ollama', {}) or {}
    models = cfg.get('models', {}) or {}
    ai = cfg.get('ai', {}) or {}

    s = dict(_DEFAULTS)

    # config.json
    if ollama.get('api_url'):
        s['ollama_url'] = _normalize_url(ollama['api_url'])
    for key in ('num_ctx', 'keep_alive', 'timeout', 'think_timeout', 'vision_timeout'):
        if ollama.get(key) is not None:
            s[key] = ollama[key]
    if models.get('primary'):
        s['chat_model'] = models['primary']
    elif ollama.get('model'):
        s['chat_model'] = ollama['model']
    for key in ('vision', 'code', 'think'):
        if models.get(key):
            s[key + '_model'] = models[key]
    for key in ('temperature', 'max_tokens', 'history_turns'):
        if ai.get(key) is not None:
            s[key] = ai[key]

    # environment
    env_url = os.environ.get('OLLAMA_URL') or os.environ.get('OLLAMA_HOST')
    if env_url:
        s['ollama_url'] = _normalize_url(env_url)
    for env, key in (('CORA_CHAT_MODEL', 'chat_model'), ('CORA_VISION_MODEL', 'vision_model'),
                     ('CORA_CODE_MODEL', 'code_model'), ('CORA_THINK_MODEL', 'think_model')):
        if os.environ.get(env):
            s[key] = os.environ[env]
    if os.environ.get('CORA_NUM_CTX'):
        try:
            s['num_ctx'] = int(os.environ['CORA_NUM_CTX'])
        except ValueError:
            pass

    if not s['code_model']:
        s['code_model'] = s['chat_model']
    if not s['think_model']:
        s['think_model'] = s['chat_model']
    return s


def settings() -> Dict[str, Any]:
    """Cached settings dict."""
    global _cache
    if _cache is None:
        _cache = _build()
    return _cache


def reload() -> Dict[str, Any]:
    """Re-read config.json and the environment."""
    global _cache
    _cache = _build()
    return _cache


# Accessors — read-through so a reload() is picked up everywhere.
def ollama_url() -> str:
    return settings()['ollama_url']


def chat_model() -> str:
    return settings()['chat_model']


def vision_model() -> str:
    return settings()['vision_model']


def code_model() -> str:
    return settings()['code_model']


def think_model() -> str:
    return settings()['think_model']


def num_ctx() -> int:
    return int(settings()['num_ctx'])


def keep_alive() -> str:
    return str(settings()['keep_alive'])


def timeout() -> int:
    return int(settings()['timeout'])


def think_timeout() -> int:
    return int(settings()['think_timeout'])


def vision_timeout() -> int:
    return int(settings()['vision_timeout'])


def temperature() -> float:
    return float(settings()['temperature'])


def max_tokens() -> int:
    return int(settings()['max_tokens'])


def history_turns() -> int:
    return int(settings()['history_turns'])


def base_options(temperature_override: Optional[float] = None,
                 max_tokens_override: Optional[int] = None) -> Dict[str, Any]:
    """The options block every Ollama request should carry."""
    opts: Dict[str, Any] = {
        'temperature': settings()['temperature'] if temperature_override is None else temperature_override,
        'num_ctx': num_ctx(),
    }
    mt = max_tokens_override if max_tokens_override is not None else None
    if mt:
        opts['num_predict'] = int(mt)
    return opts


if __name__ == '__main__':
    for k, v in settings().items():
        print(f"{k:16} = {v}")
