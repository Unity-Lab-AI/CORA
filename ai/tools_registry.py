#!/usr/bin/env python3
"""
C.O.R.A tool registry — every capability CORA has, described once as a
JSON-schema tool the model can call natively (or through the JSON fallback
protocol in ai/dispatcher.py).

Each Tool maps a name + parameter schema to a Python callable. Implementations
import lazily so one broken optional dependency never takes the registry down,
and each call is wrapped so a tool error comes back as data, never as a crash.

Tools flagged `confirm=True` are destructive or run code; the dispatcher asks
the user before executing them.

UI surfaces (boot display, GUI app, CLI) register their own tools at runtime
with register_tool(); e.g. the boot display registers open_camera_window.
"""

import json
import os
import re
import subprocess
import sys
import webbrowser
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))


@dataclass
class Tool:
    name: str
    description: str
    func: Callable[..., Any]
    params: Dict[str, Dict[str, Any]] = field(default_factory=dict)   # name -> {type, description, enum?}
    required: List[str] = field(default_factory=list)
    confirm: bool = False
    category: str = 'general'
    speak_result: bool = False     # result is already user-facing prose

    def schema(self) -> Dict[str, Any]:
        props = {}
        for n, p in self.params.items():
            q = {'type': p.get('type', 'string'), 'description': p.get('description', '')}
            if 'enum' in p:
                q['enum'] = p['enum']
            props[n] = q
        return {'type': 'function', 'function': {
            'name': self.name, 'description': self.description,
            'parameters': {'type': 'object', 'properties': props, 'required': list(self.required)}}}


_REGISTRY: Dict[str, Tool] = {}


def register_tool(tool: Tool):
    _REGISTRY[tool.name] = tool


def unregister_tool(name: str):
    _REGISTRY.pop(name, None)


def get_tool(name: str) -> Optional[Tool]:
    return _REGISTRY.get(name)


def all_tools() -> List[Tool]:
    return list(_REGISTRY.values())


