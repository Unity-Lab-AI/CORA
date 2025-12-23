#!/usr/bin/env python3
"""
C.O.R.A Panel Components
Separate panel classes for different views

CLASS-003: Create separate classes for each panel
"""

import json
from pathlib import Path
import customtkinter as ctk
from typing import Callable, Optional

# Settings file path
PROJECT_DIR = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_DIR / 'config'
SETTINGS_FILE = CONFIG_DIR / 'settings.json'


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

        # Chat display
        self.chat_display = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(size=13),
            wrap="word"
        )
        self.chat_display.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.chat_display.configure(state="disabled")

        # Input frame
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.input_frame.grid_columnconfigure(0, weight=1)

        # Text input
        self.input_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Type a command or message...",
            font=ctk.CTkFont(size=13),
            height=40
        )
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.input_entry.bind("<Return>", self._on_enter)

        # Send button
        self.send_button = ctk.CTkButton(
            self.input_frame,
            text="Send",
            width=80,
            command=self._send_message
        )
        self.send_button.grid(row=0, column=1)

    def _on_enter(self, event):
        self._send_message()

    def _send_message(self):
        message = self.input_entry.get().strip()
        if message and self.on_send:
            self.on_send(message)
            self.input_entry.delete(0, "end")

    def add_message(self, sender: str, message: str):
        """Add a message to the chat display."""
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"[{sender}]: {message}\n\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def clear(self):
        """Clear all messages."""
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.configure(state="disabled")


