#!/usr/bin/env python3
"""src.cora_parts: tools (split from src/cora.py on 2026-10-14)."""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import shutil
import subprocess
import threading
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from src.cora_parts import _base  # noqa: F401
from src.cora_parts._base import DATA_DIR, datetime, json, speak  # noqa: F401




def cmd_create_tool(args, tasks):
    from src.cora_parts.chat import respond
    """Create a new runtime tool. Usage: create_tool <name> <description>

    Creates a temporary script in tools/temp_scripts/ for runtime tool creation.
    Per ARCHITECTURE.md P4-SELF: Self-modification capabilities.
    """
    if len(args) < 2:
        respond('error', {'message': "Usage: create_tool <name> <description>"})
        print("Example: create_tool greet 'Say hello to user'")
        return tasks

    tool_name = args[0].lower().replace(' ', '_')
    description = ' '.join(args[1:])

    try:
        # Ensure temp_scripts directory exists
        temp_scripts_dir = DATA_DIR / 'tools' / 'temp_scripts'
        temp_scripts_dir.mkdir(parents=True, exist_ok=True)

        # Track tools in a registry file
        registry_file = temp_scripts_dir / 'tool_registry.json'
        if registry_file.exists():
            with open(registry_file) as f:
                registry = json.load(f)
        else:
            registry = {'tools': []}

        # Check if tool already exists
        existing = [t for t in registry.get('tools', []) if t.get('name') == tool_name]
        if existing:
            respond('error', {'message': f"Tool '{tool_name}' already exists. Use modify_tool to update."})
            return tasks

        # Create tool entry
        tool_entry = {
            'name': tool_name,
            'description': description,
            'created': datetime.now().isoformat(),
            'script': f'{tool_name}.py',
            'enabled': True
        }

        # Create a stub script file
        script_path = temp_scripts_dir / f'{tool_name}.py'
        script_template = f'''#!/usr/bin/env python3
"""
{tool_name} - Runtime tool for CORA

Description: {description}
Created: {datetime.now().isoformat()}

This is a runtime-created tool. Modify as needed.
"""

def run(args=None):
    """Main entry point for the tool."""
    args = args or []
    # TODO: Implement tool logic here
    print(f"[{tool_name}] Running with args: {{args}}")
    return {{"success": True, "message": "Tool executed"}}


if __name__ == "__main__":
    import sys
    run(sys.argv[1:])
'''
        with open(script_path, 'w') as f:
            f.write(script_template)

        # Update registry
        registry['tools'].append(tool_entry)
        with open(registry_file, 'w') as f:
            json.dump(registry, f, indent=2)

        respond('info', {'message': f"Created tool '{tool_name}'"})
        print(f"Script: {script_path}")
        print("Edit the script to add your tool logic.")

    except Exception as e:
        respond('error', {'message': f"Failed to create tool: {e}"})

    return tasks


def cmd_modify_tool(args, tasks):
    from src.cora_parts.chat import respond
    """Modify an existing runtime tool. Usage: modify_tool <name> [enable|disable|delete]

    Per ARCHITECTURE.md P4-SELF: Self-modification capabilities.
    """
    if not args:
        respond('error', {'message': "Usage: modify_tool <name> [enable|disable|delete]"})
        return tasks

    tool_name = args[0].lower()
    action = args[1].lower() if len(args) > 1 else 'show'

    try:
        temp_scripts_dir = DATA_DIR / 'tools' / 'temp_scripts'
        registry_file = temp_scripts_dir / 'tool_registry.json'

        if not registry_file.exists():
            respond('error', {'message': "No tools registry found. Create a tool first."})
            return tasks

        with open(registry_file) as f:
            registry = json.load(f)

        # Find tool
        tool_index = None
        tool_entry = None
        for i, t in enumerate(registry.get('tools', [])):
            if t.get('name') == tool_name:
                tool_index = i
                tool_entry = t
                break

        if tool_entry is None:
            respond('error', {'message': f"Tool '{tool_name}' not found."})
            print("Available tools:")
            for t in registry.get('tools', []):
                print(f"  - {t['name']}: {t.get('description', '')[:40]}")
            return tasks

        if action == 'show':
            print(f"\n=== TOOL: {tool_name} ===")
            print(f"Description: {tool_entry.get('description', 'N/A')}")
            print(f"Created:     {tool_entry.get('created', 'N/A')[:10]}")
            print(f"Enabled:     {tool_entry.get('enabled', True)}")
            print(f"Script:      {temp_scripts_dir / tool_entry.get('script', 'N/A')}")

        elif action == 'enable':
            tool_entry['enabled'] = True
            with open(registry_file, 'w') as f:
                json.dump(registry, f, indent=2)
            respond('info', {'message': f"Tool '{tool_name}' enabled."})

        elif action == 'disable':
            tool_entry['enabled'] = False
            with open(registry_file, 'w') as f:
                json.dump(registry, f, indent=2)
            respond('info', {'message': f"Tool '{tool_name}' disabled."})

        elif action == 'delete':
            # Remove from registry
            registry['tools'].pop(tool_index)
            with open(registry_file, 'w') as f:
                json.dump(registry, f, indent=2)

            # Delete script file
            script_path = temp_scripts_dir / tool_entry.get('script', '')
            if script_path.exists():
                script_path.unlink()

            respond('info', {'message': f"Tool '{tool_name}' deleted."})

        else:
            respond('error', {'message': f"Unknown action: {action}. Use: enable, disable, delete, or show"})

    except Exception as e:
        respond('error', {'message': f"Failed to modify tool: {e}"})

    return tasks


