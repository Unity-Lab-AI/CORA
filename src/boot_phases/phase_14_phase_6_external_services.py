#!/usr/bin/env python3
"""PHASE 6: EXTERNAL SERVICES

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
    # PHASE 6: EXTERNAL SERVICES
    # ================================================================
    _m.display_phase("6.0 External APIs", "running")
    _m.display_log("PHASE 6: EXTERNAL SERVICES", "phase")
    print("\n[PHASE 6] External Services")
    print("=" * 50)

    # GET LOCATION FIRST - needed for accurate weather
    location_str = None
    city_for_weather = None
    try:
        from services.location import get_location
        _m.display_tool("Location Service", "Getting current location")
        loc = get_location()
        if loc:
            city = loc.get('city', '')
            region = loc.get('region', loc.get('state', ''))
            country = loc.get('country', '')
            # Build location string from available data
            loc_parts = [p for p in [city, region, country] if p]
            location_str = ', '.join(loc_parts) if loc_parts else None
            # Use city for weather lookup
            city_for_weather = city if city else None
            if location_str:
                print(f"  [OK] Location: {location_str}")
                _m.display_result(f"We're in {location_str}")
                _m.BOOT_STATUS['location'] = loc
                _m.BOOT_STATUS['systems'].append({'name': 'Location', 'status': 'OK'})
                # CORA announces location
                response = _m.cora_respond("Location check", f"Location: {location_str}", "ok")
                _m.speak(response)
            else:
                print("  [WARN] Location data incomplete")
                _m.display_log("Location data incomplete", "warn")
                _m.BOOT_STATUS['systems'].append({'name': 'Location', 'status': 'WARN'})
        else:
            print("  [WARN] Location unavailable")
            _m.display_log("Location unavailable", "warn")
            _m.BOOT_STATUS['systems'].append({'name': 'Location', 'status': 'WARN'})
    except Exception as e:
        print(f"  [WARN] Location: {e}")
        _m.display_log(f"Location: {e}", "warn")
        _m.BOOT_STATUS['systems'].append({'name': 'Location', 'status': 'WARN'})

    # NOW GET WEATHER using location
    L.weather_data = None
    forecast_data = None
    try:
        from services.weather import get_weather, get_forecast
        # Pass location to weather service
        L.weather_data = get_weather(city_for_weather)
        forecast_data = get_forecast(city_for_weather, days=3)  # Get 3-day forecast

        if L.weather_data and L.weather_data.get('success'):
            temp = L.weather_data.get('temp', '?')
            cond = L.weather_data.get('conditions', '?')
            feels = L.weather_data.get('feels_like', '')
            humidity = L.weather_data.get('humidity', '')
            wind = L.weather_data.get('wind', '')

            print(f"  [OK] Current Weather for {city_for_weather or 'your area'}: {temp}, {cond}")
            _m.display_log(f"Current: {temp}, {cond}", "ok")
            if feels:
                _m.display_log(f"  Feels like: {feels}", "info")
            if humidity:
                _m.display_log(f"  Humidity: {humidity}", "info")
            if wind:
                _m.display_log(f"  Wind: {wind}", "info")

            _m.BOOT_STATUS['weather'] = L.weather_data
            _m.BOOT_STATUS['systems'].append({'name': 'Weather', 'status': 'OK'})

            # Get 3-day forecast info
            if forecast_data and forecast_data.get('success') and forecast_data.get('forecast'):
                print(f"  [OK] 3-Day Forecast:")
                _m.display_log("3-Day Forecast:", "ok")
                for day in forecast_data['forecast']:
                    day_name = day.get('day_name', 'Unknown')
                    high = day.get('high', '?')
                    low = day.get('low', '?')
                    conditions = day.get('conditions', '')
                    print(f"       {day_name}: High {high}, Low {low} - {conditions}")
                    _m.display_log(f"  {day_name}: {high}/{low} - {conditions}", "info")
                _m.BOOT_STATUS['forecast'] = forecast_data
        else:
            print("  [WARN] Weather service unavailable")
            _m.display_log("Weather service unavailable", "warn")
            _m.BOOT_STATUS['systems'].append({'name': 'Weather', 'status': 'WARN'})
    except Exception as e:
        print(f"  [WARN] Weather: {e}")
        _m.display_log(f"Weather: {e}", "warn")
        _m.BOOT_STATUS['systems'].append({'name': 'Weather', 'status': 'WARN'})

    # Notifications
    try:
        from services.notifications import notify
        print("  [OK] Notifications")
        _m.display_log("Notifications system loaded", "ok")
        _m.BOOT_STATUS['systems'].append({'name': 'Notifications', 'status': 'OK'})
    except Exception as e:
        print(f"  [WARN] Notifications: {e}")
        _m.display_log(f"Notifications: {e}", "warn")
        _m.BOOT_STATUS['systems'].append({'name': 'Notifications', 'status': 'WARN'})

    # Hotkeys
    try:
        from services.hotkeys import setup_cora_hotkeys
        print("  [OK] Hotkey System")
        _m.display_log("Hotkey System loaded", "ok")
        _m.BOOT_STATUS['systems'].append({'name': 'Hotkeys', 'status': 'OK'})
    except Exception as e:
        print(f"  [WARN] Hotkeys: {e}")
        _m.display_log(f"Hotkeys: {e}", "warn")
        _m.BOOT_STATUS['systems'].append({'name': 'Hotkeys', 'status': 'WARN'})

    _m.display_phase("6.0 External APIs", "ok")

    # Helper to convert temp like "61F" to "61 degrees fahrenheit"
    def speak_temp(temp_str):
        if not temp_str or temp_str == '?' or temp_str == 'N/A':
            return "unknown"
        # Remove F and convert to natural speech
        temp_str = temp_str.replace('F', '').replace('°', '').strip()
        return f"{temp_str} degrees"

    # Build weather report with 3-day forecast - natural speech
    # Location already announced separately, so just do weather
    weather_report = ""
    if L.weather_data and L.weather_data.get('success'):
        temp = L.weather_data.get('temp', '?')
        cond = L.weather_data.get('conditions', '?')
        # Convert temp for natural speech
        temp_spoken = speak_temp(temp)
        weather_report += f"Currently {temp_spoken} and {cond.lower()}. "
        if forecast_data and forecast_data.get('success') and forecast_data.get('forecast'):
            # Today's forecast with conditions
            today = forecast_data['forecast'][0]
            today_high = speak_temp(today.get('high', '?'))
            today_low = speak_temp(today.get('low', '?'))
            today_cond = today.get('conditions', '')
            if today_cond:
                weather_report += f"Today will be {today_cond.lower()} with a high of {today_high} and a low of {today_low}. "
            else:
                weather_report += f"Today the high will be {today_high} and the low will be {today_low}. "
            # Rest of the week with conditions
            if len(forecast_data['forecast']) > 1:
                for day in forecast_data['forecast'][1:]:
                    day_name = day.get('day_name', '')
                    day_high = speak_temp(day.get('high', '?'))
                    day_low = speak_temp(day.get('low', '?'))
                    day_cond = day.get('conditions', '')
                    if day_cond:
                        weather_report += f"{day_name} will be {day_cond.lower()} with a high of {day_high} and a low of {day_low}. "
                    else:
                        weather_report += f"{day_name} the high will be {day_high} and the low will be {day_low}. "
    else:
        weather_report += "Weather unavailable."

    response = _m.cora_respond("Location and Weather", weather_report, "ok" if L.weather_data else "warn", mode="full")
    _m.speak(response)
    _m.responsive_sleep(0.3)
