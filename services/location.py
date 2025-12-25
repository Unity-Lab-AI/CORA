"""
C.O.R.A Location Services Module

IP geolocation and location services.
Per ARCHITECTURE.md v1.0.0: Location detection via ip-api.com.
"""

import json
import urllib.request
import urllib.error


def get_location_from_ip():
    """Get location from IP address using ip-api.com.

    Returns:
        dict: Location data including city, region, country, lat, lon
    """
    try:
        req = urllib.request.Request(
            'http://ip-api.com/json/',
            headers={'User-Agent': 'CORA/2.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())

            if data.get('status') == 'success':
                return {
                    'city': data.get('city', 'Unknown'),
                    'region': data.get('regionName', ''),
                    'country': data.get('country', ''),
                    'country_code': data.get('countryCode', ''),
                    'lat': data.get('lat', 0),
                    'lon': data.get('lon', 0),
                    'timezone': data.get('timezone', ''),
                    'isp': data.get('isp', ''),
                    'ip': data.get('query', '')
                }
            else:
                return None
    except Exception as e:
        print(f"[!] Location lookup failed: {e}")
        return None


def get_location(config=None):
    """Get current location.

    Args:
        config: Optional config dict with location settings

    Returns:
        dict: Location data or None
    """
    # Check if location is configured in config
    if config:
        loc_config = config.get('location', {})
        if loc_config.get('manual'):
            return {
                'city': loc_config.get('city', 'Unknown'),
                'region': loc_config.get('region', ''),
                'country': loc_config.get('country', ''),
                'lat': loc_config.get('lat', 0),
                'lon': loc_config.get('lon', 0),
                'timezone': loc_config.get('timezone', ''),
                'source': 'config'
            }

    # Fall back to IP geolocation
    location = get_location_from_ip()
    if location:
        location['source'] = 'ip'
    return location


def get_coordinates(location=None):
    """Get latitude and longitude.

    Args:
        location: Optional location dict. If None, fetches from IP.

    Returns:
        tuple: (lat, lon) or (0, 0) if unavailable
    """
    if location is None:
        location = get_location_from_ip()

    if location:
        return (location.get('lat', 0), location.get('lon', 0))
    return (0, 0)


def get_timezone(location=None):
    """Get timezone for location.

    Args:
        location: Optional location dict. If None, fetches from IP.

    Returns:
        str: Timezone string (e.g., 'America/Denver') or empty string
    """
    if location is None:
        location = get_location_from_ip()

    if location:
        return location.get('timezone', '')
    return ''


def format_location_string(location):
    """Format location as readable string.

    Args:
        location: Location dict

    Returns:
        str: Formatted location (e.g., "Denver, Colorado, USA")
    """
    if not location:
        return "Unknown location"

    parts = []
    if location.get('city'):
        parts.append(location['city'])
    if location.get('region'):
        parts.append(location['region'])
    if location.get('country'):
        parts.append(location['country'])

    return ', '.join(parts) if parts else "Unknown location"


def get_location_summary(location=None):
    """Get a spoken summary of location for TTS.

    Args:
        location: Optional location dict. If None, fetches from IP.

    Returns:
        str: Natural language location summary
    """
    if location is None:
        location = get_location_from_ip()

    if not location:
        return "I couldn't determine your location."

    city = location.get('city', '')
    region = location.get('region', '')

    if city and region:
        return f"You're in {city}, {region}."
    elif city:
        return f"You're in {city}."
    else:
        return "Location detected but details unavailable."