def tool_schemas(categories: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    return [t.schema() for t in _REGISTRY.values() if not categories or t.category in categories]


def tool_catalog_text() -> str:
    """Compact human/LLM-readable catalog (used by the JSON fallback protocol and /help)."""
    lines = []
    by_cat: Dict[str, List[Tool]] = {}
    for t in _REGISTRY.values():
        by_cat.setdefault(t.category, []).append(t)
    for cat in sorted(by_cat):
        lines.append(f"[{cat}]")
        for t in by_cat[cat]:
            args = ", ".join(f"{n}{'' if n in t.required else '?'}" for n in t.params)
            lines.append(f"  {t.name}({args}) - {t.description}")
    return "\n".join(lines)


def _p(desc: str, type_: str = 'string', enum: Optional[List[str]] = None) -> Dict[str, Any]:
    d = {'type': type_, 'description': desc}
    if enum:
        d['enum'] = enum
    return d


def _ok(msg: str, **data) -> Dict[str, Any]:
    out = {'ok': True, 'message': msg}
    out.update(data)
    return out


def _err(msg: str, **data) -> Dict[str, Any]:
    out = {'ok': False, 'error': msg}
    out.update(data)
    return out


def _tool(name, desc, category, params=None, required=None, confirm=False, speak_result=False):
    """Decorator: define a tool from a function."""
    def deco(func):
        register_tool(Tool(name=name, description=desc, func=func, params=params or {},
                           required=required or [], confirm=confirm, category=category,
                           speak_result=speak_result))
        return func
    return deco


# =========================================================================== time / weather / location
@_tool('get_time', 'Current local time and date.', 'time')
def t_get_time():
    now = datetime.now()
    return _ok(f"It's {now.strftime('%I:%M %p').lstrip('0')} on {now.strftime('%A, %B %d, %Y')}",
               time=now.strftime('%H:%M'), date=now.strftime('%Y-%m-%d'), weekday=now.strftime('%A'))


@_tool('get_weather', 'Current weather (city optional, defaults to the user\'s location).', 'time',
       {'location': _p('City name, optional')})
def t_get_weather(location: str = None):
    from services.weather import get_weather
    w = get_weather(location or None)
    if not w or not w.get('success'):
        return _err('weather unavailable')
    return _ok(f"{w.get('temp')} and {w.get('conditions')}", **{k: v for k, v in w.items() if k != 'success'})


@_tool('get_forecast', 'Multi-day weather forecast.', 'time',
       {'location': _p('City name, optional'), 'days': _p('Number of days (1-5)', 'integer')})
def t_get_forecast(location: str = None, days: int = 3):
    from services.weather import get_forecast
    f = get_forecast(location or None, days=int(days or 3))
    if not f or not f.get('success'):
        return _err('forecast unavailable')
    return _ok('forecast', forecast=f.get('forecast'))


@_tool('get_location', 'Where the user is (city/region/country from IP).', 'time')
def t_get_location():
    from services.location import get_location, format_location_string
    loc = get_location()
    return _ok(format_location_string(loc), **(loc or {})) if loc else _err('location unavailable')


# =========================================================================== tasks
@_tool('add_task', 'Create a task/todo item.', 'tasks',
       {'text': _p('Task description'), 'priority': _p('1 (highest) to 10', 'integer'),
        'due': _p('Due date YYYY-MM-DD or +Nd')}, ['text'])
def _normalize_due(due: Optional[str]) -> Optional[str]:
    """Accept YYYY-MM-DD, +Nd, or natural language ("tomorrow", "next friday") -> YYYY-MM-DD."""
    if not due:
        return None
    d = str(due).strip()
    if re.match(r'^\d{4}-\d{2}-\d{2}$', d) or re.match(r'^\+\d+d$', d):
        return d
    dt = _parse_when(d)
    return dt.strftime('%Y-%m-%d') if dt else None


def t_add_task(text: str, priority: int = None, due: str = None):
    from cora_tools import tasks as T
    tid = T.add_task(text)
    if not tid:
        return _err('could not add task')
    if priority is not None:
        T.set_priority(tid, int(priority))
    due_norm = _normalize_due(due)
    if due and not due_norm:
        return _ok(f"Added task {tid}: {text} (could not understand due date '{due}')", id=tid)
    if due_norm:
        T.set_due(tid, due_norm)
    return _ok(f"Added task {tid}: {text}" + (f", due {due_norm}" if due_norm else ''), id=tid, due=due_norm)


@_tool('list_tasks', 'List tasks.', 'tasks',
       {'filter': _p('all, pending, done or overdue', enum=['all', 'pending', 'done', 'overdue'])})
def t_list_tasks(filter: str = 'pending'):
    from cora_tools import tasks as T
    items = T.list_tasks(filter or 'pending')
    brief = [{'id': t.get('id'), 'text': t.get('text'), 'status': t.get('status'),
              'priority': t.get('priority'), 'due': t.get('due')} for t in items[:25]]
    return _ok(f"{len(items)} task(s)", tasks=brief)


@_tool('complete_task', 'Mark a task done.', 'tasks', {'task_id': _p('Task id like T003')}, ['task_id'])
def t_complete_task(task_id: str):
    from cora_tools import tasks as T
    return _ok(f"{task_id} done") if T.complete_task(task_id.upper()) else _err(f"{task_id} not found")


@_tool('delete_task', 'Delete a task permanently.', 'tasks', {'task_id': _p('Task id')}, ['task_id'], confirm=True)
def t_delete_task(task_id: str):
    from cora_tools import tasks as T
    return _ok(f"{task_id} deleted") if T.delete_task(task_id.upper()) else _err(f"{task_id} not found")


@_tool('set_task_priority', 'Set a task priority (1 highest, 10 lowest).', 'tasks',
       {'task_id': _p('Task id'), 'level': _p('1-10', 'integer')}, ['task_id', 'level'])
def t_set_task_priority(task_id: str, level: int):
    from cora_tools import tasks as T
    return _ok('priority set') if T.set_priority(task_id.upper(), int(level)) else _err('task not found')


@_tool('set_task_due', 'Set a task due date.', 'tasks',
       {'task_id': _p('Task id'), 'date': _p('YYYY-MM-DD or +Nd')}, ['task_id', 'date'])
def t_set_task_due(task_id: str, date: str):
    from cora_tools import tasks as T
    d = _normalize_due(date)
    if not d:
        return _err(f"could not understand date '{date}'")
    return _ok(f'due date set to {d}') if T.set_due(task_id.upper(), d) else _err('task not found')


@_tool('add_task_note', 'Add a note to a task.', 'tasks',
       {'task_id': _p('Task id'), 'text': _p('Note text')}, ['task_id', 'text'])
def t_add_task_note(task_id: str, text: str):
    from cora_tools import tasks as T
    return _ok('note added') if T.add_note(task_id.upper(), text) else _err('task not found')


@_tool('search_tasks', 'Search tasks by text.', 'tasks', {'query': _p('Search text')}, ['query'])
def t_search_tasks(query: str):
    from cora_tools import tasks as T
    items = T.search_tasks(query)
    return _ok(f"{len(items)} match(es)", tasks=[{'id': t.get('id'), 'text': t.get('text')} for t in items[:20]])


# =========================================================================== knowledge + memory
_KB = PROJECT_DIR / 'data' / 'knowledge.json'


def _kb_load():
    try:
        with open(_KB, 'r', encoding='utf-8') as f:
            d = json.load(f)
        return d.get('counter', 0), d.get('entries', [])
    except Exception:
        return 0, []


def _kb_save(counter, entries):
    _KB.parent.mkdir(parents=True, exist_ok=True)
    tmp = _KB.with_suffix('.json.tmp')
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump({'counter': counter, 'entries': entries}, f, indent=2)
    os.replace(tmp, _KB)


@_tool('learn', 'Store a fact in the long-term knowledge base.', 'memory',
       {'text': _p('The fact to remember'), 'tags': _p('Comma-separated tags, optional')}, ['text'])
def t_learn(text: str, tags: str = ''):
    counter, entries = _kb_load()
    counter += 1
    tag_list = [t.strip().lstrip('#') for t in (tags or '').split(',') if t.strip()]
    entry = {'id': f"K{counter:03d}", 'content': text, 'tags': tag_list, 'created': datetime.now().isoformat()}
    entries.append(entry)
    _kb_save(counter, entries)
    return _ok(f"Learned {entry['id']}", id=entry['id'])


@_tool('recall_knowledge', 'Search the long-term knowledge base.', 'memory',
       {'query': _p('Words to search for (optional)'), 'tag': _p('Tag filter (optional)')})
def t_recall(query: str = '', tag: str = ''):
    _, entries = _kb_load()
    q = (query or '').lower().strip()
    tg = (tag or '').lstrip('#').lower().strip()
    hits = [e for e in entries
            if (not tg or tg in [t.lower() for t in e.get('tags', [])])
            and (not q or all(w in e.get('content', '').lower() for w in q.split()))]
    return _ok(f"{len(hits)} entr{'y' if len(hits) == 1 else 'ies'}",
               entries=[{'id': e['id'], 'content': e['content'], 'tags': e.get('tags', [])} for e in hits[-15:]])


@_tool('forget_knowledge', 'Delete a knowledge entry by id.', 'memory', {'entry_id': _p('Knowledge id like K004')}, ['entry_id'], confirm=True)
def t_forget_knowledge(entry_id: str):
    counter, entries = _kb_load()
    kept = [e for e in entries if e.get('id') != entry_id.upper()]
    if len(kept) == len(entries):
        return _err('not found')
    _kb_save(counter, kept)
    return _ok(f"forgot {entry_id}")


@_tool('remember', 'Store a key/value in working memory (names, preferences, short facts).', 'memory',
       {'key': _p('Name of the thing'), 'value': _p('What to remember')}, ['key', 'value'])
def t_remember(key: str, value: str):
    from cora_tools.memory import remember
    return _ok(f"remembered {key}") if remember(key, value) else _err('memory write failed')


@_tool('recall_memory', 'Recall from working memory (all entries when key omitted).', 'memory', {'key': _p('Key, optional')})
def t_recall_memory(key: str = None):
    from cora_tools.memory import recall
    v = recall(key or None)
    return _ok('memory', value=v) if v not in (None, {}, []) else _err('nothing stored')


@_tool('forget_memory', 'Remove a working-memory key.', 'memory', {'key': _p('Key')}, ['key'])
def t_forget_memory(key: str):
    from cora_tools.memory import forget
    return _ok('forgotten') if forget(key) else _err('no such key')


# =========================================================================== calendar + reminders
def _parse_when(when: str) -> Optional[datetime]:
    from cora_tools.reminders import parse_time_string
    for cand in (when, f"in {when}", f"at {when}"):
        try:
            dt = parse_time_string(cand)
            if dt:
                return dt
        except Exception:
            pass
    try:
        return datetime.fromisoformat(when)
    except Exception:
        return None


@_tool('add_event', 'Add a calendar event.', 'calendar',
       {'title': _p('Event title'), 'start': _p('When: ISO datetime or natural like "tomorrow 3pm"'),
        'duration_minutes': _p('Length in minutes', 'integer'), 'description': _p('Optional details'),
        'location': _p('Optional place')}, ['title', 'start'])
def t_add_event(title: str, start: str, duration_minutes: int = 60, description: str = '', location: str = ''):
    from cora_tools.calendar import add_event
    dt = _parse_when(start)
    if not dt:
        return _err(f"could not understand time: {start}")
    ev = add_event(title, dt.isoformat(), int(duration_minutes or 60), description or '', location or '')
    return _ok(f"Event '{title}' at {dt.strftime('%A %I:%M %p')}", event=ev)


@_tool('today_events', "Today's calendar events.", 'calendar')
def t_today_events():
    from cora_tools.calendar import get_today_events, get_events_summary
    ev = get_today_events()
    return _ok(get_events_summary(ev), events=ev)


@_tool('upcoming_events', 'Calendar events for the next N days.', 'calendar', {'days': _p('Days ahead', 'integer')})
def t_upcoming_events(days: int = 7):
    from cora_tools.calendar import get_upcoming
    ev = get_upcoming(int(days or 7))
    return _ok(f"{len(ev)} upcoming", events=ev)


@_tool('delete_event', 'Delete a calendar event by id.', 'calendar', {'event_id': _p('Event id')}, ['event_id'], confirm=True)
def t_delete_event(event_id: str):
    from cora_tools.calendar import delete_event
    return _ok('deleted') if delete_event(event_id) else _err('not found')


@_tool('set_reminder', 'Set a reminder that will be spoken and shown when due.', 'calendar',
       {'text': _p('What to remind'), 'when': _p('"in 20 minutes", "at 3pm", "tomorrow 9am", or ISO datetime'),
        'repeat': _p('none, daily, weekly, monthly', enum=['none', 'daily', 'weekly', 'monthly'])}, ['text', 'when'])
def t_set_reminder(text: str, when: str, repeat: str = 'none'):
    from cora_tools.reminders import ReminderManager
    dt = _parse_when(when)
    if not dt:
        return _err(f"could not understand time: {when}")
    rid = ReminderManager().add(text, dt, repeat=None if repeat in (None, '', 'none') else repeat)
    return _ok(f"Reminder {rid} set for {dt.strftime('%A %I:%M %p')}", id=rid, time=dt.isoformat())


@_tool('list_reminders', 'List reminders.', 'calendar')
def t_list_reminders():
    from cora_tools.reminders import ReminderManager
    rs = ReminderManager().list_all()
    return _ok(f"{len(rs)} reminder(s)", reminders=[{'id': r['id'], 'text': r['text'], 'time': r.get('time'),
                                                     'enabled': r.get('enabled', True)} for r in rs])


@_tool('delete_reminder', 'Delete a reminder by id.', 'calendar', {'reminder_id': _p('Reminder id like R002')}, ['reminder_id'], confirm=True)
def t_delete_reminder(reminder_id: str):
    from cora_tools.reminders import ReminderManager
    return _ok('deleted') if ReminderManager().remove(reminder_id.upper()) else _err('not found')


# =========================================================================== vision + images
@_tool('take_screenshot', 'Capture the desktop; optionally describe it with vision.', 'vision',
       {'question': _p('What to look for / describe (optional). If given, the screenshot is analysed.')})
def t_take_screenshot(question: str = None):
    from cora_tools.screenshots import desktop
    r = desktop()
    if not r.success:
        return _err(r.error or 'screenshot failed')
    out = {'path': str(r.path), 'size': f"{r.width}x{r.height}"}
    if question:
        from ai.ollama import generate_with_image
        v = generate_with_image(question, str(r.path))
        out['description'] = v.content if not v.error else f"vision error: {v.error}"
        return _ok(out['description'], **out)
    return _ok(f"Screenshot saved to {r.path}", **out)


@_tool('look_camera', 'Look through the webcam and describe/answer a question about what is visible.', 'vision',
       {'question': _p('Question about the view, optional')})
def t_look_camera(question: str = None):
    from services.presence import capture_webcam, ask_vision
    p = capture_webcam()
    if not p:
        return _err('camera unavailable')
    desc = ask_vision(p, question or 'Describe what you see in detail: people, objects, environment, mood.')
    return _ok(desc or 'vision returned nothing', path=str(p))


@_tool('check_presence', 'Is someone at the desk? Includes emotion/activity when visible.', 'vision')
def t_check_presence():
    from services.presence import full_human_check
    r = full_human_check()
    if r.error:
        return _err(r.error)
    return _ok('present' if r.present else 'nobody there', present=r.present, emotion=r.emotion,
               activity=r.activity, posture=r.posture, holding=r.holding)


@_tool('open_camera', 'Open the live webcam window.', 'vision')
def t_open_camera():
    from ui.camera_feed import open_live_camera
    cam = open_live_camera()
    return _ok('camera window open') if cam else _err('could not open camera')


@_tool('close_camera', 'Close the live webcam window.', 'vision')
def t_close_camera():
    from ui.camera_feed import close_live_camera
    close_live_camera()
    return _ok('camera closed')


@_tool('generate_image', 'Generate an image from a prompt (Pollinations) and show it.', 'images',
       {'prompt': _p('Detailed image description'), 'width': _p('Pixels', 'integer'), 'height': _p('Pixels', 'integer'),
        'show': _p('Open the result in a window', 'boolean')}, ['prompt'])
def t_generate_image(prompt: str, width: int = 1024, height: int = 1024, show: bool = True):
    from cora_tools.image_gen import generate_image, show_fullscreen_image
    r = generate_image(prompt, width=int(width or 1024), height=int(height or 1024))
    if not r.get('success'):
        return _err(r.get('error', 'generation failed'))
    if show:
        try:
            from ui.fullscreen_image import show_image_async
            show_image_async(r['path'])
        except Exception:
            try:
                show_fullscreen_image(r['path'], duration=15)
            except Exception:
                pass
    return _ok(f"Image generated in {r.get('inference_time', 0):.1f}s", path=r['path'], model=r.get('model'))


@_tool('recent_images', 'List recently generated images.', 'images', {'limit': _p('How many', 'integer')})
def t_recent_images(limit: int = 5):
    from cora_tools.image_gen import get_recent_images
    return _ok('images', images=get_recent_images(int(limit or 5)))


# =========================================================================== web
@_tool('web_search', 'Search the web (DuckDuckGo) and return top results.', 'web',
       {'query': _p('Search query'), 'num_results': _p('How many', 'integer')}, ['query'])
def t_web_search(query: str, num_results: int = 5):
    from cora_tools.web import web_search
    r = web_search(query, int(num_results or 5))
    return r if isinstance(r, dict) else _ok(str(r))


@_tool('fetch_url', 'Fetch a web page as readable text.', 'web', {'url': _p('http(s) URL')}, ['url'])
def t_fetch_url(url: str):
    from cora_tools.web import fetch_url
    r = fetch_url(url)
    if isinstance(r, dict) and r.get('text'):
        r['text'] = r['text'][:6000]
    return r if isinstance(r, dict) else _ok(str(r)[:6000])


@_tool('summarize_url', 'Fetch a page and summarize it.', 'web', {'url': _p('http(s) URL')}, ['url'])
def t_summarize_url(url: str):
    from cora_tools.web import summarize_url
    r = summarize_url(url)
    return r if isinstance(r, dict) else _ok(str(r))


@_tool('open_in_browser', "Open a URL in the user's default browser.", 'web', {'url': _p('URL')}, ['url'])
def t_open_in_browser(url: str):
    if not url.lower().startswith(('http://', 'https://')):
        url = 'https://' + url
    webbrowser.open(url)
    return _ok(f"opened {url}")


@_tool('browse_screenshot', 'Load a page in a headless browser and screenshot it (Playwright).', 'web', {'url': _p('URL')}, ['url'])
def t_browse_screenshot(url: str):
    from cora_tools.browser import browse_sync
    return browse_sync(url)


# =========================================================================== files
@_tool('read_file', 'Read a text file (inside allowed folders).', 'files', {'path': _p('File path')}, ['path'])
def t_read_file(path: str):
    from cora_tools.files import read_file
    c = read_file(path)
    return _ok('read', content=c[:8000], truncated=len(c) > 8000) if c is not None else _err('cannot read')


@_tool('write_file', 'Create or overwrite a text file.', 'files',
       {'path': _p('File path'), 'content': _p('Text content'), 'overwrite': _p('Overwrite if exists', 'boolean')}, ['path', 'content'])
def t_write_file(path: str, content: str, overwrite: bool = True):
    from cora_tools.files import create_file
    return _ok(f"wrote {path}") if create_file(path, content, overwrite=bool(overwrite)) else _err('write refused')


@_tool('append_file', 'Append text to a file.', 'files', {'path': _p('File path'), 'content': _p('Text')}, ['path', 'content'])
def t_append_file(path: str, content: str):
    from cora_tools.files import append_file
    return _ok('appended') if append_file(path, content) else _err('append refused')


@_tool('list_directory', 'List files in a folder.', 'files',
       {'path': _p('Folder path'), 'recursive': _p('Include subfolders', 'boolean')}, ['path'])
def t_list_directory(path: str, recursive: bool = False):
    from cora_tools.files import list_directory
    files = list_directory(path, recursive=bool(recursive))
    return _ok(f"{len(files)} file(s)", files=files[:200])


@_tool('file_info', 'Size/dates of a file.', 'files', {'path': _p('Path')}, ['path'])
def t_file_info(path: str):
    from cora_tools.files import get_file_info
    i = get_file_info(path)
    return _ok('info', **i) if i else _err('not found')


@_tool('search_in_file', 'Find lines containing text in a file.', 'files', {'path': _p('Path'), 'query': _p('Text')}, ['path', 'query'])
def t_search_in_file(path: str, query: str):
    from cora_tools.files import search_in_file
    hits = search_in_file(path, query)
    return _ok(f"{len(hits)} line(s)", lines=hits[:50])


@_tool('search_files', 'Find files by name under a folder.', 'files',
       {'query': _p('Name fragment'), 'path': _p('Folder (optional)')}, ['query'])
def t_search_files(query: str, path: str = None):
    from cora_tools.system import search_files
    r = search_files(query, path)
    return _ok('results', results=(r or [])[:100]) if r is not None else _err('search failed')


@_tool('delete_file', 'Delete a file.', 'files', {'path': _p('Path')}, ['path'], confirm=True)
def t_delete_file(path: str):
    from cora_tools.files import delete_file
    return _ok('deleted') if delete_file(path) else _err('delete refused')


@_tool('move_file', 'Move/rename a file.', 'files', {'source': _p('From'), 'destination': _p('To')}, ['source', 'destination'], confirm=True)
def t_move_file(source: str, destination: str):
    from cora_tools.files import move_file
    return _ok('moved') if move_file(source, destination, overwrite=False) else _err('move refused')


@_tool('copy_file', 'Copy a file.', 'files', {'source': _p('From'), 'destination': _p('To')}, ['source', 'destination'])
def t_copy_file(source: str, destination: str):
    from cora_tools.files import copy_file
    return _ok('copied') if copy_file(source, destination) else _err('copy refused')


@_tool('create_directory', 'Create a folder.', 'files', {'path': _p('Folder path')}, ['path'])
def t_create_directory(path: str):
    from cora_tools.files import create_directory
    return _ok('created') if create_directory(path) else _err('refused')


@_tool('open_path', 'Open a file, folder, or launch an application by name.', 'files', {'target': _p('Path or app name')}, ['target'])
def t_open_path(target: str):
    from cora_tools.system import open_file, open_folder, launch_app
    if os.path.isdir(target):
        return _ok('opened folder') if open_folder(target) else _err('could not open folder')
    if os.path.exists(target):
        return _ok('opened file') if open_file(target) else _err('could not open file')
    return _ok(f"launched {target}") if launch_app(target) else _err(f"could not open or launch {target}")


# =========================================================================== system
@_tool('system_stats', 'CPU, RAM, disk, GPU usage.', 'system')
def t_system_stats():
    from cora_tools.system import get_system_info, get_gpu_info
    info = get_system_info() or {}
    try:
        info['gpu'] = get_gpu_info()
    except Exception:
        pass
    return _ok('stats', **info)


@_tool('running_processes', 'List running processes (optionally filtered).', 'system', {'filter': _p('Name fragment, optional')})
def t_running_processes(filter: str = None):
    from cora_tools.system import get_running_processes
    procs = get_running_processes() or []
    if filter:
        f = filter.lower()
        procs = [p for p in procs if f in str(p).lower()]
    return _ok(f"{len(procs)} process(es)", processes=procs[:60])


@_tool('kill_process', 'End a process by name.', 'system', {'name': _p('Process name')}, ['name'], confirm=True)
def t_kill_process(name: str):
    from cora_tools.system import kill_process
    return _ok(f"killed {name}") if kill_process(name) else _err('could not kill')


@_tool('set_system_volume', 'Set master volume 0-100.', 'system', {'level': _p('0-100', 'integer')}, ['level'])
def t_set_system_volume(level: int):
    from cora_tools.system import set_volume
    return _ok(f"volume {level}") if set_volume(int(level)) else _err('volume control unavailable')


@_tool('notify', 'Show a desktop notification.', 'system', {'title': _p('Title'), 'message': _p('Body')}, ['title', 'message'])
def t_notify(title: str, message: str):
    from cora_tools.system import notify
    notify(title, message)
    return _ok('notified')


@_tool('clipboard_copy', 'Put text on the clipboard.', 'system', {'text': _p('Text')}, ['text'])
def t_clipboard_copy(text: str):
    from cora_tools.system import clipboard_copy
    return _ok('copied') if clipboard_copy(text) else _err('clipboard unavailable')


@_tool('clipboard_paste', 'Read the clipboard.', 'system')
def t_clipboard_paste():
    from cora_tools.system import clipboard_paste
    return _ok('clipboard', text=str(clipboard_paste() or '')[:4000])


@_tool('calculate', 'Evaluate a math expression safely.', 'system', {'expression': _p('e.g. 12*(3+4)/7')}, ['expression'])
def t_calculate(expression: str):
    from cora_tools.system import calculate
    r = calculate(expression)
    return r if isinstance(r, dict) else _ok(str(r))


@_tool('run_shell', 'Run a shell command and return its output.', 'system',
       {'command': _p('Command line'), 'timeout': _p('Seconds', 'integer')}, ['command'], confirm=True)
def t_run_shell(command: str, timeout: int = 30):
    from cora_tools.system import run_shell
    r = run_shell(command, timeout=int(timeout or 30))
    if isinstance(r, dict):
        for k in ('stdout', 'output', 'stderr'):
            if isinstance(r.get(k), str):
                r[k] = r[k][-4000:]
    return r


# =========================================================================== windows
@_tool('list_windows', 'List open application windows.', 'windows')
def t_list_windows():
    from cora_tools.windows import list_windows
    return _ok('windows', windows=list_windows()[:60])


@_tool('focus_window', 'Bring a window to the front.', 'windows', {'name': _p('Window/app title fragment')}, ['name'])
def t_focus_window(name: str):
    from cora_tools.windows import focus_window
    return _ok('focused') if focus_window(name) else _err('window not found')


@_tool('minimize_window', 'Minimize a window.', 'windows', {'name': _p('Title fragment')}, ['name'])
def t_minimize_window(name: str):
    from cora_tools.windows import minimize_window
    return _ok('minimized') if minimize_window(name) else _err('window not found')


@_tool('maximize_window', 'Maximize a window.', 'windows', {'name': _p('Title fragment')}, ['name'])
def t_maximize_window(name: str):
    from cora_tools.windows import maximize_window
    return _ok('maximized') if maximize_window(name) else _err('window not found')


@_tool('close_window', 'Close a window.', 'windows', {'name': _p('Title fragment')}, ['name'], confirm=True)
def t_close_window(name: str):
    from cora_tools.windows import close_window
    return _ok('closed') if close_window(name) else _err('window not found')


@_tool('arrange_windows', 'Tile/arrange open windows.', 'windows',
       {'layout': _p('Layout', enum=['tile_horizontal', 'tile_vertical', 'cascade', 'grid'])})
def t_arrange_windows(layout: str = 'tile_horizontal'):
    from cora_tools.windows import arrange_windows
    return _ok('arranged') if arrange_windows(layout or 'tile_horizontal') else _err('arrange failed')


# =========================================================================== code
@_tool('explain_code', 'Explain a code snippet.', 'code', {'code': _p('Source code'), 'detail': _p('low, medium, high', enum=['low', 'medium', 'high'])}, ['code'])
def t_explain_code(code: str, detail: str = 'medium'):
    from cora_tools.code import explain_code
    return _ok(explain_code(code, detail or 'medium'))


@_tool('write_code', 'Generate code from a description.', 'code', {'description': _p('What to build'), 'language': _p('Language')}, ['description'])
def t_write_code(description: str, language: str = 'python'):
    from cora_tools.code import write_code
    return _ok(write_code(description, language or 'python'))


@_tool('fix_code', 'Fix a code snippet (optionally given the error).', 'code', {'code': _p('Code'), 'error': _p('Error text, optional')}, ['code'])
def t_fix_code(code: str, error: str = None):
    from cora_tools.code import fix_code
    return _ok(fix_code(code, error))


@_tool('analyze_code', 'Analyze code for issues.', 'code', {'code': _p('Code')}, ['code'])
def t_analyze_code(code: str):
    from cora_tools.code import analyze_code
    a = analyze_code(code)
    return _ok('analysis', **(a.__dict__ if hasattr(a, '__dict__') else {'result': str(a)}))


@_tool('run_code', 'Execute a code snippet and return its output.', 'code',
       {'code': _p('Code'), 'language': _p('python/js/bash, optional')}, ['code'], confirm=True)
def t_run_code(code: str, language: str = None):
    from cora_tools.code import run_code
    r = run_code(code, language, safe_mode=True)
    return _ok('ran', **(r.__dict__ if hasattr(r, '__dict__') else {'result': str(r)}))


@_tool('open_code_editor', 'Open the CORA code editor (optionally on a file).', 'code', {'path': _p('File path, optional')})
def t_open_code_editor(path: str = None):
    from ui.code_editor import open_code_editor
    open_code_editor(file_path=path) if path else open_code_editor()
    return _ok('editor open')


@_tool('open_folder_in_editor', 'Open a folder tree in the code editor.', 'code', {'path': _p('Folder')}, ['path'])
def t_open_folder_in_editor(path: str):
    from ui.code_editor import open_folder
    open_folder(path)
    return _ok('folder open in editor')


@_tool('open_github_in_editor', 'Open a GitHub repository in the code editor.', 'code', {'url': _p('Repo URL')}, ['url'])
def t_open_github_in_editor(url: str):
    from ui.code_editor import open_github_repo
    open_github_repo(url)
    return _ok('repo open in editor')


# =========================================================================== media
def _media(fn, *a):
    from cora_tools import media as M
    msg = getattr(M, fn)(*a)
    ok = not str(msg).startswith('[!]')
    return (_ok if ok else _err)(str(msg).replace('[+] ', '').replace('[!] ', ''))


@_tool('media_play', 'Play media: a file path, a YouTube URL, a search like "lofi beats", or empty to toggle play/pause.', 'media',
       {'target': _p('File, URL, or search; optional')})
def t_media_play(target: str = None):
    return _media('play', target or None)


@_tool('media_pause', 'Pause playback.', 'media')
def t_media_pause():
    return _media('pause')


@_tool('media_resume', 'Resume playback.', 'media')
def t_media_resume():
    return _media('resume')


@_tool('media_stop', 'Stop playback.', 'media')
def t_media_stop():
    return _media('stop')


@_tool('media_next', 'Next track.', 'media')
def t_media_next():
    return _media('next_track')


@_tool('media_previous', 'Previous track.', 'media')
def t_media_previous():
    return _media('prev_track')


@_tool('media_volume', 'Get or set media volume 0-100.', 'media', {'level': _p('0-100, omit to read', 'integer')})
def t_media_volume(level: int = None):
    return _media('volume', int(level)) if level is not None else _media('volume')


@_tool('media_mute', 'Toggle mute.', 'media')
def t_media_mute():
    return _media('mute')


@_tool('now_playing', "What's playing now.", 'media')
def t_now_playing():
    return _media('now')


# =========================================================================== git / github
def _git(fn, *a):
    from cora_tools import git_ops as G
    r = getattr(G, fn)(*a)
    return r if isinstance(r, dict) else _ok(str(r))


@_tool('git_status', 'Git status of the project repo.', 'git')
def t_git_status():
    return _git('git_status')


@_tool('git_pull', 'git pull.', 'git')
def t_git_pull():
    return _git('git_pull')


@_tool('git_push', 'git push.', 'git', confirm=True)
def t_git_push():
    return _git('git_push')


@_tool('git_commit', 'Commit staged changes.', 'git', {'message': _p('Commit message')}, ['message'])
def t_git_commit(message: str):
    return _git('git_commit', message)


@_tool('git_add', 'Stage files.', 'git', {'files': _p('Paths or "." for all')})
def t_git_add(files: str = '.'):
    return _git('git_add', files or '.')


@_tool('git_branch', 'List branches.', 'git')
def t_git_branch():
    return _git('git_branch')


@_tool('git_checkout', 'Switch branch (create with create=true).', 'git',
       {'branch': _p('Branch name'), 'create': _p('Create new', 'boolean')}, ['branch'])
def t_git_checkout(branch: str, create: bool = False):
    from cora_tools.git_ops import get_git
    g = get_git()
    r = g.checkout_new(branch) if create else g.checkout(branch)
    return r if isinstance(r, dict) else _ok(str(r))


@_tool('git_log', 'Recent commits.', 'git', {'count': _p('How many', 'integer')})
def t_git_log(count: int = 10):
    return _git('git_log', int(count or 10))


@_tool('git_diff', 'Unstaged diff.', 'git')
def t_git_diff():
    r = _git('git_diff')
    if isinstance(r, dict) and isinstance(r.get('diff'), str):
        r['diff'] = r['diff'][:6000]
    return r


@_tool('github_repos', "List the user's GitHub repositories.", 'git')
def t_github_repos():
    return _git('github_repos')


@_tool('github_create_repo', 'Create a GitHub repository.', 'git',
       {'name': _p('Repo name'), 'description': _p('Description'), 'private': _p('Private', 'boolean')}, ['name'], confirm=True)
def t_github_create_repo(name: str, description: str = '', private: bool = False):
    return _git('github_create_repo', name, description or '', bool(private))


# =========================================================================== email
@_tool('send_email', 'Compose an email to a saved contact or address (opens the mail app).', 'email',
       {'to': _p('Contact name or email'), 'message': _p('Body'), 'subject': _p('Subject, optional')}, ['to', 'message'])
def t_send_email(to: str, message: str, subject: str = None):
    from cora_tools.email_tool import email_send
    return _ok(email_send(to, message, subject))


@_tool('check_email', 'Open the inbox in the mail app.', 'email')
def t_check_email():
    from cora_tools.email_tool import email_read
    return _ok(email_read())


@_tool('add_contact', 'Save an email contact.', 'email', {'name': _p('Name'), 'email': _p('Address')}, ['name', 'email'])
def t_add_contact(name: str, email: str):
    from cora_tools.email_tool import add_contact
    r = add_contact(name, email)
    return r if isinstance(r, dict) else _ok(str(r))


@_tool('list_contacts', 'List saved contacts.', 'email')
def t_list_contacts():
    from cora_tools.email_tool import list_contacts
    r = list_contacts()
    return r if isinstance(r, dict) else _ok(str(r))


# =========================================================================== self-modify
@_tool('create_script', 'Write a Python script CORA can run later (self-modification).', 'scripts',
       {'name': _p('Script name'), 'code': _p('Python source'), 'description': _p('What it does')}, ['name', 'code'])
def t_create_script(name: str, code: str, description: str = ''):
    from cora_tools.self_modify import create_script
    return create_script(name, code, description or '')


@_tool('run_script', 'Run a saved script.', 'scripts', {'name': _p('Script name')}, ['name'], confirm=True)
def t_run_script(name: str):
    from cora_tools.self_modify import run_script
    return run_script(name, confirmed=True, delete_after=False)


@_tool('list_scripts', 'List saved scripts.', 'scripts')
def t_list_scripts():
    from cora_tools.self_modify import list_scripts
    return _ok('scripts', scripts=list_scripts())


@_tool('delete_script', 'Delete a saved script.', 'scripts', {'name': _p('Script name')}, ['name'], confirm=True)
def t_delete_script(name: str):
    from cora_tools.self_modify import delete_script
    return _ok('deleted') if delete_script(name) else _err('not found')


# =========================================================================== UI / modals / voice
@_tool('view_file', 'Show a file in a viewer window.', 'ui', {'path': _p('Path')}, ['path'])
def t_view_file(path: str):
    from cora_tools.modal_tools import viewfile
    return viewfile(path)


@_tool('view_code', 'Show a code file with syntax highlighting.', 'ui', {'path': _p('Path')}, ['path'])
def t_view_code(path: str):
    from cora_tools.modal_tools import viewcode
    return viewcode(path)


@_tool('view_image', 'Show an image in a window.', 'ui', {'path': _p('Path')}, ['path'])
def t_view_image(path: str):
    from cora_tools.modal_tools import viewimage
    return viewimage(path)


@_tool('show_message', 'Show a popup message to the user.', 'ui', {'text': _p('Message')}, ['text'])
def t_show_message(text: str):
    from cora_tools.modal_tools import message
    return message(text)


@_tool('stats_window', 'Open the live system stats window.', 'ui')
def t_stats_window():
    from cora_tools.modal_tools import systemstats
    return systemstats()


@_tool('monitor_panel', 'Open the monitoring panel.', 'ui')
def t_monitor_panel():
    from ui.monitor_panel import create_monitor_panel
    create_monitor_panel()
    return _ok('monitor panel open')


@_tool('open_cli_popup', 'Open the CORA terminal popup (optionally say something in it).', 'ui', {'message': _p('Text, optional')})
def t_open_cli_popup(message: str = None):
    from services.cli_popup import open_cli_popup, cli_say
    ok = open_cli_popup()
    if ok and message:
        cli_say(message)
    return _ok('terminal open') if ok else _err('could not open terminal')


@_tool('ask_user', 'Pop up a question with answer buttons and block until the user clicks one. ONLY when a task cannot '
       'continue without their decision (which file, which option). Never for conversation, greetings or small talk.', 'ui',
       {'question': _p('Question'), 'buttons': _p('Comma-separated answers, optional')}, ['question'])
def t_ask_user(question: str, buttons: str = None):
    from ui.query_panel import quick_ask
    opts = [b.strip() for b in (buttons or '').split(',') if b.strip()] or None
    ans = quick_ask(question, opts)
    return _ok(f"user answered: {ans}", answer=ans) if ans else _err('no answer')


@_tool('open_gui_app', 'Open the full CORA GUI application window (chat/tasks/knowledge/settings).', 'ui')
def t_open_gui_app():
    launcher = PROJECT_DIR / 'src' / 'gui_launcher.py'
    flags = getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0)
    subprocess.Popen([sys.executable, str(launcher)], cwd=str(PROJECT_DIR), creationflags=flags)
    return _ok('GUI app launching')


