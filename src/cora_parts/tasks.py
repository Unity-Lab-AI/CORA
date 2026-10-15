#!/usr/bin/env python3
"""src.cora_parts: tasks (split from src/cora.py on 2026-10-14)."""
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
from src.cora_parts._base import datetime, generate_id, save_tasks, timedelta  # noqa: F401




def cmd_add(args, tasks):
    from src.cora_parts.chat import respond
    """Add a new task."""
    if not args:
        respond('error', {'message': "Please provide task text. Usage: add <description>"})
        return tasks

    text = ' '.join(args)
    task = {
        'id': generate_id(),
        'text': text,
        'status': 'pending',
        'priority': 5,
        'created': datetime.now().isoformat(),
        'notes': []
    }
    tasks.append(task)
    save_tasks(tasks)
    respond('task_added', {'id': task['id'], 'text': text[:40]})
    return tasks


def cmd_list(args, tasks):
    from src.cora_parts.chat import respond
    """List all tasks. Use 'list pri' to sort by priority."""
    if not tasks:
        respond('info', {'message': "No tasks found. Use 'add <text>' to create one."})
        return tasks

    # Check for sort option
    sort_by_pri = args and args[0].lower() in ('pri', 'priority', 'p')

    display_tasks = tasks.copy()
    if sort_by_pri:
        display_tasks.sort(key=lambda t: t.get('priority', 5))
        print("\n=== TASKS (sorted by priority) ===")
    else:
        print("\n=== TASKS ===")

    print(f"{'ID':<6} {'STATUS':<10} {'PRI':<4} {'DESCRIPTION'}")
    print("-" * 60)

    for task in display_tasks:
        status_icon = "[x]" if task['status'] == 'done' else "[ ]"
        print(f"{task['id']:<6} {status_icon:<10} P{task.get('priority', 5):<3} {task['text'][:40]}")

    pending = len([t for t in tasks if t['status'] == 'pending'])
    done = len([t for t in tasks if t['status'] == 'done'])
    active = len([t for t in tasks if t['status'] == 'active'])
    print("-" * 60)
    print(f"Total: {len(tasks)} | Pending: {pending} | Active: {active} | Done: {done}")
    return tasks


def cmd_done(args, tasks):
    from src.cora_parts.chat import respond
    """Mark a task as done."""
    if not args:
        respond('error', {'message': "Please provide task ID. Usage: done <id>"})
        return tasks

    task_id = args[0].upper()
    for task in tasks:
        if task['id'] == task_id:
            task['status'] = 'done'
            task['completed'] = datetime.now().isoformat()
            save_tasks(tasks)
            respond('task_done', {'id': task_id, 'text': task['text'][:40]})
            return tasks

    respond('not_found', {'id': task_id})
    return tasks


def cmd_pri(args, tasks):
    from src.cora_parts.chat import respond
    """Set task priority (1-10)."""
    if len(args) < 2:
        respond('error', {'message': "Please provide task ID and priority. Usage: pri <id> <1-10>"})
        return tasks

    task_id = args[0].upper()
    try:
        priority = int(args[1])
        if priority < 1 or priority > 10:
            respond('error', {'message': "Priority must be between 1 and 10"})
            return tasks
    except ValueError:
        respond('error', {'message': "Priority must be a number (1-10)"})
        return tasks

    for task in tasks:
        if task['id'] == task_id:
            task['priority'] = priority
            save_tasks(tasks)
            respond('priority_set', {'id': task_id, 'priority': priority})
            return tasks

    respond('not_found', {'id': task_id})
    return tasks


def cmd_note(args, tasks):
    from src.cora_parts.chat import respond
    """Add a note to a task."""
    if len(args) < 2:
        respond('error', {'message': "Please provide task ID and note text. Usage: note <id> <text>"})
        return tasks

    task_id = args[0].upper()
    note_text = ' '.join(args[1:])

    for task in tasks:
        if task['id'] == task_id:
            if 'notes' not in task:
                task['notes'] = []
            note = {
                'text': note_text,
                'created': datetime.now().isoformat()
            }
            task['notes'].append(note)
            save_tasks(tasks)
            respond('note_added', {'id': task_id, 'note': note_text[:40]})
            return tasks

    respond('not_found', {'id': task_id})
    return tasks


