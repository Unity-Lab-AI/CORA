#!/usr/bin/env python3
"""PHASE 7: NEWS HEADLINES

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
    # PHASE 7: NEWS HEADLINES
    # ================================================================
    _m.display_phase("7.0 News Headlines", "running")
    _m.display_log("PHASE 7: NEWS HEADLINES", "phase")
    print("\n[PHASE 7] News Headlines")
    print("=" * 50)

    headlines = []
    try:
        import requests
        import re
        print("  Fetching top headlines from Google News...")
        _m.display_tool("HTTP Request", "Fetching Google News RSS")
        _m.display_action("GET https://news.google.com/rss")

        # Use Google News RSS for real headlines
        url = 'https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en'
        resp = requests.get(url, timeout=10)

        if resp.status_code == 200:
            _m.display_result(f"HTTP 200 OK - {len(resp.text)} bytes")
            _m.display_action("Parsing RSS feed for headlines...")

            # Parse RSS titles
            titles = re.findall(r'<title>([^<]+)</title>', resp.text)

            # Skip first 2 (channel title and description)
            for t in titles[2:7]:
                # Clean up the headline
                headline = t.strip()
                if headline and len(headline) > 10:
                    headlines.append(headline)

            print("  [OK] News fetch successful")
            _m.display_result(f"Found {len(headlines)} headlines")
            _m.BOOT_STATUS['tools_tested'].append({'name': 'News Headlines', 'status': 'OK'})

            for i, hl in enumerate(headlines[:3], 1):
                print(f"  {i}. {hl[:75]}...")
                _m.display_log(f"Headline {i}: {hl[:60]}...", "info")

            _m.BOOT_STATUS['headlines'] = headlines

            # Announce top 3-4 headlines
            if headlines:
                _m.display_phase("7.0 News Headlines", "ok")
                # Clean headlines for speech
                clean_headlines = []
                for hl in headlines[:4]:
                    clean = hl.split(' - ')[0] if ' - ' in hl else hl
                    if len(clean) > 100:
                        clean = clean[:97] + "..."
                    clean_headlines.append(clean)

                # News - full mode for longer content
                news_data = "Top headlines: " + ". ".join(clean_headlines)
                response = _m.cora_respond("News Headlines", news_data, "ok", mode="full")
                _m.speak(response)
            else:
                _m.display_phase("7.0 News Headlines", "warn")
                response = _m.cora_respond("News Headlines", "No headlines found.", "warn")
                _m.speak(response)
        else:
            print("  [WARN] News fetch failed")
            _m.display_log(f"News fetch failed (HTTP {resp.status_code})", "warn")
            _m.BOOT_STATUS['tools_tested'].append({'name': 'News Headlines', 'status': 'WARN'})
            _m.display_phase("7.0 News Headlines", "warn")
            response = _m.cora_respond("News Headlines", f"News failed. HTTP {resp.status_code}.", "fail")
            _m.speak(response)

    except Exception as e:
        print(f"  [WARN] News fetch: {e}")
        _m.display_log(f"News fetch error: {e}", "warn")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'Web Search', 'status': 'WARN'})
        _m.display_phase("7.0 News Headlines", "warn")
        response = _m.cora_respond("News Headlines", "News fetch error.", "fail")
        _m.speak(response)

    _m.responsive_sleep(0.3)
