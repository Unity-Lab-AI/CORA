#!/usr/bin/env python3
"""
C.O.R.A Weather Service
Weather API integration using wttr.in (free, no API key required)

Per ARCHITECTURE.md:
- Current conditions (temp, sky, precipitation)
- Forecast (high/low, precipitation)
- Natural language summaries for TTS
"""

import requests
from typing import Dict, Optional, Any
from datetime import datetime


def get_weather(location: Optional[str] = None) -> Dict[str, Any]:
    """Get current weather conditions.

    Args:
        location: City name or coordinates. If None, uses IP geolocation.

    Returns:
        Dict with weather data:
        - temp: Temperature string (e.g., "45F")
        - conditions: Sky conditions (e.g., "Partly cloudy")
        - humidity: Humidity percentage
        - wind: Wind speed and direction
        - feels_like: "Feels like" temperature
        - raw: Raw response text
    """
    try:
        # wttr.in format codes:
        # %t = temperature, %C = condition, %h = humidity
        # %w = wind, %f = feels like
        url = f"https://wttr.in/{location or ''}?format=%t|%C|%h|%w|%f"

        resp = requests.get(url, timeout=10, headers={'User-Agent': 'CORA/2.0'})

        if resp.status_code == 200:
            parts = resp.text.strip().split('|')
            if len(parts) >= 5:
                return {
                    'temp': parts[0].strip(),
                    'conditions': parts[1].strip(),
                    'humidity': parts[2].strip(),
                    'wind': parts[3].strip(),
                    'feels_like': parts[4].strip(),
                    'raw': resp.text.strip(),
                    'success': True
                }
    except requests.RequestException as e:
        pass

    return {
        'temp': 'N/A',
        'conditions': 'Weather unavailable',
        'humidity': 'N/A',
        'wind': 'N/A',
        'feels_like': 'N/A',
        'raw': '',
        'success': False
    }


def get_forecast(location: Optional[str] = None, days: int = 1) -> Dict[str, Any]:
    """Get weather forecast.

    Args:
        location: City name or coordinates
        days: Number of days (1-3)

    Returns:
        Dict with forecast data including high/low and precipitation
    """
    try:
        # Get JSON format for more detailed forecast
        url = f"https://wttr.in/{location or ''}?format=j1"

        resp = requests.get(url, timeout=10, headers={'User-Agent': 'CORA/2.0'})

        if resp.status_code == 200:
            data = resp.json()

            # Parse current conditions
            current = data.get('current_condition', [{}])[0]

            # Parse forecast
            weather = data.get('weather', [])
            forecast_days = []

            for i, day in enumerate(weather[:days]):
                forecast_days.append({
                    'date': day.get('date', ''),
                    'high': day.get('maxtempF', 'N/A') + 'F',
                    'low': day.get('mintempF', 'N/A') + 'F',
                    'avg': day.get('avgtempF', 'N/A') + 'F',
                    'hourly': day.get('hourly', [])
                })

            return {
                'current': {
                    'temp': current.get('temp_F', 'N/A') + 'F',
                    'conditions': current.get('weatherDesc', [{}])[0].get('value', 'N/A'),
                    'humidity': current.get('humidity', 'N/A') + '%',
                    'wind': f"{current.get('windspeedMiles', 'N/A')} mph {current.get('winddir16Point', '')}",
                    'feels_like': current.get('FeelsLikeF', 'N/A') + 'F'
                },
                'forecast': forecast_days,
                'success': True
            }
    except (requests.RequestException, ValueError, KeyError) as e:
        pass

    return {
        'current': None,
        'forecast': [],
        'success': False
    }


def get_weather_summary(location: Optional[str] = None) -> str:
    """Get a natural language weather summary for TTS.

    Args:
        location: City name or coordinates

    Returns:
        Natural language string suitable for TTS
    """
    weather = get_weather(location)

    if weather['success']:
        temp = weather['temp']
        conditions = weather['conditions'].lower()
        return f"It's {temp} and {conditions} outside."
    else:
        return "I couldn't get the weather right now."


def get_forecast_summary(location: Optional[str] = None) -> str:
    """Get a natural language forecast summary for TTS.

    Args:
        location: City name or coordinates

    Returns:
        Natural language string suitable for TTS
    """
    forecast = get_forecast(location, days=1)

    if forecast['success'] and forecast['forecast']:
        day = forecast['forecast'][0]
        high = day['high']
        low = day['low']

        # Check for precipitation keywords
        hourly = day.get('hourly', [])
        precip_keywords = []
        for hour in hourly:
            desc = hour.get('weatherDesc', [{}])[0].get('value', '').lower()
            if 'rain' in desc:
                precip_keywords.append('rain')
            elif 'snow' in desc:
                precip_keywords.append('snow')
            elif 'thunder' in desc:
                precip_keywords.append('storms')

        summary = f"Today's high is {high}, low {low}."

        if precip_keywords:
            unique_precip = list(set(precip_keywords))
            summary += f" Expect {', '.join(unique_precip)} later."

        return summary
    else:
        return "Forecast unavailable."


if __name__ == "__main__":
    # Test weather service
    print("=== WEATHER TEST ===")
    weather = get_weather()
    print(f"Current: {weather}")

    print("\n=== FORECAST TEST ===")
    forecast = get_forecast()
    print(f"Forecast: {forecast}")

    print("\n=== SUMMARIES ===")
    print(f"Weather: {get_weather_summary()}")
    print(f"Forecast: {get_forecast_summary()}")
