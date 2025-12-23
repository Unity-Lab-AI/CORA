#!/usr/bin/env python3
"""
C.O.R.A Reminders Service
Time-based reminders and alerts

Per ARCHITECTURE.md v2.0.0:
- Add/remove reminders
- Time-based trigger checking
- Notification integration
- Repeating reminders (daily, weekly)
"""

import os
import sys
import json
import threading
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Callable
from pathlib import Path

# Add project root to path
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))


class ReminderManager:
    """Manages time-based reminders."""

    def __init__(self, data_file: Optional[Path] = None):
        """Initialize reminder manager.

        Args:
            data_file: Path to reminders.json
        """
        self.data_file = data_file or PROJECT_DIR / 'data' / 'reminders.json'
        self.reminders: List[Dict[str, Any]] = []
        self._next_id = 1
        self._check_thread: Optional[threading.Thread] = None
        self._running = False
        self._on_trigger: Optional[Callable] = None

        self.load()

    def load(self) -> bool:
        """Load reminders from file.

        Returns:
            True if loaded successfully
        """
        try:
            if self.data_file.exists():
                with open(self.data_file) as f:
                    data = json.load(f)
                    self.reminders = data.get('reminders', [])

                    # Find next ID
                    for r in self.reminders:
                        rid = r.get('id', '')
                        if rid.startswith('R'):
                            try:
                                num = int(rid[1:])
                                if num >= self._next_id:
                                    self._next_id = num + 1
                            except ValueError:
                                pass
                    return True
        except Exception as e:
            print(f"[!] Failed to load reminders: {e}")
        return False

    def save(self) -> bool:
        """Save reminders to file.

        Returns:
            True if saved successfully
        """
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                'version': '1.0.0',
                'description': 'Time-based reminders for CORA',
                'reminders': self.reminders
            }
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"[!] Failed to save reminders: {e}")
            return False

    def add(
        self,
        text: str,
        time: datetime,
        repeat: Optional[str] = None,
        urgent: bool = False
    ) -> str:
        """Add a new reminder.

        Args:
            text: Reminder message
            time: When to remind
            repeat: None, 'daily', 'weekly', 'monthly'
            urgent: If True, use urgent notification style

        Returns:
            Reminder ID (e.g., R001)
        """
        reminder_id = f"R{self._next_id:03d}"
        self._next_id += 1

        reminder = {
            'id': reminder_id,
            'text': text,
            'time': time.isoformat(),
            'repeat': repeat,
            'created': datetime.now().isoformat(),
            'last_triggered': None,
            'enabled': True,
            'urgent': urgent
        }

        self.reminders.append(reminder)
        self.save()
        return reminder_id

    def remove(self, reminder_id: str) -> bool:
        """Remove a reminder.

        Args:
            reminder_id: ID of reminder to remove

        Returns:
            True if removed
        """
        for i, r in enumerate(self.reminders):
            if r.get('id') == reminder_id:
                self.reminders.pop(i)
                self.save()
                return True
        return False

    def get(self, reminder_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific reminder.

        Args:
            reminder_id: ID of reminder

        Returns:
            Reminder dict or None
        """
        for r in self.reminders:
            if r.get('id') == reminder_id:
                return r
        return None

    def list_all(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """List all reminders.

        Args:
            enabled_only: If True, only return enabled reminders

        Returns:
            List of reminder dicts
        """
        if enabled_only:
            return [r for r in self.reminders if r.get('enabled', True)]
        return self.reminders

    def list_due(self) -> List[Dict[str, Any]]:
        """Get reminders that are due now.

        Returns:
            List of due reminders
        """
        now = datetime.now()
        due = []

        for r in self.reminders:
            if not r.get('enabled', True):
                continue

            try:
                reminder_time = datetime.fromisoformat(r['time'])
                if reminder_time <= now:
                    # Check if already triggered recently (within 1 minute)
                    last = r.get('last_triggered')
                    if last:
                        last_time = datetime.fromisoformat(last)
                        if (now - last_time).total_seconds() < 60:
                            continue
                    due.append(r)
            except (ValueError, KeyError):
                continue

        return due

    def mark_triggered(self, reminder_id: str) -> bool:
        """Mark a reminder as triggered.

        Args:
            reminder_id: ID of reminder

        Returns:
            True if marked
        """
        for r in self.reminders:
            if r.get('id') == reminder_id:
                now = datetime.now()
                r['last_triggered'] = now.isoformat()

                # Handle repeating reminders
                repeat = r.get('repeat')
                if repeat:
                    current_time = datetime.fromisoformat(r['time'])
                    if repeat == 'daily':
                        next_time = current_time + timedelta(days=1)
                    elif repeat == 'weekly':
                        next_time = current_time + timedelta(weeks=1)
                    elif repeat == 'monthly':
                        # Add ~30 days for monthly
                        next_time = current_time + timedelta(days=30)
                    else:
                        next_time = None

                    if next_time:
                        r['time'] = next_time.isoformat()
                else:
                    # Non-repeating reminder - disable after trigger
                    r['enabled'] = False

                self.save()
                return True
        return False

    def toggle(self, reminder_id: str) -> Optional[bool]:
        """Toggle a reminder's enabled state.

        Args:
            reminder_id: ID of reminder

        Returns:
            New enabled state or None if not found
        """
        for r in self.reminders:
            if r.get('id') == reminder_id:
                r['enabled'] = not r.get('enabled', True)
                self.save()
                return r['enabled']
        return None

    def set_callback(self, callback: Callable):
        """Set callback for when reminders trigger.

        Args:
            callback: Function called with (reminder_dict) when triggered
        """
        self._on_trigger = callback

    def start_checking(self, interval: int = 60):
        """Start background thread to check reminders.

        Args:
            interval: Check interval in seconds
        """
        if self._running:
            return

        self._running = True

        def check_loop():
            while self._running:
                try:
                    due = self.list_due()
                    for r in due:
                        if self._on_trigger:
                            self._on_trigger(r)
                        self.mark_triggered(r['id'])
                except Exception as e:
                    print(f"[!] Reminder check error: {e}")

                # Sleep in small increments to allow clean shutdown
                for _ in range(interval):
                    if not self._running:
                        break
                    threading.Event().wait(1)

        self._check_thread = threading.Thread(target=check_loop, daemon=True)
        self._check_thread.start()

    def stop_checking(self):
        """Stop background reminder checking."""
        self._running = False
        if self._check_thread:
            self._check_thread.join(timeout=5)
            self._check_thread = None


# Convenience functions

def parse_time_string(time_str: str) -> Optional[datetime]:
    """Parse a time string into datetime.

    Supports formats:
    - "in 5 minutes", "in 2 hours", "in 1 day"
    - "at 3pm", "at 14:30"
    - "tomorrow", "tomorrow at 9am"
    - ISO format "2024-01-15T14:30:00"

    Args:
        time_str: Time string to parse

    Returns:
        datetime or None if unparseable
    """
    time_str = time_str.lower().strip()
    now = datetime.now()

    # "in X minutes/hours/days"
    if time_str.startswith('in '):
        parts = time_str[3:].split()
        if len(parts) >= 2:
            try:
                amount = int(parts[0])
                unit = parts[1].rstrip('s')  # Remove trailing 's'

                if unit in ('minute', 'min'):
                    return now + timedelta(minutes=amount)
                elif unit in ('hour', 'hr'):
                    return now + timedelta(hours=amount)
                elif unit == 'day':
                    return now + timedelta(days=amount)
                elif unit == 'week':
                    return now + timedelta(weeks=amount)
            except ValueError:
                pass

    # "tomorrow" or "tomorrow at X"
    if time_str.startswith('tomorrow'):
        tomorrow = now + timedelta(days=1)
        tomorrow = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)

        if 'at ' in time_str:
            time_part = time_str.split('at ')[-1]
            parsed = _parse_time_only(time_part)
            if parsed:
                tomorrow = tomorrow.replace(hour=parsed[0], minute=parsed[1])

        return tomorrow

    # "at X" (today)
    if time_str.startswith('at '):
        time_part = time_str[3:]
        parsed = _parse_time_only(time_part)
        if parsed:
            result = now.replace(hour=parsed[0], minute=parsed[1], second=0, microsecond=0)
            # If time has passed, assume tomorrow
            if result <= now:
                result += timedelta(days=1)
            return result

    # Try ISO format
    try:
        return datetime.fromisoformat(time_str)
    except ValueError:
        pass

    return None


def _parse_time_only(time_str: str) -> Optional[tuple]:
    """Parse time-only string like '3pm' or '14:30'.

    Returns:
        (hour, minute) tuple or None
    """
    time_str = time_str.strip().lower()

    # "3pm", "3:30pm", "3 pm"
    is_pm = 'pm' in time_str
    is_am = 'am' in time_str
    time_str = time_str.replace('pm', '').replace('am', '').strip()

    try:
        if ':' in time_str:
            parts = time_str.split(':')
            hour = int(parts[0])
            minute = int(parts[1])
        else:
            hour = int(time_str)
            minute = 0

        if is_pm and hour < 12:
            hour += 12
        elif is_am and hour == 12:
            hour = 0

        return (hour, minute)
    except ValueError:
        return None


def format_reminder(reminder: Dict[str, Any]) -> str:
    """Format reminder for display.

    Args:
        reminder: Reminder dict

    Returns:
        Formatted string
    """
    rid = reminder.get('id', '?')
    text = reminder.get('text', '')
    time_str = reminder.get('time', '')
    enabled = reminder.get('enabled', True)
    repeat = reminder.get('repeat', '')

    status = "[ON]" if enabled else "[OFF]"

    try:
        time_obj = datetime.fromisoformat(time_str)
        time_display = time_obj.strftime('%Y-%m-%d %H:%M')
    except ValueError:
        time_display = time_str

    result = f"{rid} {status} {text} @ {time_display}"
    if repeat:
        result += f" (repeats {repeat})"

    return result


if __name__ == "__main__":
    # Test reminder system
    print("=== REMINDER MANAGER TEST ===")

    manager = ReminderManager()

    # List existing
    print(f"\nExisting reminders: {len(manager.list_all())}")

    # Test parsing
    print("\n=== TIME PARSING TEST ===")
    test_strings = [
        "in 5 minutes",
        "in 2 hours",
        "tomorrow",
        "tomorrow at 9am",
        "at 3pm",
        "at 14:30"
    ]

    for ts in test_strings:
        result = parse_time_string(ts)
        print(f"  '{ts}' -> {result}")

    print("\n=== FORMAT TEST ===")
    if manager.reminders:
        for r in manager.reminders[:3]:
            print(f"  {format_reminder(r)}")