def cmd_status(args, tasks):
    from src.cora_parts.chat import respond
    """Change task status."""
    if len(args) < 2:
        respond('error', {'message': "Please provide task ID and status. Usage: status <id> <pending|active|done>"})
        return tasks

    task_id = args[0].upper()
    new_status = args[1].lower()

    valid_statuses = ['pending', 'active', 'done']
    if new_status not in valid_statuses:
        respond('error', {'message': f"Invalid status. Use: {', '.join(valid_statuses)}"})
        return tasks

    for task in tasks:
        if task['id'] == task_id:
            old_status = task['status']
            task['status'] = new_status
            if new_status == 'done' and 'completed' not in task:
                task['completed'] = datetime.now().isoformat()
            save_tasks(tasks)
            respond('status_changed', {'id': task_id, 'old': old_status, 'new': new_status})
            return tasks

    respond('not_found', {'id': task_id})
    return tasks


def cmd_show(args, tasks):
    from src.cora_parts.chat import respond
    """Show detailed view of a single task."""
    if not args:
        respond('error', {'message': "Please provide task ID. Usage: show <id>"})
        return tasks

    task_id = args[0].upper()
    for task in tasks:
        if task['id'] == task_id:
            respond('task_shown', {'id': task_id}, speak_it=False)
            print(f"\n=== TASK {task_id} ===")
            print(f"Description: {task['text']}")
            print(f"Status:      {task['status']}")
            print(f"Priority:    P{task.get('priority', 5)}")
            if 'due' in task:
                print(f"Due Date:    {task['due']}")
            print(f"Created:     {task['created'][:10]}")
            if 'completed' in task:
                print(f"Completed:   {task['completed'][:10]}")

            # Show notes if any
            notes = task.get('notes', [])
            if notes:
                print(f"\nNotes ({len(notes)}):")
                for i, note in enumerate(notes, 1):
                    print(f"  {i}. {note['text']}")
                    print(f"     ({note['created'][:10]})")
            else:
                print("\nNotes: (none)")

            print("")
            return tasks

    respond('not_found', {'id': task_id})
    return tasks


def cmd_search(args, tasks):
    from src.cora_parts.chat import respond
    """Search tasks by text content."""
    if not args:
        respond('error', {'message': "Please provide search query. Usage: search <query>"})
        return tasks

    query = ' '.join(args).lower()
    matches = []

    for task in tasks:
        # Search in text
        if query in task['text'].lower():
            matches.append(task)
            continue
        # Search in notes
        for note in task.get('notes', []):
            if query in note['text'].lower():
                matches.append(task)
                break

    if not matches:
        respond('no_results', {'query': query})
        return tasks

    respond('search_results', {'count': len(matches), 'query': query}, speak_it=False)
    print(f"\n=== SEARCH RESULTS for '{query}' ===")
    print(f"{'ID':<6} {'STATUS':<10} {'PRI':<4} {'DESCRIPTION'}")
    print("-" * 60)

    for task in matches:
        status_icon = "[x]" if task['status'] == 'done' else "[ ]"
        print(f"{task['id']:<6} {status_icon:<10} P{task.get('priority', 5):<3} {task['text'][:40]}")

    print("-" * 60)
    print(f"Found: {len(matches)} matching tasks")
    return tasks


def cmd_edit(args, tasks):
    from src.cora_parts.chat import respond
    """Edit task text. Usage: edit <id> <new text>"""
    if len(args) < 2:
        respond('error', {'message': "Please provide task ID and new text. Usage: edit <id> <new text>"})
        return tasks

    task_id = args[0].upper()
    new_text = ' '.join(args[1:])

    for task in tasks:
        if task['id'] == task_id:
            old_text = task['text']
            task['text'] = new_text
            task['modified'] = datetime.now().isoformat()
            save_tasks(tasks)
            respond('task_edited', {'id': task_id, 'text': new_text[:40]})
            return tasks

    respond('not_found', {'id': task_id})
    return tasks


def get_task_context(tasks):
    """Build a context string describing current tasks for AI awareness."""
    if not tasks:
        return "The user has no tasks currently."

    pending = [t for t in tasks if t['status'] == 'pending']
    active = [t for t in tasks if t['status'] == 'active']
    done = [t for t in tasks if t['status'] == 'done']

    context_parts = [
        f"The user has {len(tasks)} total tasks: {len(pending)} pending, {len(active)} active, {len(done)} done."
    ]

    # Add high priority pending tasks
    high_pri = [t for t in pending if t.get('priority', 5) <= 3]
    if high_pri:
        context_parts.append("High priority pending tasks:")
        for t in high_pri[:3]:
            context_parts.append(f"  - {t['id']}: {t['text']} (P{t.get('priority', 5)})")

    # Add overdue tasks
    today = datetime.now().strftime('%Y-%m-%d')
    overdue = [t for t in tasks if t.get('due') and t['due'] < today and t['status'] != 'done']
    if overdue:
        context_parts.append("Overdue tasks:")
        for t in overdue[:3]:
            context_parts.append(f"  - {t['id']}: {t['text']} (due {t['due']})")

    # Add recently added tasks
    if pending:
        context_parts.append("Recent pending tasks:")
        for t in pending[:5]:
            context_parts.append(f"  - {t['id']}: {t['text']}")

    return "\n".join(context_parts)


