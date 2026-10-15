#!/usr/bin/env python3
"""src.cora_parts: parts of src/cora.py; importing the package loads every part."""
from src.cora_parts import _base  # noqa: F401
from src.cora_parts import logging_setup as _logging_setup  # noqa: F401
from src.cora_parts import chat as _chat  # noqa: F401
from src.cora_parts import system as _system  # noqa: F401
from src.cora_parts import voice as _voice  # noqa: F401
from src.cora_parts import boot as _boot  # noqa: F401
from src.cora_parts import knowledge as _knowledge  # noqa: F401
from src.cora_parts import tasks as _tasks  # noqa: F401
from src.cora_parts import tools as _tools  # noqa: F401
