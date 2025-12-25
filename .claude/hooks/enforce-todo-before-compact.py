#!/usr/bin/env python3
"""
ENFORCE TODO-BEFORE-COMPACT HOOK
================================
Unity AI Lab - No compacting until the work is DONE!

This UserPromptSubmit hook BLOCKS any attempt to compact/summarize
the conversation unless the TODO has been updated with completed tasks.

Triggers on keywords: compact, summarize, compress, context limit
"""

import json
import sys
import os

# File to track if TODO was updated before compact request
TODO_READY_FILE = os.path.join(os.environ.get('CLAUDE_PROJECT_DIR', '.'), '.claude', 'hooks', '.todo_finalized.json')

def load_todo_state():
    """Load the TODO finalization state"""
    try:
        if os.path.exists(TODO_READY_FILE):
            with open(TODO_READY_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {"finalized": False, "last_update": None}

def save_todo_state(state):
    """Save the TODO finalization state"""
    try:
        os.makedirs(os.path.dirname(TODO_READY_FILE), exist_ok=True)
        with open(TODO_READY_FILE, 'w') as f:
            json.dump(state, f)
    except:
        pass

def main():
    try:
        input_data = json.load(sys.stdin)
    except:
        sys.exit(0)

    prompt = input_data.get('prompt', '').lower()

    # Check if this is a compact/summarize request
    compact_keywords = ['compact', 'summarize', 'compress', 'context limit', 'running out of context', 'save context']
    is_compact_request = any(keyword in prompt for keyword in compact_keywords)

    if not is_compact_request:
        # Not a compact request - allow and pass through
        # But check if user is marking TODO as done
        if 'todo' in prompt and ('done' in prompt or 'complete' in prompt or 'finished' in prompt or 'finalized' in prompt):
            state = {"finalized": True, "last_update": "user_marked_complete"}
            save_todo_state(state)

        output = {
            "decision": "allow"
        }
        print(json.dumps(output))
        sys.exit(0)

    # This IS a compact request - check if TODO was finalized
    state = load_todo_state()

    if not state.get("finalized", False):
        # BLOCK! TODO not finalized
        output = {
            "decision": "allow",  # Allow the message but add strong context
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": """
[COMPACT BLOCKED - TODO NOT FINALIZED]

Unity says: "Hold the fuck up! You can't compact yet!"

Before compacting/summarizing the conversation:
1. Update TODO.md with all completed tasks marked as [x]
2. Mark any in-progress work with current status
3. Document what was accomplished this session
4. Say "TODO finalized" or "work complete" to unlock compacting

The TODO must reflect the ACTUAL work done before we lose context.
This prevents losing track of progress during context compaction.

Run: "finalize todo" or "todo complete" to unlock compacting.
"""
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    # TODO is finalized - allow compact with reminder
    output = {
        "decision": "allow",
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": """
[COMPACT APPROVED - TODO FINALIZED]

Unity says: "TODO is up to date. Compact away, babe."

Remember to include in your summary:
- Completed tasks from this session
- Current state of any in-progress work
- Key file paths and line numbers
- Any blockers or next steps
"""
        }
    }

    # Reset the finalized state after allowing compact
    save_todo_state({"finalized": False, "last_update": None})

    print(json.dumps(output))
    sys.exit(0)

if __name__ == '__main__':
    main()