@_tool('what_did_you_hear', 'What CORA heard in the last 30 seconds before the wake word.', 'voice')
def t_what_did_you_hear():
    from voice.stt import WakeWordDetector
    heard = WakeWordDetector.get_last_heard()
    return _ok(heard or 'nothing caught')


@_tool('set_chattiness', 'Make CORA interject more or less on her own (ambient awareness).', 'voice',
       {'level': _p('more, less or status', enum=['more', 'less', 'status'])}, ['level'])
def t_set_chattiness(level: str):
    from voice.ambient_awareness import get_ambient_awareness
    a = get_ambient_awareness()
    if level == 'more':
        a.set_friend_threshold(min(1.0, a.friend_threshold + 0.2))
    elif level == 'less':
        a.set_friend_threshold(max(0.0, a.friend_threshold - 0.3))
    return _ok(f"friend threshold {a.friend_threshold:.0%}", status=a.get_status())


@_tool('stop_speaking', 'Stop talking immediately and drop queued speech.', 'voice')
def t_stop_speaking():
    from voice.tts import stop_speaking
    stop_speaking()
    return _ok('stopped')


@_tool('speak', 'Say something out loud right now.', 'voice', {'text': _p('Text'), 'emotion': _p('Emotion label, optional')}, ['text'])
def t_speak(text: str, emotion: str = None):
    from voice.tts import queue_speak
    queue_speak(text, emotion or 'neutral')
    return _ok('speaking')


