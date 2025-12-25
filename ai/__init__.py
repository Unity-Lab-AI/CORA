"""
C.O.R.A AI Module

Ollama integration, context building, and model routing.
Per ARCHITECTURE.md v1.0.0: Full AI pipeline with HTTP API.
"""

from .ollama import (
    check_ollama,
    list_models,
    pull_model,
    chat,
    chat_stream,
    generate
)

from .context import (
    ContextBuilder,
    build_system_context,
    get_task_context,
    get_time_context
)

from .router import (
    ModelRouter,
    select_model,
    MODEL_KEYWORDS
)

__all__ = [
    # Ollama
    'check_ollama',
    'list_models',
    'pull_model',
    'chat',
    'chat_stream',
    'generate',
    # Context
    'ContextBuilder',
    'build_system_context',
    'get_task_context',
    'get_time_context',
    # Router
    'ModelRouter',
    'select_model',
    'MODEL_KEYWORDS',
]
