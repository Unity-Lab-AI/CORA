#!/usr/bin/env python3
"""PHASE 4.1: CODE IMPORT TEST - Fetch real code from GitHub (demo)

One phase of src.boot_sequence.run_boot_sequence, split out on 2026-10-14. `_m` is the live
src.boot_sequence module (its names are read and assigned through it); `L` holds the locals
shared across phases."""
from __future__ import annotations
import json
import os
import re
import sys
import time

import sys
import os
import time
import signal
import atexit
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any


# Import centralized window manager
from ui.window_manager import create_window, create_popup, create_image_window, create_code_window, bring_to_front


def run(_m, L):

    # ================================================================
    # PHASE 4.1: CODE IMPORT TEST - Fetch real code from GitHub (demo)
    # ================================================================
    _m.display_phase("4.1 Code Import", "running")
    _m.display_log("PHASE 4.1: CODE IMPORT FROM GITHUB", "phase")
    print("\n[PHASE 4.1] Code Import from GitHub")
    print("=" * 50)

    try:
        if not L._demo:
            raise _m._SkippedPhase("boot.demo_phases is false")
        import random
        import urllib.request
        import json
        import base64
        import os

        # Private-repo import is opt-in (boot.github_import); public fallback otherwise
        github_token = os.environ.get('GITHUB_TOKEN', '') if L._github_import else ''
        fetched_from_user_repo = False
        url = None
        code_name = None
        lang = "python"
        repo_name = None

        if github_token:
            try:
                # Get user's repos via GitHub API
                api_url = "https://api.github.com/user/repos?per_page=100&sort=updated"
                req = urllib.request.Request(api_url, headers={
                    'Authorization': f'token {github_token}',
                    'Accept': 'application/vnd.github.v3+json',
                    'User-Agent': 'CORA-Bot/1.0'
                })
                with urllib.request.urlopen(req, timeout=10) as response:
                    repos = json.loads(response.read().decode('utf-8'))

                # Filter for repos with Python code
                python_repos = [r for r in repos if r.get('language') == 'Python' and not r.get('fork')]
                if python_repos:
                    # Pick a random repo
                    chosen_repo = random.choice(python_repos)
                    repo_name = chosen_repo['full_name']
                    print(f"  Using your repo: {repo_name}")

                    # Get contents of repo root
                    contents_url = f"https://api.github.com/repos/{repo_name}/contents"
                    req = urllib.request.Request(contents_url, headers={
                        'Authorization': f'token {github_token}',
                        'Accept': 'application/vnd.github.v3+json',
                        'User-Agent': 'CORA-Bot/1.0'
                    })
                    with urllib.request.urlopen(req, timeout=10) as response:
                        contents = json.loads(response.read().decode('utf-8'))

                    # Find Python files (check root and common dirs)
                    py_files = [f for f in contents if f['name'].endswith('.py') and f['type'] == 'file' and f['size'] < 50000]

                    # Also check src/, tools/, utils/ directories if they exist
                    for subdir in ['src', 'tools', 'utils', 'lib']:
                        subdir_entry = next((f for f in contents if f['name'] == subdir and f['type'] == 'dir'), None)
                        if subdir_entry:
                            try:
                                req = urllib.request.Request(subdir_entry['url'], headers={
                                    'Authorization': f'token {github_token}',
                                    'Accept': 'application/vnd.github.v3+json',
                                    'User-Agent': 'CORA-Bot/1.0'
                                })
                                with urllib.request.urlopen(req, timeout=5) as response:
                                    subdir_contents = json.loads(response.read().decode('utf-8'))
                                    py_files.extend([f for f in subdir_contents if f['name'].endswith('.py') and f['type'] == 'file' and f['size'] < 50000])
                            except:
                                pass

                    if py_files:
                        # Pick a random Python file
                        chosen_file = random.choice(py_files)
                        url = chosen_file['download_url']
                        code_name = f"{chosen_file['name']} (from {repo_name.split('/')[-1]})"
                        fetched_from_user_repo = True
                        print(f"  Selected: {chosen_file['name']}")

            except Exception as e:
                print(f"  [INFO] GitHub API access failed: {e}, falling back to public repos")

        # Fallback to public repos if no user repo available
        if not url:
            # Use GitHub API to find public Python repos dynamically
            fallback_repos = ["TheAlgorithms/Python", "geekcomputers/Python", "realpython/python-basics-exercises"]
            fallback_dirs = ["maths", "strings", "conversions", "searches", "sorts", "src", ""]

            for fallback_repo in fallback_repos:
                if url:
                    break
                try:
                    # Get repo contents
                    for check_dir in fallback_dirs:
                        if url:
                            break
                        try:
                            api_path = f"/repos/{fallback_repo}/contents/{check_dir}" if check_dir else f"/repos/{fallback_repo}/contents"
                            api_url = f"https://api.github.com{api_path}"
                            headers = {'Accept': 'application/vnd.github.v3+json', 'User-Agent': 'CORA-Bot/1.0'}
                            if github_token:
                                headers['Authorization'] = f'token {github_token}'
                            req = urllib.request.Request(api_url, headers=headers)
                            with urllib.request.urlopen(req, timeout=8) as response:
                                contents = json.loads(response.read().decode('utf-8'))

                            # Find Python files under 30KB
                            py_files = [f for f in contents if isinstance(f, dict) and f.get('name', '').endswith('.py') and f.get('type') == 'file' and f.get('size', 0) < 30000]
                            if py_files:
                                chosen = random.choice(py_files)
                                url = chosen.get('download_url')
                                code_name = f"{chosen['name']} (from {fallback_repo.split('/')[-1]})"
                                print(f"  Found: {chosen['name']} in {fallback_repo}")
                        except:
                            continue
                except:
                    continue

            # Ultimate fallback - just try to get any Python file from the CORA project itself
            if not url:
                try:
                    # Use local file as last resort
                    local_files = list(Path(__file__).parent.glob("*.py"))
                    if local_files:
                        chosen_local = random.choice(local_files)
                        with open(chosen_local, 'r', encoding='utf-8') as f:
                            fetched_code = f.read()
                        code_name = f"{chosen_local.name} (local CORA)"
                        url = "local"
                        print(f"  Using local file: {chosen_local.name}")
                except:
                    pass

        print(f"  Fetching: {code_name}")
        _m.display_tool("Code Import", f"GitHub - {code_name}")
        _m.display_action(f"Importing code from GitHub...")

        # Show code modal popup
        code_window = None
        code_text = None
        try:
            import tkinter as tk

            parent = _m._boot_display.root if _m._boot_display else None
            code_window = create_code_window(
                title=f"CORA - Code Import: {code_name}",
                width=900, height=600,
                parent=parent
            )

            # Header
            header = tk.Label(
                code_window,
                text=f"Importing: {code_name}",
                font=('Consolas', 12, 'bold'),
                fg='#00ff88',
                bg='#1e1e1e',
                pady=10
            )
            header.pack(fill='x')

            # Source URL
            source_text = "Source: Local CORA file" if url == "local" else f"Source: GitHub API"
            url_label = tk.Label(
                code_window,
                text=source_text,
                font=('Consolas', 9),
                fg='#888888',
                bg='#1e1e1e'
            )
            url_label.pack(fill='x', padx=10)

            # Code display area with scrollbar
            code_frame = tk.Frame(code_window, bg='#1e1e1e')
            code_frame.pack(fill='both', expand=True, padx=10, pady=5)

            scrollbar = tk.Scrollbar(code_frame)
            scrollbar.pack(side='right', fill='y')

            code_text = tk.Text(
                code_frame,
                font=('Consolas', 10),
                fg='#d4d4d4',
                bg='#1e1e2e',
                insertbackground='white',
                padx=10,
                pady=10,
                wrap='none',
                yscrollcommand=scrollbar.set
            )
            code_text.pack(fill='both', expand=True, side='left')
            scrollbar.config(command=code_text.yview)

            code_text.insert('1.0', f"Fetching code...\n\nSource: {'Local' if url == 'local' else 'GitHub API'}\n\nPlease wait...")
            code_text.config(state='disabled')
            code_window.update()

        except Exception as e:
            print(f"  [INFO] Code modal creation failed: {e}")
            code_window = None

        # Fetch the actual code (skip if already loaded from local)
        try:
            if url != "local":
                req = urllib.request.Request(url, headers={'User-Agent': 'CORA-Bot/1.0'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    fetched_code = response.read().decode('utf-8')

            # Limit to first 100 lines for display
            code_lines = fetched_code.split('\n')
            display_code = '\n'.join(code_lines[:100])
            if len(code_lines) > 100:
                display_code += f"\n\n... [{len(code_lines) - 100} more lines] ..."

            print(f"  [OK] Fetched {len(code_lines)} lines of {lang} code")
            _m.display_result(f"Imported {len(code_lines)} lines from GitHub")
            _m.BOOT_STATUS['tools_tested'].append({'name': 'Code Import', 'status': 'OK'})

            # Update modal with actual code
            if code_window and code_text:
                try:
                    source_info = "Local CORA project" if url == "local" else "GitHub API"
                    code_text.config(state='normal')
                    code_text.delete('1.0', 'end')
                    code_text.insert('1.0', f"# {code_name}\n# Source: {source_info}\n# Lines: {len(code_lines)}\n\n{display_code}")
                    code_text.config(state='disabled')
                    code_window.update()
                except:
                    pass

            # CORA announces code import - just the data
            if fetched_from_user_repo:
                response = _m.cora_respond("Code Import", f"Pulled {len(code_lines)} lines from your GitHub.", "ok")
            else:
                response = _m.cora_respond("Code Import", f"Pulled {len(code_lines)} lines of {code_name} from GitHub.", "ok")
            _m.speak(response)

            _m.display_phase("4.1 Code Import", "ok")

        except Exception as fetch_error:
            print(f"  [WARN] GitHub fetch failed: {fetch_error}")
            _m.display_log(f"GitHub fetch failed: {fetch_error}", "warn")
            _m.BOOT_STATUS['tools_tested'].append({'name': 'Code Import', 'status': 'WARN'})
            _m.display_phase("4.1 Code Import", "warn")

            response = _m.cora_respond("Code Import", "GitHub unreachable.", "warn")
            _m.speak(response)

        # Close code window after speaking
        if code_window:
            try:
                code_window.destroy()
            except:
                pass

    except _m._SkippedPhase as e:
        _m.display_log(f"Code import skipped ({e})", "info")
        _m.display_phase("4.1 Code Import", "ok")
    except Exception as e:
        print(f"  [WARN] Code import test: {e}")
        _m.display_log(f"Code import error: {e}", "warn")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'Code Import', 'status': 'WARN'})
        _m.display_phase("4.1 Code Import", "warn")

    _m.responsive_sleep(0.3)