def cmd_stats(args, tasks):
    from src.cora_parts.chat import respond
    """Show task statistics."""
    if not tasks:
        respond('info', {'message': "No tasks found. Use 'add <text>' to create one."})
        return tasks

    # Count by status
    pending = len([t for t in tasks if t['status'] == 'pending'])
    active = len([t for t in tasks if t['status'] == 'active'])
    done = len([t for t in tasks if t['status'] == 'done'])
    total = len(tasks)

    # Count by priority
    pri_counts = {}
    for t in tasks:
        p = t.get('priority', 5)
        pri_counts[p] = pri_counts.get(p, 0) + 1

    # Count overdue
    today = datetime.now().strftime('%Y-%m-%d')
    overdue = len([t for t in tasks if t.get('due') and t['due'] < today and t['status'] != 'done'])

    # Count with notes
    with_notes = len([t for t in tasks if t.get('notes')])

    print("\n=== TASK STATISTICS ===")
    print("-" * 40)
    print(f"Total Tasks:     {total}")
    print(f"  Pending:       {pending}")
    print(f"  Active:        {active}")
    print(f"  Done:          {done}")
    print("-" * 40)
    print("By Priority:")
    for p in sorted(pri_counts.keys()):
        count = pri_counts[p]
        bar = "#" * count
        print(f"  P{p}: {count:>3} {bar}")
    print("-" * 40)
    print(f"Overdue:         {overdue}")
    print(f"With Notes:      {with_notes}")

    if total > 0:
        completion = (done / total) * 100
        print(f"Completion:      {completion:.1f}%")

    print("")
    return tasks


def cmd_due(args, tasks):
    from src.cora_parts.chat import respond
    """Set task due date."""
    if len(args) < 2:
        respond('error', {'message': "Please provide task ID and date. Usage: due <id> <YYYY-MM-DD> or +Nd"})
        return tasks

    task_id = args[0].upper()
    date_str = args[1]

    # Parse date
    try:
        if date_str.startswith('+') and date_str.endswith('d'):
            # Relative date: +3d means 3 days from now
            days = int(date_str[1:-1])
            due_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
        else:
            # Absolute date: YYYY-MM-DD
            datetime.strptime(date_str, '%Y-%m-%d')  # Validate format
            due_date = date_str
    except ValueError:
        respond('error', {'message': "Invalid date. Use YYYY-MM-DD or +Nd (e.g., +3d)"})
        return tasks

    for task in tasks:
        if task['id'] == task_id:
            task['due'] = due_date
            save_tasks(tasks)
            respond('due_set', {'id': task_id, 'due': due_date})
            return tasks

    respond('not_found', {'id': task_id})
    return tasks


def cmd_today(args, tasks):
    """Show tasks due today and overdue tasks."""
    today = datetime.now().strftime('%Y-%m-%d')

    # Find overdue and today's tasks
    overdue = [t for t in tasks if t.get('due') and t['due'] < today and t['status'] != 'done']
    today_tasks = [t for t in tasks if t.get('due') == today and t['status'] != 'done']

    if not overdue and not today_tasks:
        print("No tasks due today or overdue.")
        return tasks

    print(f"\n=== TODAY ({today}) ===")

    if overdue:
        print(f"\nOVERDUE ({len(overdue)}):")
        print("-" * 50)
        for task in overdue:
            days_late = (datetime.now() - datetime.strptime(task['due'], '%Y-%m-%d')).days
            print(f"  {task['id']}: {task['text'][:35]} (due {task['due']}, {days_late}d late)")

    if today_tasks:
        print(f"\nDUE TODAY ({len(today_tasks)}):")
        print("-" * 50)
        for task in today_tasks:
            print(f"  {task['id']}: {task['text'][:40]} P{task.get('priority', 5)}")

    print("")
    return tasks
