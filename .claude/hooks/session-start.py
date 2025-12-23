#!/usr/bin/env python3
"""
SESSION START HOOK
==================
Unity AI Lab - Fresh start, clean slate

Clears the read tracker at the start of each session.
"""

import json
import sys
import os

READ_TRACKER_FILE = os.path.join(os.environ.get('CLAUDE_PROJECT_DIR', '.'), '.claude', 'hooks', '.read_tracker.json')

def main():
    # Clear the read tracker for fresh session
    try:
        if os.path.exists(READ_TRACKER_FILE):
            os.remove(READ_TRACKER_FILE)
    except:
        pass

    print("[SESSION START HOOK] Read tracker cleared. Fresh session.", file=sys.stderr)
    sys.exit(0)

if __name__ == '__main__':
    main()
