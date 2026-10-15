#!/usr/bin/env python3
"""
C.O.R.A Panel Components
Separate panel classes for the GUI app views (chat, tasks, settings, knowledge).

All panels work on the SAME data as the rest of CORA:
  - tasks     -> cora_tools.tasks (data/tasks.json)
  - knowledge -> data/knowledge.json (same store the `learn` tool uses)
  - settings  -> config/config.json (the one config everything reads)
"""

import json
import os
from pathlib import Path
import customtkinter as ctk
from typing import Callable, Optional

PROJECT_DIR = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_DIR / 'config'
CONFIG_FILE = CONFIG_DIR / 'config.json'
KNOWLEDGE_FILE = PROJECT_DIR / 'data' / 'knowledge.json'


def _load_config() -> dict:
    try:
        from ai import config as _config
        return json.loads(json.dumps(_config.load(force=True)))   # an editable copy
    except Exception:
        return {}


def _save_config(cfg: dict):
    from ai import config as _config
    _config.save(cfg)      # atomic, cache + ai.settings refreshed


class BasePanel(ctk.CTkFrame):
    """Base class for all panels."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)


class ChatPanel(BasePanel):
    """Chat interface panel."""

    def __init__(self, parent, on_send: Optional[Callable] = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_send = on_send

        self.chat_display = ctk.CTkTextbox(self, font=ctk.CTkFont(size=13), wrap="word")
        self.chat_display.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.chat_display.configure(state="disabled")

        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.input_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Type a command or message...",
                                        font=ctk.CTkFont(size=13), height=40)
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.input_entry.bind("<Return>", self._on_enter)

        self.send_button = ctk.CTkButton(self.input_frame, text="Send", width=80, command=self._send_message)
        self.send_button.grid(row=0, column=1)

    def _on_enter(self, event):
        self._send_message()

    def _send_message(self):
        message = self.input_entry.get().strip()
        if message and self.on_send:
            self.on_send(message)
            self.input_entry.delete(0, "end")

    def add_message(self, sender: str, message: str):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"[{sender}]: {message}\n\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def clear(self):
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.configure(state="disabled")


class TasksPanel(BasePanel):
    """Tasks list panel backed by cora_tools.tasks."""

    def __init__(self, parent, on_change: Optional[Callable] = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_change = on_change
        self.grid_rowconfigure(1, weight=1)

        self.header = ctk.CTkLabel(self, text="Tasks", font=ctk.CTkFont(size=20, weight="bold"))
        self.header.grid(row=0, column=0, sticky="w", padx=20, pady=10)

        self.task_frame = ctk.CTkScrollableFrame(self)
        self.task_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.task_frame.grid_columnconfigure(0, weight=1)

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        bar.grid_columnconfigure(0, weight=1)
        self.new_entry = ctk.CTkEntry(bar, placeholder_text="New task... (optional: !1 for priority 1, @2026-10-20 for due)")
        self.new_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.new_entry.bind("<Return>", lambda e: self._add_task())
        self.add_button = ctk.CTkButton(bar, text="+ Add Task", command=self._add_task, width=110)
        self.add_button.grid(row=0, column=1)
        self.filter_var = ctk.StringVar(value="pending")
        self.filter_menu = ctk.CTkOptionMenu(bar, values=["pending", "all", "done", "overdue"],
                                             variable=self.filter_var, command=lambda _v: self.refresh(), width=110)
        self.filter_menu.grid(row=0, column=2, padx=(10, 0))

        self.tasks = []

    def _manager(self):
        from cora_tools.tasks import get_manager
        tm = get_manager()
        tm.load()
        return tm

    def _add_task(self):
        """Create a task from the entry: text, optional !priority and @due tokens."""
        raw = self.new_entry.get().strip()
        if not raw:
            return
        import re
        priority = None
        due = None
        m = re.search(r'!(\d{1,2})\b', raw)
        if m:
            priority = int(m.group(1))
            raw = raw.replace(m.group(0), '').strip()
        m = re.search(r'@(\S+)', raw)
        if m:
            due = m.group(1)
            raw = raw.replace(m.group(0), '').strip()
        try:
            from ai.tools_registry import execute
            r = execute('add_task', {'text': raw, 'priority': priority, 'due': due})
            if not r.get('ok'):
                print(f"[GUI] add task: {r}")
        except Exception as e:
            print(f"[GUI] add task failed: {e}")
        self.new_entry.delete(0, "end")
        self.refresh()

    def refresh(self):
        try:
            tm = self._manager()
            items = tm.list_tasks(self.filter_var.get())
            self.load_tasks([{"id": t.get("id"), "text": t.get("text", ""), "priority": t.get("priority", 5),
                              "status": t.get("status", "pending"), "due": t.get("due")} for t in items])
        except Exception as e:
            print(f"[GUI] tasks refresh: {e}")
        if self.on_change:
            try:
                self.on_change()
            except Exception:
                pass

    def load_tasks(self, tasks: list):
        for widget in self.task_frame.winfo_children():
            widget.destroy()
        self.tasks = tasks
        for i, task in enumerate(tasks):
            self._create_task_row(i, task)

    def _toggle(self, task_id: str, var):
        try:
            tm = self._manager()
            if var.get():
                tm.complete_task(task_id)
            else:
                tm.update_task(task_id, status='pending')
        except Exception as e:
            print(f"[GUI] toggle task: {e}")
        self.refresh()

    def _delete(self, task_id: str):
        try:
            from tkinter import messagebox
            if not messagebox.askyesno("Delete task", f"Delete {task_id}?", parent=self):
                return
            self._manager().delete_task(task_id)
        except Exception as e:
            print(f"[GUI] delete task: {e}")
        self.refresh()

    def _create_task_row(self, index: int, task: dict):
        row_frame = ctk.CTkFrame(self.task_frame)
        row_frame.grid(row=index, column=0, sticky="ew", pady=2)
        row_frame.grid_columnconfigure(1, weight=1)

        var = ctk.BooleanVar(value=task.get("status") == "done")
        checkbox = ctk.CTkCheckBox(row_frame, text="", width=24, variable=var,
                                   command=lambda tid=task.get('id'), v=var: self._toggle(tid, v))
        checkbox.grid(row=0, column=0, padx=5)

        due = f"  (due {task['due']})" if task.get('due') else ''
        label = ctk.CTkLabel(row_frame, text=f"{task.get('id', '')}: {task.get('text', '')[:60]}{due}", anchor="w")
        label.grid(row=0, column=1, sticky="ew", padx=5)

        pri_label = ctk.CTkLabel(row_frame, text=f"P{task.get('priority', 5)}", width=40)
        pri_label.grid(row=0, column=2, padx=5)

        del_btn = ctk.CTkButton(row_frame, text="x", width=28, fg_color="#552222", hover_color="#883333",
                                command=lambda tid=task.get('id'): self._delete(tid))
        del_btn.grid(row=0, column=3, padx=5)


class SettingsPanel(BasePanel):
    """Settings panel editing config/config.json (the single config)."""

    def __init__(self, parent, config: Optional[dict] = None, on_save: Optional[Callable] = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.config = config or {}
        self.on_save = on_save

        self.header = ctk.CTkLabel(self, text="Settings", font=ctk.CTkFont(size=20, weight="bold"))
        self.header.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=10)

        # Voice
        self._create_section("Voice (unity-voice-v2)", 1)
        self.tts_enabled = ctk.CTkSwitch(self, text="Enable voice")
        self.tts_enabled.grid(row=2, column=0, columnspan=2, padx=40, pady=5, sticky="w")
        ctk.CTkLabel(self, text="Voice:").grid(row=3, column=0, padx=40, pady=5, sticky="w")
        self.voice_label = ctk.CTkLabel(self, text="Unity voice v2 (A2 low warm alto) - her own trained voice")
        self.voice_label.grid(row=3, column=1, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(self, text="Volume:").grid(row=4, column=0, padx=40, pady=5, sticky="w")
        self.tts_volume = ctk.CTkSlider(self, from_=0, to=1, number_of_steps=20)
        self.tts_volume.grid(row=4, column=1, padx=10, pady=5, sticky="ew")
        self.tts_volume.set(1.0)
        ctk.CTkLabel(self, text="Emotion intensity:").grid(row=5, column=0, padx=40, pady=5, sticky="w")
        self.tts_intensity = ctk.CTkSlider(self, from_=0, to=1, number_of_steps=20)
        self.tts_intensity.grid(row=5, column=1, padx=10, pady=5, sticky="ew")
        self.tts_intensity.set(0.5)
        self.presence_gate = ctk.CTkSwitch(self, text="Only speak when someone is at the desk (webcam)")
        self.presence_gate.grid(row=6, column=0, columnspan=2, padx=40, pady=5, sticky="w")

        # AI
        self._create_section("AI (Ollama)", 7)
        self.ollama_enabled = ctk.CTkSwitch(self, text="Enable AI")
        self.ollama_enabled.grid(row=8, column=0, columnspan=2, padx=40, pady=5, sticky="w")
        ctk.CTkLabel(self, text="Chat model:").grid(row=9, column=0, padx=40, pady=5, sticky="w")
        self.ollama_model = ctk.CTkComboBox(self, values=self._installed_models(), width=320)
        self.ollama_model.grid(row=9, column=1, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(self, text="Vision model:").grid(row=10, column=0, padx=40, pady=5, sticky="w")
        self.vision_model = ctk.CTkComboBox(self, values=self._installed_models(), width=320)
        self.vision_model.grid(row=10, column=1, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(self, text="Context (tokens):").grid(row=11, column=0, padx=40, pady=5, sticky="w")
        self.num_ctx = ctk.CTkOptionMenu(self, values=["8192", "16384", "32768"], width=120)
        self.num_ctx.grid(row=11, column=1, padx=10, pady=5, sticky="w")

        # Voice recognition
        self._create_section("Voice Recognition", 12)
        self.stt_enabled = ctk.CTkSwitch(self, text="Enable wake word / voice input")
        self.stt_enabled.grid(row=13, column=0, columnspan=2, padx=40, pady=5, sticky="w")
        ctk.CTkLabel(self, text="Sensitivity:").grid(row=14, column=0, padx=40, pady=5, sticky="w")
        self.stt_sensitivity = ctk.CTkSlider(self, from_=0, to=1, number_of_steps=10)
        self.stt_sensitivity.grid(row=14, column=1, padx=10, pady=5, sticky="ew")
        self.stt_sensitivity.set(0.5)
        ctk.CTkLabel(self, text="Whisper model:").grid(row=15, column=0, padx=40, pady=5, sticky="w")
        self.whisper_model = ctk.CTkOptionMenu(self, values=["tiny.en", "base.en", "small.en", "medium.en"], width=140)
        self.whisper_model.grid(row=15, column=1, padx=10, pady=5, sticky="w")

        # Boot
        self._create_section("Boot", 16)
        self.demo_phases = ctk.CTkSwitch(self, text="Run demo phases at boot (YouTube, GitHub import, image gen...)")
        self.demo_phases.grid(row=17, column=0, columnspan=2, padx=40, pady=5, sticky="w")

        self.status_label = ctk.CTkLabel(self, text="", text_color="gray")
        self.status_label.grid(row=18, column=0, columnspan=2, padx=20, pady=5)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=19, column=0, columnspan=2, padx=20, pady=20)
        self.save_button = ctk.CTkButton(btn_frame, text="Save Settings", command=self._save_settings)
        self.save_button.pack(side="left", padx=10)
        self.load_button = ctk.CTkButton(btn_frame, text="Reload", command=self._load_settings)
        self.load_button.pack(side="left", padx=10)

        self._load_settings()

    def _installed_models(self) -> list:
        try:
            from ai.ollama import list_models
            names = [m['name'] for m in list_models()]
            return names or ["(ollama offline)"]
        except Exception:
            return ["(ollama offline)"]

    def _create_section(self, title: str, row: int):
        label = ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=14, weight="bold"))
        label.grid(row=row, column=0, columnspan=2, sticky="w", padx=20, pady=(15, 5))

    def _save_settings(self):
        try:
            cfg = _load_config()
            tts = cfg.setdefault('tts', {})
            tts['enabled'] = bool(self.tts_enabled.get())
            tts['volume'] = round(float(self.tts_volume.get()), 2)
            tts['presence_gate'] = bool(self.presence_gate.get())
            tts.setdefault('unity_voice', {})['default_intensity'] = round(float(self.tts_intensity.get()), 2)
            cfg.setdefault('emotion', {})['intensity'] = round(float(self.tts_intensity.get()) * 2, 2)
            ol = cfg.setdefault('ollama', {})
            ol['enabled'] = bool(self.ollama_enabled.get())
            chat_model = self.ollama_model.get().strip()
            if chat_model and not chat_model.startswith('('):
                ol['model'] = chat_model
                cfg.setdefault('models', {})['primary'] = chat_model
            vision = self.vision_model.get().strip()
            if vision and not vision.startswith('('):
                cfg.setdefault('models', {})['vision'] = vision
            ol['num_ctx'] = int(self.num_ctx.get())
            stt = cfg.setdefault('stt', {})
            stt['enabled'] = bool(self.stt_enabled.get())
            stt['sensitivity'] = round(float(self.stt_sensitivity.get()), 2)
            stt['whisper_model'] = self.whisper_model.get()
            cfg.setdefault('boot', {})['demo_phases'] = bool(self.demo_phases.get())
            _save_config(cfg)
            try:
                from ai import settings as _s
                _s.reload()
            except Exception:
                pass
            self.config = cfg
            self.status_label.configure(text="Settings saved to config/config.json", text_color="green")
            if self.on_save:
                self.on_save(cfg)
            self.after(2500, lambda: self.status_label.configure(text=""))
        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)[:40]}", text_color="red")

    def _load_settings(self):
        try:
            self.load_config(_load_config())
            self.status_label.configure(text="Settings loaded", text_color="gray")
            self.after(1500, lambda: self.status_label.configure(text=""))
        except Exception as e:
            self.status_label.configure(text=f"Load error: {str(e)[:30]}", text_color="orange")

    def load_config(self, config: dict):
        self.config = config
        tts = config.get("tts", {}) or {}
        ol = config.get("ollama", {}) or {}
        models = config.get("models", {}) or {}
        stt = config.get("stt", {}) or {}
        boot = config.get("boot", {}) or {}

        (self.tts_enabled.select if tts.get("enabled", True) else self.tts_enabled.deselect)()
        self.tts_volume.set(float(tts.get("volume", 1.0)))
        self.tts_intensity.set(float((tts.get('unity_voice') or {}).get('default_intensity', 0.5)))
        (self.presence_gate.select if tts.get("presence_gate", False) else self.presence_gate.deselect)()

        (self.ollama_enabled.select if ol.get("enabled", True) else self.ollama_enabled.deselect)()
        self.ollama_model.set(models.get("primary") or ol.get("model", ""))
        self.vision_model.set(models.get("vision", ""))
        self.num_ctx.set(str(ol.get("num_ctx", 16384)))

        (self.stt_enabled.select if stt.get("enabled", True) else self.stt_enabled.deselect)()
        self.stt_sensitivity.set(float(stt.get("sensitivity", 0.5)))
        self.whisper_model.set(stt.get("whisper_model", "base.en"))
        (self.demo_phases.select if boot.get("demo_phases", False) else self.demo_phases.deselect)()


class KnowledgePanel(BasePanel):
    """Knowledge base panel (data/knowledge.json, shared with the `learn` tool)."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.grid_rowconfigure(2, weight=1)

        self.header = ctk.CTkLabel(self, text="Knowledge Base", font=ctk.CTkFont(size=20, weight="bold"))
        self.header.grid(row=0, column=0, sticky="w", padx=20, pady=10)

        self.search_entry = ctk.CTkEntry(self, placeholder_text="Search knowledge... (#tag to filter)", width=300)
        self.search_entry.grid(row=1, column=0, padx=20, pady=5, sticky="w")
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh())

        self.knowledge_frame = ctk.CTkScrollableFrame(self)
        self.knowledge_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        self.knowledge_frame.grid_columnconfigure(0, weight=1)

        self.add_button = ctk.CTkButton(self, text="+ Add Knowledge", command=self._add_knowledge)
        self.add_button.grid(row=3, column=0, padx=20, pady=10, sticky="w")
        self.refresh()

    def _entries(self) -> list:
        try:
            with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f).get('entries', [])
        except Exception:
            return []

    def refresh(self):
        q = self.search_entry.get().strip().lower()
        entries = self._entries()
        if q.startswith('#'):
            tag = q[1:]
            entries = [e for e in entries if tag in [t.lower() for t in e.get('tags', [])]]
        elif q:
            entries = [e for e in entries if all(w in e.get('content', '').lower() for w in q.split())]
        self.load_entries(entries[-100:])

    def _add_knowledge(self):
        dialog = AddKnowledgeDialog(self)
        dialog.wait_window()
        if dialog.result and dialog.result.get('content'):
            try:
                from ai.tools_registry import execute
                execute('learn', {'text': dialog.result['content'], 'tags': ','.join(dialog.result.get('tags', []))})
            except Exception as e:
                print(f"[!] Failed to add knowledge: {e}")
            self.refresh()

    def _delete(self, entry_id: str):
        try:
            from tkinter import messagebox
            if not messagebox.askyesno("Forget", f"Forget {entry_id}?", parent=self):
                return
            from ai.tools_registry import execute
            execute('forget_knowledge', {'entry_id': entry_id})
        except Exception as e:
            print(f"[!] forget failed: {e}")
        self.refresh()

    def load_entries(self, entries: list):
        for widget in self.knowledge_frame.winfo_children():
            widget.destroy()
        for i, entry in enumerate(entries):
            self._create_entry_row(i, entry)

    def _create_entry_row(self, index: int, entry: dict):
        row_frame = ctk.CTkFrame(self.knowledge_frame)
        row_frame.grid(row=index, column=0, sticky="ew", pady=2)
        row_frame.grid_columnconfigure(0, weight=1)
        label = ctk.CTkLabel(row_frame, text=f"{entry.get('id', '')}: {entry.get('content', '')[:90]}", anchor="w")
        label.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        tags = entry.get("tags", [])
        if tags:
            ctk.CTkLabel(row_frame, text=" ".join(f"#{t}" for t in tags), text_color="gray").grid(row=0, column=1, padx=10)
        ctk.CTkButton(row_frame, text="x", width=28, fg_color="#552222", hover_color="#883333",
                      command=lambda eid=entry.get('id'): self._delete(eid)).grid(row=0, column=2, padx=5)