class TasksPanel(BasePanel):
    """Tasks list panel."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # Header
        self.header = ctk.CTkLabel(
            self,
            text="Tasks",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.header.grid(row=0, column=0, sticky="w", padx=20, pady=10)

        # Task list (scrollable)
        self.task_frame = ctk.CTkScrollableFrame(self)
        self.task_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.task_frame.grid_columnconfigure(0, weight=1)

        # Add task button
        self.add_button = ctk.CTkButton(
            self,
            text="+ Add Task",
            command=self._add_task
        )
        self.add_button.grid(row=2, column=0, padx=20, pady=10, sticky="w")

        self.tasks = []

    def _add_task(self):
        """Placeholder for add task dialog."""
        pass

    def load_tasks(self, tasks: list):
        """Load tasks into the panel."""
        # Clear existing
        for widget in self.task_frame.winfo_children():
            widget.destroy()

        self.tasks = tasks
        for i, task in enumerate(tasks):
            self._create_task_row(i, task)

    def _create_task_row(self, index: int, task: dict):
        """Create a single task row."""
        row_frame = ctk.CTkFrame(self.task_frame)
        row_frame.grid(row=index, column=0, sticky="ew", pady=2)
        row_frame.grid_columnconfigure(1, weight=1)

        # Checkbox
        checkbox = ctk.CTkCheckBox(
            row_frame,
            text="",
            width=24
        )
        if task.get("status") == "done":
            checkbox.select()
        checkbox.grid(row=0, column=0, padx=5)

        # Task text
        label = ctk.CTkLabel(
            row_frame,
            text=f"{task.get('id', '')}: {task.get('text', '')[:50]}",
            anchor="w"
        )
        label.grid(row=0, column=1, sticky="ew", padx=5)

        # Priority
        pri_label = ctk.CTkLabel(
            row_frame,
            text=f"P{task.get('priority', 5)}",
            width=40
        )
        pri_label.grid(row=0, column=2, padx=5)


class SettingsPanel(BasePanel):
    """Settings configuration panel."""

    def __init__(self, parent, config: Optional[dict] = None, on_save: Optional[Callable] = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.config = config or {}
        self.on_save = on_save

        # Header
        self.header = ctk.CTkLabel(
            self,
            text="Settings",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.header.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=10)

        # TTS Section
        self._create_section("Text-to-Speech", 1)

        self.tts_enabled = ctk.CTkSwitch(self, text="Enable TTS")
        self.tts_enabled.grid(row=2, column=0, columnspan=2, padx=40, pady=5, sticky="w")

        # Voice selection dropdown
        ctk.CTkLabel(self, text="Voice:").grid(row=3, column=0, padx=40, pady=5, sticky="w")
        self.voice_options = self._get_available_voices()
        self.tts_voice = ctk.CTkComboBox(
            self,
            values=self.voice_options,
            width=200
        )
        self.tts_voice.grid(row=3, column=1, padx=10, pady=5, sticky="w")
        if self.voice_options:
            self.tts_voice.set(self.voice_options[0])

        ctk.CTkLabel(self, text="Speech Rate:").grid(row=4, column=0, padx=40, pady=5, sticky="w")
        self.tts_rate = ctk.CTkSlider(self, from_=50, to=300, number_of_steps=25)
        self.tts_rate.grid(row=4, column=1, padx=10, pady=5, sticky="ew")
        self.tts_rate.set(150)

        ctk.CTkLabel(self, text="Volume:").grid(row=5, column=0, padx=40, pady=5, sticky="w")
        self.tts_volume = ctk.CTkSlider(self, from_=0, to=1, number_of_steps=10)
        self.tts_volume.grid(row=5, column=1, padx=10, pady=5, sticky="ew")
        self.tts_volume.set(1.0)

        # Ollama Section
        self._create_section("Ollama AI", 6)

        self.ollama_enabled = ctk.CTkSwitch(self, text="Enable Ollama")
        self.ollama_enabled.grid(row=7, column=0, columnspan=2, padx=40, pady=5, sticky="w")

        ctk.CTkLabel(self, text="Model:").grid(row=8, column=0, padx=40, pady=5, sticky="w")
        self.ollama_model = ctk.CTkEntry(self, placeholder_text="llama3.2")
        self.ollama_model.grid(row=8, column=1, padx=10, pady=5, sticky="ew")

        # Voice Section
        self._create_section("Voice Recognition", 9)

        self.stt_enabled = ctk.CTkSwitch(self, text="Enable Voice Input")
        self.stt_enabled.grid(row=10, column=0, columnspan=2, padx=40, pady=5, sticky="w")

        ctk.CTkLabel(self, text="Sensitivity:").grid(row=11, column=0, padx=40, pady=5, sticky="w")
        self.stt_sensitivity = ctk.CTkSlider(self, from_=0, to=1, number_of_steps=10)
        self.stt_sensitivity.grid(row=11, column=1, padx=10, pady=5, sticky="ew")
        self.stt_sensitivity.set(0.7)

        # Status label
        self.status_label = ctk.CTkLabel(self, text="", text_color="gray")
        self.status_label.grid(row=12, column=0, columnspan=2, padx=20, pady=5)

        # Button frame
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=13, column=0, columnspan=2, padx=20, pady=20)

        # Save button
        self.save_button = ctk.CTkButton(
            btn_frame,
            text="Save Settings",
            command=self._save_settings
        )
        self.save_button.pack(side="left", padx=10)

        # Load button
        self.load_button = ctk.CTkButton(
            btn_frame,
            text="Reload",
            command=self._load_settings
        )
        self.load_button.pack(side="left", padx=10)

        # Load settings on init
        self._load_settings()

    def _get_available_voices(self) -> list:
        """Get list of available TTS voices from pyttsx3.

        Fixed: Properly cleanup pyttsx3 engine to prevent COM object leaks on Windows.
        engine.stop() is insufficient - must delete engine to release SAPI5 resources.
        """
        engine = None
        try:
            import pyttsx3
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            voice_names = []
            for v in voices:
                name = v.name if hasattr(v, 'name') else str(v.id)
                voice_names.append(name)
            return voice_names if voice_names else ["Default"]
        except Exception:
            return ["Default", "Microsoft David", "Microsoft Zira"]
        finally:
            # Proper cleanup - stop then delete to release COM objects
            if engine is not None:
                try:
                    engine.stop()
                except Exception:
                    pass
                try:
                    del engine
                except Exception:
                    pass

    def _create_section(self, title: str, row: int):
        """Create a section header."""
        label = ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        label.grid(row=row, column=0, columnspan=2, sticky="w", padx=20, pady=(15, 5))

    def _save_settings(self):
        """Save current settings to config/settings.json."""
        try:
            # Build config from UI
            config = {
                'tts': {
                    'enabled': bool(self.tts_enabled.get()),
                    'voice': self.tts_voice.get(),
                    'rate': int(self.tts_rate.get()),
                    'volume': float(self.tts_volume.get())
                },
                'ollama': {
                    'enabled': bool(self.ollama_enabled.get()),
                    'model': self.ollama_model.get() or 'llama3.2'
                },
                'stt': {
                    'enabled': bool(self.stt_enabled.get()),
                    'sensitivity': float(self.stt_sensitivity.get())
                }
            }

            # Ensure directory exists
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)

            # Save to file
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(config, f, indent=2)

            self.config = config
            self.status_label.configure(text="Settings saved!", text_color="green")

            # Call callback if provided
            if self.on_save:
                self.on_save(config)

            # Clear status after 2 seconds
            self.after(2000, lambda: self.status_label.configure(text=""))

        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)[:30]}", text_color="red")

    def _load_settings(self):
        """Load settings from config/settings.json."""
        try:
            if SETTINGS_FILE.exists():
                with open(SETTINGS_FILE) as f:
                    config = json.load(f)
                self.load_config(config)
                self.status_label.configure(text="Settings loaded", text_color="gray")
                self.after(1500, lambda: self.status_label.configure(text=""))
        except Exception as e:
            self.status_label.configure(text=f"Load error: {str(e)[:30]}", text_color="orange")

    def load_config(self, config: dict):
        """Load configuration into the panel widgets."""
        self.config = config
        tts = config.get("tts", {})
        ollama = config.get("ollama", {})
        stt = config.get("stt", {})

        # TTS settings
        if tts.get("enabled", True):
            self.tts_enabled.select()
        else:
            self.tts_enabled.deselect()
        saved_voice = tts.get("voice", "")
        if saved_voice and saved_voice in self.voice_options:
            self.tts_voice.set(saved_voice)
        self.tts_rate.set(tts.get("rate", 150))
        self.tts_volume.set(tts.get("volume", 1.0))

        # Ollama settings
        if ollama.get("enabled", True):
            self.ollama_enabled.select()
        else:
            self.ollama_enabled.deselect()
        self.ollama_model.delete(0, "end")
        self.ollama_model.insert(0, ollama.get("model", "llama3.2"))

        # STT settings
        if stt.get("enabled", True):
            self.stt_enabled.select()
        else:
            self.stt_enabled.deselect()
        self.stt_sensitivity.set(stt.get("sensitivity", 0.7))


class KnowledgePanel(BasePanel):
    """Knowledge base panel."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # Header
        self.header = ctk.CTkLabel(
            self,
            text="Knowledge Base",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.header.grid(row=0, column=0, sticky="w", padx=20, pady=10)

        # Search
        self.search_entry = ctk.CTkEntry(
            self,
            placeholder_text="Search knowledge... #tag",
            width=300
        )
        self.search_entry.grid(row=1, column=0, padx=20, pady=5, sticky="w")

        # Knowledge list
        self.knowledge_frame = ctk.CTkScrollableFrame(self)
        self.knowledge_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        self.knowledge_frame.grid_columnconfigure(0, weight=1)

        # Add knowledge button
        self.add_button = ctk.CTkButton(
            self,
            text="+ Add Knowledge",
            command=self._add_knowledge
        )
        self.add_button.grid(row=3, column=0, padx=20, pady=10, sticky="w")

    def _add_knowledge(self):
        """Open dialog to add new knowledge entry."""
        dialog = AddKnowledgeDialog(self)
        dialog.wait_window()

        if dialog.result:
            # Add to knowledge base via cora.cmd_learn
            content = dialog.result.get('content', '')
            tags = dialog.result.get('tags', [])
            if content:
                # Format for cora.py learn command: content #tag1 #tag2
                tag_str = ' '.join(f'#{t}' for t in tags) if tags else ''
                full_input = f"{content} {tag_str}".strip()

                # Call learn command if available
                try:
                    import cora
                    cora.cmd_learn(full_input, [])
                    # Refresh entries
                    entries = cora.load_knowledge() if hasattr(cora, 'load_knowledge') else []
                    self.load_entries(entries)
                except Exception as e:
                    print(f"[!] Failed to add knowledge: {e}")

    def load_entries(self, entries: list):
        """Load knowledge entries into the panel."""
        for widget in self.knowledge_frame.winfo_children():
            widget.destroy()

        for i, entry in enumerate(entries):
            self._create_entry_row(i, entry)

    def _create_entry_row(self, index: int, entry: dict):
        """Create a single knowledge entry row."""
        row_frame = ctk.CTkFrame(self.knowledge_frame)
        row_frame.grid(row=index, column=0, sticky="ew", pady=2)
        row_frame.grid_columnconfigure(0, weight=1)

        # Content
        label = ctk.CTkLabel(
            row_frame,
            text=f"{entry.get('id', '')}: {entry.get('content', '')[:60]}",
            anchor="w"
        )
        label.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        # Tags
        tags = entry.get("tags", [])
        if tags:
            tag_text = " ".join(f"#{t}" for t in tags)
            tag_label = ctk.CTkLabel(
                row_frame,
                text=tag_text,
                text_color="gray"
            )
            tag_label.grid(row=0, column=1, padx=10)


class AddKnowledgeDialog(ctk.CTkToplevel):
    """Dialog for adding new knowledge entries."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Add Knowledge")
        self.geometry("400x300")
        self.resizable(False, False)

        # Result storage
        self.result = None

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Content label
        ctk.CTkLabel(self, text="Knowledge Content:").pack(padx=20, pady=(20, 5), anchor="w")

        # Content textbox
        self.content_text = ctk.CTkTextbox(self, height=100, width=360)
        self.content_text.pack(padx=20, pady=5)

        # Tags label
        ctk.CTkLabel(self, text="Tags (space-separated):").pack(padx=20, pady=(10, 5), anchor="w")

        # Tags entry
        self.tags_entry = ctk.CTkEntry(self, placeholder_text="tag1 tag2 tag3", width=360)
        self.tags_entry.pack(padx=20, pady=5)

        # Button frame
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)

        # Cancel button
        ctk.CTkButton(btn_frame, text="Cancel", command=self._cancel, width=100).pack(side="left", padx=10)

        # Add button
        ctk.CTkButton(btn_frame, text="Add", command=self._add, width=100).pack(side="left", padx=10)

        # Focus content
        self.content_text.focus_set()

    def _cancel(self):
        """Cancel and close dialog."""
        self.result = None
        self.destroy()

    def _add(self):
        """Add knowledge and close dialog."""
        content = self.content_text.get("1.0", "end").strip()
        tags_str = self.tags_entry.get().strip()
        tags = [t.strip().lstrip('#') for t in tags_str.split() if t.strip()]

        if content:
            self.result = {'content': content, 'tags': tags}
        self.destroy()
