#!/usr/bin/env python3
"""ui.boot_display_parts: mixins of BootDisplay (split from ui/boot_display.py on 2026-10-14)."""
from ui.boot_display_parts.window import WindowMixin  # noqa: F401
from ui.boot_display_parts.chat_input import ChatInputMixin  # noqa: F401
from ui.boot_display_parts.legacy_input import LegacyInputMixin  # noqa: F401
from ui.boot_display_parts.logging import LoggingMixin  # noqa: F401
from ui.boot_display_parts.phases import PhasesMixin  # noqa: F401
from ui.boot_display_parts.stats import StatsMixin  # noqa: F401
from ui.boot_display_parts.speech import SpeechMixin  # noqa: F401
