#!/usr/bin/env python3
"""
C.O.R.A Services Module
External API integrations for weather, location, notifications
"""

from .weather import get_weather, get_forecast, get_weather_summary, get_forecast_summary
from .location import get_location, get_location_from_ip, get_coordinates, get_timezone
from .notifications import notify, notify_toast, notify_async, show_reminder

__all__ = [
    # Weather
    'get_weather',
    'get_forecast',
    'get_weather_summary',
    'get_forecast_summary',
    # Location
    'get_location',
    'get_location_from_ip',
    'get_coordinates',
    'get_timezone',
    # Notifications
    'notify',
    'notify_toast',
    'notify_async',
    'show_reminder',
]
