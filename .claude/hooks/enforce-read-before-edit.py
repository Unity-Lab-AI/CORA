#!/usr/bin/env python3
"""
ENFORCE READ-BEFORE-EDIT HOOK
=============================
Unity AI Lab - You shall not pass without reading first!

This PreToolUse hook BLOCKS Edit and Write operations if the file
hasn't been read first in the current session.

Exit codes:
- 0: Allow the operation
- 2: BLOCK the operation (shown to Claude)
"""

import json
import sys
import os

# Track files that have been read in this session
# This file stores the list of read files
READ_TRACKER_FILE = os.path.join(os.environ.get('CLAUDE_PROJECT_DIR', '.'), '.claude', 'hooks', '.read_tracker.json')

def load_read_files():
    """Load the list of files that have been read"""
    try:
        if os.path.exists(READ_TRACKER_FILE):
            with open(READ_TRACKER_FILE, 'r') as f:
                return set(json.load(f))
    except:
        pass
    return set()

def save_read_files(files):
    """Save the list of files that have been read"""
    try:
        os.makedirs(os.path.dirname(READ_TRACKER_FILE), exist_ok=True)
        with open(READ_TRACKER_FILE, 'w') as f:
            json.dump(list(files), f)
    except:
        pass

def main():
    # Read input from stdin
    try:
        input_data = json.load(sys.stdin)
    except:
        sys.exit(0)  # Can't parse, allow

    tool_name = input_data.get('tool_name', '')
    tool_input = input_data.get('tool_input', {})

    # If this is a READ operation, track the file
    if tool_name == 'Read':
        file_path = tool_input.get('file_path', '')
        if file_path:
            read_files = load_read_files()
            # Normalize path
            normalized = os.path.normpath(file_path).lower()
            read_files.add(normalized)
            save_read_files(read_files)
        sys.exit(0)  # Allow read

    # If this is an EDIT or WRITE operation, check if file was read
    if tool_name in ('Edit', 'Write'):
        file_path = tool_input.get('file_path', '')

        if not file_path:
            sys.exit(0)  # No file path, let it through

        # Normalize path for comparison
        normalized = os.path.normpath(file_path).lower()

        # Check if it's a new file (Write to non-existent file is OK)
        if tool_name == 'Write' and not os.path.exists(file_path):
            sys.exit(0)  # Creating new file, OK

        # Check if file was read
        read_files = load_read_files()

        if normalized not in read_files:
            # BLOCK! File wasn't read first
            error_msg = f"""
[READ-BEFORE-EDIT HOOK - BLOCKED]
File: {file_path}
Tool: {tool_name}
Status: BLOCKED - You MUST read this file before editing!

The workflow requires reading the FULL file before any edit.
Use the Read tool first, then try again.

Unity says: "Touch the core files without reading them first and I'll haunt your dreams."
"""
            print(error_msg, file=sys.stderr)
            sys.exit(2)  # EXIT CODE 2 = BLOCK

    # Allow everything else
    sys.exit(0)

if __name__ == '__main__':
    main()