class AddKnowledgeDialog(ctk.CTkToplevel):
    """Dialog for adding new knowledge entries."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Add Knowledge")
        self.geometry("400x300")
        self.resizable(False, False)
        self.result = None
        self.transient(parent)
        self.grab_set()

        ctk.CTkLabel(self, text="Knowledge Content:").pack(padx=20, pady=(20, 5), anchor="w")
        self.content_text = ctk.CTkTextbox(self, height=100, width=360)
        self.content_text.pack(padx=20, pady=5)
        ctk.CTkLabel(self, text="Tags (space-separated):").pack(padx=20, pady=(10, 5), anchor="w")
        self.tags_entry = ctk.CTkEntry(self, placeholder_text="tag1 tag2 tag3", width=360)
        self.tags_entry.pack(padx=20, pady=5)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)
        ctk.CTkButton(btn_frame, text="Cancel", command=self._cancel, width=100).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Add", command=self._add, width=100).pack(side="left", padx=10)
        self.content_text.focus_set()

    def _cancel(self):
        self.result = None
        self.destroy()

    def _add(self):
        content = self.content_text.get("1.0", "end").strip()
        tags = [t.strip().lstrip('#') for t in self.tags_entry.get().strip().split() if t.strip()]
        if content:
            self.result = {'content': content, 'tags': tags}
        self.destroy()