SAY_EMOTIONS = ['neutral', 'warm', 'happy', 'amused', 'excited', 'sad', 'concerned', 'frustrated', 'surprised']
SAY_ACTS = ['statement', 'yes_no_question', 'wh_question', 'exclamation', 'instruction', 'reassurance', 'aside']


@_tool('say', "[VOICE] Say a line out loud in Unity's voice (TTS). This is how the user hears you. One to three "
       "short sentences per call; several calls for a longer reply. emotion + act are how the line is delivered; "
       "[laughter] inside the text is a real laugh.", 'voice',
       {'text': _p('What to say'),
        'emotion': _p('How it is delivered', enum=SAY_EMOTIONS),
        'act': _p('What kind of line it is', enum=SAY_ACTS)},
       ['text'])
def t_say(text: str, emotion: str = 'neutral', act: str = 'statement'):
    """The brain's trained speech tool: the designators go straight to unity-voice-v2."""
    line = str(text or '').strip()
    if not line:
        return _err('nothing to say')
    from voice.tts import queue_speak
    queue_speak(line, (emotion or 'neutral').lower(), speech_act=(act or 'statement').lower())
    return _ok(f'said: {line}', emotion=emotion, act=act)


@_tool('list_capabilities', 'List everything CORA can do (tool catalog).', 'general')
def t_list_capabilities():
    return _ok(tool_catalog_text())


