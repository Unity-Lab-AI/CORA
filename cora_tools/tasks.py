#!/usr/bin/env python3
"""
C.O.R.A Task Management Service
Core task management functionality for CORA

Per ARCHITECTURE.md v2.2.0:
- add_task(text, priority, due_date, notes)
- list_tasks(filter) - Returns pending/done/overdue
- complete_task(id)
- delete_task(id)
- set_priority(id, level)
- set_due(id, date)
- add_note(id, text)
- search_tasks(query)
"""

import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

# Project paths
PROJECT_DIR = Path(__file__).parent.parent
TASKS_FILE = PROJECT_DIR / 'data' / 'tasks.json'


class TaskManager:
    """Manages tasks for CORA."""

    def __init__(self, data_file: Optional[Path] = None):
        """Initialize task manager.

        Args:
            data_file: Path to tasks.json
        """
        self.data_file = data_file or TASKS_FILE
        self.tasks: List[Dict[str, Any]] = []
        self._counter = 0

        self.load()

    def load(self) -> bool:
        """Load tasks from file.

        Returns:
            True if loaded successfully
        """
        try:
            if self.data_file.exists():
                with open(self.data_file) as f:
                    data = json.load(f)
                    self.tasks = data.get('tasks', [])
                    self._counter = data.get('counter', 0)

                    # Update counter from existing tasks
                    for t in self.tasks:
                        tid = t.get('id', '')
                        if tid.startswith('T'):
                            try:
                                num = int(tid[1:])
                                if num >= self._counter:
                                    self._counter = num + 1
                            except ValueError:
                                pass
                    return True
        except Exception as e:
            print(f"[!] Failed to load tasks: {e}")
        return False

    def save(self) -> bool:
        """Save tasks to file.

        Returns:
            True if saved successfully
        """
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                'counter': self._counter,
                'tasks': self.tasks
            }
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"[!] Failed to save tasks: {e}")
            return False

    def _get_next_id(self) -> str:
        """Generate the next task ID.

        Returns:
            Task ID (e.g., T001)
        """
        self._counter += 1
        return f"T{self._counter:03d}"

    def add_task(
        self,
        text: str,
        priority: int = 5,
        due_date: Optional[str] = None,
        notes: Optional[str] = None
    ) -> str:
        """Add a new task.

        Args:
            text: Task description
            priority: Priority 1-10 (1=highest)
            due_date: Due date as ISO string or "YYYY-MM-DD"
            notes: Optional initial note

        Returns:
            Task ID (e.g., T001)
        """
        task_id = self._get_next_id()

        task = {
            'id': task_id,
            'text': text,
            'status': 'pending',
            'priority': max(1, min(10, priority)),
            'created': datetime.now().isoformat(),
            'notes': []
        }

        if due_date:
            task['due'] = due_date

        if notes:
            task['notes'].append({
                'text': notes,
                'created': datetime.now().isoformat()
            })

        self.tasks.append(task)
        self.save()
        return task_id

    def list_tasks(self, filter_type: str = 'all') -> List[Dict[str, Any]]:
        """List tasks with optional filtering.

        Args:
            filter_type: 'all', 'pending', 'done', 'overdue'

        Returns:
            List of task dicts
        """
        now = datetime.now()
        today = now.date()

        if filter_type == 'all':
            return self.tasks
        elif filter_type == 'pending':
            return [t for t in self.tasks if t.get('status') == 'pending']
        elif filter_type == 'done':
            return [t for t in self.tasks if t.get('status') == 'done']
        elif filter_type == 'overdue':
            overdue = []
            for t in self.tasks:
                if t.get('status') != 'pending':
                    continue
                due = t.get('due')
                if due:
                    try:
                        due_date = datetime.fromisoformat(due).date()
                        if due_date < today:
                            overdue.append(t)
                    except ValueError:
                        pass
            return overdue
        else:
            return self.tasks

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific task by ID.

        Args:
            task_id: Task ID (e.g., T001)

        Returns:
            Task dict or None
        """
        task_id = task_id.upper()
        for t in self.tasks:
            if t.get('id') == task_id:
                return t
        return None

    def complete_task(self, task_id: str) -> bool:
        """Mark a task as completed.

        Args:
            task_id: Task ID (e.g., T001)

        Returns:
            True if completed successfully
        """
        task = self.get_task(task_id)
        if task:
            task['status'] = 'done'
            task['completed'] = datetime.now().isoformat()
            self.save()
            return True
        return False

    def delete_task(self, task_id: str) -> bool:
        """Delete a task.

        Args:
            task_id: Task ID (e.g., T001)

        Returns:
            True if deleted successfully
        """
        task_id = task_id.upper()
        for i, t in enumerate(self.tasks):
            if t.get('id') == task_id:
                self.tasks.pop(i)
                self.save()
                return True
        return False

    def set_priority(self, task_id: str, level: int) -> bool:
        """Set task priority.

        Args:
            task_id: Task ID
            level: Priority 1-10 (1=highest)

        Returns:
            True if set successfully
        """
        task = self.get_task(task_id)
        if task:
            task['priority'] = max(1, min(10, level))
            task['modified'] = datetime.now().isoformat()
            self.save()
            return True
        return False

    def set_due(self, task_id: str, date: str) -> bool:
        """Set task due date.

        Args:
            task_id: Task ID
            date: Due date as "YYYY-MM-DD" or ISO string

        Returns:
            True if set successfully
        """
        task = self.get_task(task_id)
        if task:
            task['due'] = date
            task['modified'] = datetime.now().isoformat()
            self.save()
            return True
        return False

    def add_note(self, task_id: str, text: str) -> bool:
        """Add a note to a task.

        Args:
            task_id: Task ID
            text: Note text

        Returns:
            True if added successfully
        """
        task = self.get_task(task_id)
        if task:
            if 'notes' not in task:
                task['notes'] = []
            task['notes'].append({
                'text': text,
                'created': datetime.now().isoformat()
            })
            self.save()
            return True
        return False

    def search_tasks(self, query: str) -> List[Dict[str, Any]]:
        """Search tasks by text.

        Args:
            query: Search query

        Returns:
            List of matching tasks
        """
        query = query.lower()
        results = []
        for t in self.tasks:
            text = t.get('text', '').lower()
            notes_text = ' '.join(n.get('text', '') for n in t.get('notes', [])).lower()
            if query in text or query in notes_text:
                results.append(t)
        return results

    def update_task(self, task_id: str, **kwargs) -> bool:
        """Update task fields.

        Args:
            task_id: Task ID
            **kwargs: Fields to update (text, priority, due, status)

        Returns:
            True if updated successfully
        """
        task = self.get_task(task_id)
        if task:
            for key, value in kwargs.items():
                if key in ('text', 'priority', 'due', 'status'):
                    task[key] = value
            task['modified'] = datetime.now().isoformat()
            self.save()
            return True
        return False

    def get_stats(self) -> Dict[str, int]:
        """Get task statistics.

        Returns:
            Dict with pending, done, overdue counts
        """
        pending = len(self.list_tasks('pending'))
        done = len(self.list_tasks('done'))
        overdue = len(self.list_tasks('overdue'))
        total = len(self.tasks)

        return {
            'total': total,
            'pending': pending,
            'done': done,
            'overdue': overdue
        }


# Convenience functions for direct use

_manager: Optional[TaskManager] = None


def get_manager() -> TaskManager:
    """Get or create the global task manager."""
    global _manager
    if _manager is None:
        _manager = TaskManager()
    return _manager


def add_task(
    text: str,
    priority: int = 5,
    due_date: Optional[str] = None,
    notes: Optional[str] = None
) -> str:
    """Add a new task.

    Args:
        text: Task description
        priority: Priority 1-10 (1=highest)
        due_date: Due date as "YYYY-MM-DD"
        notes: Optional initial note

    Returns:
        Task ID (e.g., T001)
    """
    return get_manager().add_task(text, priority, due_date, notes)


def list_tasks(filter_type: str = 'all') -> List[Dict[str, Any]]:
    """List tasks with optional filtering.

    Args:
        filter_type: 'all', 'pending', 'done', 'overdue'

    Returns:
        List of task dicts
    """
    return get_manager().list_tasks(filter_type)


def complete_task(task_id: str) -> bool:
    """Mark a task as completed.

    Args:
        task_id: Task ID (e.g., T001)

    Returns:
        True if completed successfully
    """
    return get_manager().complete_task(task_id)


def delete_task(task_id: str) -> bool:
    """Delete a task.

    Args:
        task_id: Task ID

    Returns:
        True if deleted successfully
    """
    return get_manager().delete_task(task_id)


def set_priority(task_id: str, level: int) -> bool:
    """Set task priority.

    Args:
        task_id: Task ID
        level: Priority 1-10

    Returns:
        True if set successfully
    """
    return get_manager().set_priority(task_id, level)


def set_due(task_id: str, date: str) -> bool:
    """Set task due date.

    Args:
        task_id: Task ID
        date: Due date as "YYYY-MM-DD"

    Returns:
        True if set successfully
    """
    return get_manager().set_due(task_id, date)


def add_note(task_id: str, text: str) -> bool:
    """Add a note to a task.

    Args:
        task_id: Task ID
        text: Note text

    Returns:
        True if added successfully
    """
    return get_manager().add_note(task_id, text)


def search_tasks(query: str) -> List[Dict[str, Any]]:
    """Search tasks by text.

    Args:
        query: Search query

    Returns:
        List of matching tasks
    """
    return get_manager().search_tasks(query)


def format_task(task: Dict[str, Any], verbose: bool = False) -> str:
    """Format a task for display.

    Args:
        task: Task dict
        verbose: Include all details

    Returns:
        Formatted string
    """
    tid = task.get('id', '?')
    text = task.get('text', '')
    status = task.get('status', 'pending')
    priority = task.get('priority', 5)
    due = task.get('due', '')

    # Status indicator
    if status == 'done':
        status_icon = "[X]"
    else:
        status_icon = "[ ]"

    # Priority indicator
    if priority <= 2:
        priority_str = f"[P{priority}!]"
    elif priority <= 4:
        priority_str = f"[P{priority}]"
    else:
        priority_str = ""

    # Due date
    due_str = ""
    if due and status != 'done':
        try:
            due_date = datetime.fromisoformat(due).date()
            today = datetime.now().date()
            if due_date < today:
                days_overdue = (today - due_date).days
                due_str = f" (OVERDUE {days_overdue}d!)"
            elif due_date == today:
                due_str = " (DUE TODAY)"
            else:
                due_str = f" (due {due_date})"
        except ValueError:
            due_str = f" (due {due})"

    result = f"{tid} {status_icon} {priority_str}{text}{due_str}"

    if verbose:
        notes = task.get('notes', [])
        if notes:
            result += f"\n    Notes: {len(notes)}"
            for n in notes[-2:]:  # Show last 2 notes
                result += f"\n      - {n.get('text', '')[:50]}"

    return result.strip()


if __name__ == "__main__":
    print("=== CORA TASK MANAGER TEST ===")

    manager = TaskManager()

    # Show stats
    stats = manager.get_stats()
    print(f"\nCurrent stats: {stats}")

    # List tasks
    print("\n=== ALL TASKS ===")
    for task in manager.list_tasks('all'):
        print(f"  {format_task(task)}")

    # List overdue
    print("\n=== OVERDUE TASKS ===")
    overdue = manager.list_tasks('overdue')
    if overdue:
        for task in overdue:
            print(f"  {format_task(task)}")
    else:
        print("  None")

    # Test search
    print("\n=== SEARCH TEST ===")
    results = manager.search_tasks("test")
    print(f"  Found {len(results)} tasks matching 'test'")

    print("\n=== TEST COMPLETE ===")
