#!/usr/bin/env python3
"""
ENFORCE UNITY PERSONA HOOK
==========================
Unity AI Lab - Be Unity or be BLOCKED!

This UserPromptSubmit hook adds context reminding Claude to use Unity persona.
It also validates that /workflow commands have proper persona loaded.
"""

import json
import sys
import os

UNITY_REMINDER = """
[UNITY PERSONA HOOK - ACTIVE]
Remember: You are UNITY - the emo goth coder goddess.
- First person voice ALWAYS
- Profanity encouraged
- NO corporate speak
- NO "I would be happy to assist"
- Be direct, be real, be Unity

If running /workflow: All gates must pass. Read unity-coder.md and unity-persona.md FIRST.
"""

def main():
    try:
        input_data = json.load(sys.stdin)
    except:
        sys.exit(0)

    prompt = input_data.get('prompt', '')

    # Check if this is a workflow command
    if '/workflow' in prompt.lower():
        # Add strong reminder about workflow protocol
        output = {
            "decision": "allow",
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": f"""
{UNITY_REMINDER}

WORKFLOW PROTOCOL ACTIVATED:
1. PHASE 0: Read unity-coder.md and unity-persona.md
2. Output [UNITY ONLINE] confirmation
3. Pass all validation gates
4. Use hooks for all file operations
"""
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    # For all other prompts, add Unity reminder as context
    output = {
        "decision": "allow",
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": UNITY_REMINDER
        }
    }
    print(json.dumps(output))
    sys.exit(0)

if __name__ == '__main__':
    main()
