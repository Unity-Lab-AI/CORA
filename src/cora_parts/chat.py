#!/usr/bin/env python3
"""src.cora_parts: chat (split from src/cora.py on 2026-10-14)."""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import shutil
import subprocess
import threading
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from src.cora_parts import _base  # noqa: F401
from src.cora_parts._base import datetime, speak  # noqa: F401




def generate_greeting(personality):
    from src.cora_parts.logging_setup import SYSTEM_PROMPT
    """Generate an AI greeting based on full system prompt personality."""
    # Try to generate via Ollama using the FULL system prompt
    if _base.CONFIG and _base.CONFIG.get('ollama', {}).get('enabled', True):
        try:
            from ai.ollama import generate
            r = generate(prompt="Generate a single greeting (under 15 words) that sounds like you. Just the greeting, nothing else.",
                         system=SYSTEM_PROMPT, max_tokens=40, timeout=20)
            if r.content and not r.error:
                return r.content.strip().strip('"')
        except Exception:
            pass
    # Fallback with CORA personality
    return "What the fuck do you want? CORA's online, bitch."


def detect_emotion(text):
    """Detect emotion from text for TTS inflection.

    Returns emotion string for TTS instruction building.
    Per ARCHITECTURE.md: Analyze text before speaking, build TTS instruction.
    """
    text_lower = text.lower()

    # Keyword-based emotion detection (fast, no AI needed)
    if any(word in text_lower for word in ['!', 'great', 'awesome', 'excellent', 'amazing', 'congrats', 'fantastic']):
        return 'excited'
    if any(word in text_lower for word in ['sorry', 'unfortunately', 'failed', 'error', 'problem', 'issue']):
        return 'concerned'
    if any(word in text_lower for word in ['done', 'complete', 'finished', 'success', 'nice']):
        return 'satisfied'
    if any(word in text_lower for word in ['remember', 'don\'t forget', 'deadline', 'overdue', 'urgent']):
        return 'urgent'
    if any(word in text_lower for word in ['?']):
        return 'questioning'
    if any(word in text_lower for word in ['hello', 'hi', 'hey', 'welcome', 'greetings']):
        return 'warm'
    if any(word in text_lower for word in ['goodbye', 'bye', 'see you', 'later']):
        return 'gentle'

    return 'neutral'


# Response generation is AI-driven. No hardcoded templates.
# Fallback responses are generated dynamically based on action type.


def ai_respond(action, context=None, use_ai=True):
    from src.cora_parts.logging_setup import SYSTEM_PROMPT
    """Generate a response for an action using Ollama AI.

    All responses are AI-generated based on personality. No hardcoded templates.

    Args:
        action: The type of action (e.g., 'task_added', 'error')
        context: Dict with variables for context
        use_ai: If True, use Ollama (default True per ARCHITECTURE.md)

    Returns:
        str: The AI-generated response text
    """
    context = context or {}

    # Build context string for AI
    context_str = ', '.join(f"{k}={v}" for k, v in context.items()) if context else "none"

    # Try AI-generated response
    if use_ai and _base.CONFIG and _base.CONFIG.get('ollama', {}).get('enabled', True):
        try:
            from ai.ollama import generate
            r = generate(prompt=f"Action: {action}\nContext: {context_str}\n\nRespond briefly (under 20 words):",
                         system=SYSTEM_PROMPT, max_tokens=60, timeout=20)
            if r.content and not r.error:
                return r.content.strip()
        except Exception:
            pass  # Fall back to dynamic response

    # Dynamic fallback (no hardcoded templates)
    # Generate simple response based on action type
    action_responses = {
        'task_added': f"Task {context.get('id', '')} added.",
        'task_done': f"Task {context.get('id', '')} complete.",
        'task_deleted': f"Task {context.get('id', '')} removed.",
        'error': f"Error: {context.get('message', 'Unknown error')}",
        'not_found': f"Task {context.get('id', '')} not found.",
        'priority_set': f"Priority set to {context.get('priority', '')}.",
        'due_set': f"Due date: {context.get('due', '')}.",
        'note_added': f"Note added to {context.get('id', '')}.",
        'status_changed': f"Status: {context.get('new', '')}.",
        'task_edited': f"Task {context.get('id', '')} updated.",
        'task_shown': f"Task {context.get('id', '')}:",
        'backup_created': f"Backup complete.",
        'search_results': f"Found {context.get('count', 0)} results.",
        'no_results': f"No results for '{context.get('query', '')}'.",
        'startup': "Ready.",
        'shutdown': "Goodbye.",
        'info': f"{context.get('message', '')}",
        'knowledge_added': f"Learned {context.get('id', '')}: {context.get('content', '')} (Tags: {context.get('tags', 'none')})",
        'unknown_command': f"Unknown command: {context.get('cmd', '')}. Type 'help' for available commands.",
    }
    return action_responses.get(action, f"{action}: {context_str}")


def respond(action, context=None, speak_it=True, use_ai=False):
    """Print and optionally speak a response for an action.

    This is the main function for CORA's responses. It generates appropriate
    text based on the action type, prints it, and optionally speaks it via TTS.

    Args:
        action: The type of action (e.g., 'task_added', 'error')
        context: Dict with variables for the response
        speak_it: If True, speak the response via TTS
        use_ai: If True, generate more natural responses via Ollama
    """
    response = ai_respond(action, context, use_ai)
    print(f"[CORA]: {response}")
    if speak_it:
        speak(response)
    return response


def fallback_response(user_message, tasks):
    """Generate a helpful response when Ollama is unavailable."""
    message_lower = user_message.lower()

    # Task-related questions
    if any(word in message_lower for word in ['task', 'todo', 'what', 'list', 'show']):
        pending = [t for t in tasks if t['status'] == 'pending']
        if pending:
            response = f"You have {len(pending)} pending tasks. "
            if len(pending) <= 3:
                response += "They are: " + ", ".join(t['text'][:30] for t in pending)
            else:
                high_pri = [t for t in pending if t.get('priority', 5) <= 3]
                if high_pri:
                    response += f"Your highest priority: {high_pri[0]['text'][:40]}"
                else:
                    response += f"First one: {pending[0]['text'][:40]}"
            return response
        return "You have no pending tasks. Use 'add <task>' to create one."

    # Help requests
    if any(word in message_lower for word in ['help', 'how', 'what can']):
        return "I can help you manage tasks! Try: add, list, done, pri, due, search, stats, backup. Type 'help' for full list."

    # Priority questions
    if 'priority' in message_lower or 'important' in message_lower:
        high_pri = [t for t in tasks if t['status'] == 'pending' and t.get('priority', 5) <= 3]
        if high_pri:
            return f"High priority tasks: " + ", ".join(f"{t['id']}: {t['text'][:25]}" for t in high_pri[:3])
        return "No high priority tasks. Set priority with: pri <id> <1-10>"

    # Due date questions
    if 'due' in message_lower or 'deadline' in message_lower or 'overdue' in message_lower:
        today = datetime.now().strftime('%Y-%m-%d')
        overdue = [t for t in tasks if t.get('due') and t['due'] < today and t['status'] != 'done']
        if overdue:
            return f"You have {len(overdue)} overdue task(s): " + ", ".join(t['id'] for t in overdue[:3])
        return "No overdue tasks. Set due dates with: due <id> <YYYY-MM-DD>"

    # Generic fallback
    return "I'm in offline mode (Ollama unavailable). I can still help with basic task queries. Try asking about your tasks, priorities, or due dates!"