def cmd_imagine(args, tasks):
    from src.cora_parts.logging_setup import logger
    from src.cora_parts.chat import respond
    """Generate an image from a text prompt. Usage: imagine <description>

    Uses Pollinations.AI via PolliLibPy for image generation.
    """
    if not args:
        respond('error', {'message': "What should I create? Usage: imagine <description>"})
        return tasks

    prompt = ' '.join(args)

    try:
        from cora_tools.image_gen import generate_image, show_fullscreen_image

        print(f"[CORA]: Creating image: {prompt[:50]}...")
        speak("Generating image. This might take a moment.")

        result = generate_image(prompt=prompt, width=1024, height=1024)

        if result["success"]:
            print(f"[CORA]: Image saved: {result['path']}")
            print(f"[CORA]: Generated in {result['inference_time']:.1f}s")
            speak("Done. Opening image.")

            # Show the image
            show_fullscreen_image(result['path'])
        else:
            respond('error', {'message': f"Generation failed: {result.get('error', 'Unknown')}"})

    except ImportError as e:
        logger.error(f"Image module not available: {e}")
        respond('error', {'message': f"Image module not available: {e}"})
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        respond('error', {'message': f"Image error: {e}"})

    return tasks


def cmd_see(args, tasks):
    from src.cora_parts.logging_setup import logger
    from src.cora_parts.chat import respond
    """See through the camera - describe what's visible. Usage: see [question]

    Uses webcam + the configured Ollama vision model to analyze what's visible.
    """
    try:
        from services.presence import capture_webcam, ask_vision

        print("[CORA]: Accessing visual cortex...")
        speak("Let me take a look.")

        # Capture from webcam
        image_path = capture_webcam()
        if not image_path:
            respond('error', {'message': "Camera offline. Can't see shit."})
            return tasks

        # Build vision prompt
        if args:
            question = ' '.join(args)
        else:
            question = "Describe what you see in detail. Include people, objects, environment, lighting, and mood."

        print("[CORA]: Processing visual data...")

        # Use Ollama llava to analyze
        description = ask_vision(image_path, question)

        if description:
            print(f"[CORA]: {description}")
            speak(description[:150])
        else:
            respond('error', {'message': "Vision processing failed. Try again."})

    except ImportError as e:
        logger.error(f"Vision module not loaded: {e}")
        respond('error', {'message': f"Vision module not loaded: {e}"})
    except Exception as e:
        logger.error(f"Vision error: {e}")
        respond('error', {'message': f"Vision error: {e}"})

    return tasks


def cmd_list_tools(args, tasks):
    from src.cora_parts.chat import respond
    """List all runtime tools. Usage: list_tools"""
    try:
        temp_scripts_dir = DATA_DIR / 'tools' / 'temp_scripts'
        registry_file = temp_scripts_dir / 'tool_registry.json'

        if not registry_file.exists():
            print("No runtime tools created yet.")
            print("Use 'create_tool <name> <description>' to create one.")
            return tasks

        with open(registry_file) as f:
            registry = json.load(f)

        tools = registry.get('tools', [])
        if not tools:
            print("No runtime tools created yet.")
            return tasks

        print("\n=== RUNTIME TOOLS ===")
        print("-" * 50)
        for t in tools:
            status = "[ON]" if t.get('enabled', True) else "[OFF]"
            print(f"  {status} {t['name']}: {t.get('description', '')[:40]}")
        print("-" * 50)
        print(f"Total: {len(tools)} tools")

    except Exception as e:
        respond('error', {'message': f"Failed to list tools: {e}"})

    return tasks