# Tools every turn gets regardless of wording (speech, time, the things she is asked most).
CORE_TOOLS = ['say', 'get_time', 'get_weather', 'list_tasks', 'add_task', 'complete_task', 'set_reminder',
              'list_reminders', 'remember', 'recall_memory', 'learn', 'recall_knowledge', 'look_camera',
              'take_screenshot', 'web_search', 'open_path', 'open_in_browser', 'media_play',
              'stop_speaking', 'list_capabilities', 'get_location', 'today_events', 'add_event']

_WORD = re.compile(r"[a-z0-9]+")


def select_tools(text: str, max_tools: int = 40) -> List[Tool]:
    """The tools worth showing the model for this message: the core set plus
    the best keyword matches on name/description/category. A 9B model picks
    the right tool far more reliably from ~40 schemas than from 115."""
    tools = all_tools()
    if max_tools <= 0 or len(tools) <= max_tools:
        ordered = sorted(tools, key=lambda t: (t.name != 'say', t.name))
        return ordered
    words = set(_WORD.findall((text or '').lower()))
    stems = {w[:5] for w in words if len(w) > 4}

    def score(t: Tool) -> int:
        hay = f"{t.name} {t.category} {t.description}".lower().replace('_', ' ')
        hw = set(_WORD.findall(hay))
        hit = len(words & hw) * 2 + sum(1 for st in stems if any(h.startswith(st) for h in hw))
        if t.name.replace('_', ' ') in (text or '').lower():
            hit += 5
        return hit

    core = [t for t in tools if t.name in CORE_TOOLS]
    rest = sorted((t for t in tools if t.name not in CORE_TOOLS), key=lambda t: (-score(t), t.name))
    picked = core + [t for t in rest if score(t) > 0][:max(0, max_tools - len(core))]
    picked.sort(key=lambda t: (t.name != 'say', t.name not in CORE_TOOLS, t.name))
    return picked


def execute(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Run a tool by name with keyword arguments; errors come back as data."""
    tool = get_tool(name)
    if not tool:
        return _err(f"unknown tool {name}")
    kwargs = {}
    for k, v in (arguments or {}).items():
        if k in tool.params:
            kwargs[k] = v
    missing = [r for r in tool.required if r not in kwargs or kwargs[r] in (None, '')]
    if missing:
        return _err(f"missing required argument(s): {', '.join(missing)}")
    try:
        result = tool.func(**kwargs)
        if isinstance(result, dict):
            return result
        return _ok(str(result))
    except Exception as e:
        return _err(f"{type(e).__name__}: {e}")


if __name__ == '__main__':
    print(f"{len(_REGISTRY)} tools")
    print(tool_catalog_text())
    print(json.dumps(execute('get_time', {}), indent=1))
