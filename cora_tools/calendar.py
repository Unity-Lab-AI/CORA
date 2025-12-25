"""
C.O.R.A Calendar Tools Module

Event and calendar management.
Per ARCHITECTURE.md v1.0.0: Calendar operations for scheduling.
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path


# Default calendar file path
CALENDAR_FILE = Path(__file__).parent.parent / 'data' / 'calendar.json'


def _load_calendar():
    """Load calendar data from file.

    Returns:
        dict: Calendar data with events list
    """
    try:
        if CALENDAR_FILE.exists():
            with open(CALENDAR_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"[!] Failed to load calendar: {e}")

    return {'counter': 0, 'events': []}


def _save_calendar(data):
    """Save calendar data to file.

    Args:
        data: Calendar data dict

    Returns:
        bool: True if saved successfully
    """
    try:
        # Ensure directory exists
        CALENDAR_FILE.parent.mkdir(parents=True, exist_ok=True)

        with open(CALENDAR_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[!] Failed to save calendar: {e}")
        return False


def add_event(title, start_time, duration_minutes=60, description='', location=''):
    """Add a new calendar event.

    Args:
        title: Event title
        start_time: Start time (datetime or ISO string)
        duration_minutes: Duration in minutes (default 60)
        description: Optional event description
        location: Optional location

    Returns:
        str: Event ID or None if failed
    """
    data = _load_calendar()

    # Generate ID
    data['counter'] = data.get('counter', 0) + 1
    event_id = f"E{data['counter']:03d}"

    # Parse start time
    if isinstance(start_time, str):
        start_time = datetime.fromisoformat(start_time)

    end_time = start_time + timedelta(minutes=duration_minutes)

    event = {
        'id': event_id,
        'title': title,
        'start': start_time.isoformat(),
        'end': end_time.isoformat(),
        'duration_minutes': duration_minutes,
        'description': description,
        'location': location,
        'created': datetime.now().isoformat()
    }

    data['events'].append(event)

    if _save_calendar(data):
        return event_id
    return None


def get_event(event_id):
    """Get a specific event by ID.

    Args:
        event_id: Event ID to find

    Returns:
        dict: Event data or None
    """
    data = _load_calendar()
    for event in data.get('events', []):
        if event.get('id') == event_id:
            return event
    return None


def delete_event(event_id):
    """Delete an event by ID.

    Args:
        event_id: Event ID to delete

    Returns:
        bool: True if deleted successfully
    """
    data = _load_calendar()
    events = data.get('events', [])

    for i, event in enumerate(events):
        if event.get('id') == event_id:
            events.pop(i)
            return _save_calendar(data)

    return False


def get_today_events():
    """Get all events for today.

    Returns:
        list: Events scheduled for today
    """
    data = _load_calendar()
    today = datetime.now().date()

    today_events = []
    for event in data.get('events', []):
        try:
            start = datetime.fromisoformat(event['start'])
            if start.date() == today:
                today_events.append(event)
        except Exception:
            continue

    # Sort by start time
    today_events.sort(key=lambda e: e['start'])
    return today_events


def get_upcoming(days=7):
    """Get upcoming events for next N days.

    Args:
        days: Number of days to look ahead

    Returns:
        list: Upcoming events
    """
    data = _load_calendar()
    now = datetime.now()
    end_date = now + timedelta(days=days)

    upcoming = []
    for event in data.get('events', []):
        try:
            start = datetime.fromisoformat(event['start'])
            if now <= start <= end_date:
                upcoming.append(event)
        except Exception:
            continue

    # Sort by start time
    upcoming.sort(key=lambda e: e['start'])
    return upcoming


def get_events_on_date(date):
    """Get events on a specific date.

    Args:
        date: Date to check (datetime.date or string 'YYYY-MM-DD')

    Returns:
        list: Events on that date
    """
    if isinstance(date, str):
        date = datetime.strptime(date, '%Y-%m-%d').date()

    data = _load_calendar()

    events = []
    for event in data.get('events', []):
        try:
            start = datetime.fromisoformat(event['start'])
            if start.date() == date:
                events.append(event)
        except Exception:
            continue

    events.sort(key=lambda e: e['start'])
    return events


def format_event_time(event):
    """Format event time for display.

    Args:
        event: Event dict

    Returns:
        str: Formatted time string (e.g., "10:00 AM - 11:00 AM")
    """
    try:
        start = datetime.fromisoformat(event['start'])
        end = datetime.fromisoformat(event['end'])
        return f"{start.strftime('%I:%M %p')} - {end.strftime('%I:%M %p')}"
    except Exception:
        return "Time unknown"


def get_events_summary(events):
    """Get spoken summary of events for TTS.

    Args:
        events: List of event dicts

    Returns:
        str: Natural language summary
    """
    if not events:
        return "You have no events scheduled."

    count = len(events)
    if count == 1:
        event = events[0]
        start = datetime.fromisoformat(event['start'])
        return f"You have {event['title']} at {start.strftime('%I:%M %p')}."

    # Multiple events
    summary_parts = [f"You have {count} things today."]
    for event in events[:3]:  # Limit to first 3 for TTS
        start = datetime.fromisoformat(event['start'])
        summary_parts.append(f"{event['title']} at {start.strftime('%I:%M %p')}")

    if count > 3:
        summary_parts.append(f"and {count - 3} more.")

    return ' '.join(summary_parts)


def remind_me(text, remind_time, repeat=None):
    """Create a reminder (stored as special event type).

    Args:
        text: Reminder text
        remind_time: When to remind (datetime or ISO string)
        repeat: Optional repeat pattern ('daily', 'weekly', None)

    Returns:
        str: Reminder ID or None
    """
    data = _load_calendar()

    data['counter'] = data.get('counter', 0) + 1
    reminder_id = f"R{data['counter']:03d}"

    if isinstance(remind_time, str):
        remind_time = datetime.fromisoformat(remind_time)

    reminder = {
        'id': reminder_id,
        'type': 'reminder',
        'text': text,
        'time': remind_time.isoformat(),
        'repeat': repeat,
        'created': datetime.now().isoformat(),
        'triggered': False
    }

    if 'reminders' not in data:
        data['reminders'] = []

    data['reminders'].append(reminder)

    if _save_calendar(data):
        return reminder_id
    return None


def get_pending_reminders():
    """Get all pending reminders that should trigger.

    Returns:
        list: Reminders that are due
    """
    data = _load_calendar()
    now = datetime.now()

    pending = []
    for reminder in data.get('reminders', []):
        if reminder.get('triggered'):
            continue
        try:
            remind_time = datetime.fromisoformat(reminder['time'])
            if remind_time <= now:
                pending.append(reminder)
        except Exception:
            continue

    return pending


def mark_reminder_triggered(reminder_id):
    """Mark a reminder as triggered.

    Args:
        reminder_id: Reminder ID

    Returns:
        bool: True if updated successfully
    """
    data = _load_calendar()

    for reminder in data.get('reminders', []):
        if reminder.get('id') == reminder_id:
            reminder['triggered'] = True
            reminder['triggered_at'] = datetime.now().isoformat()
            return _save_calendar(data)

    return False
