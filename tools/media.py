"""
# ================================================================
#   ____   ___   ____      _
#  / ___| / _ \ |  _ \    / \
# | |    | | | || |_) |  / _ \
# | |___ | |_| ||  _ <  / ___ \
#  \____| \___/ |_| \_\/_/   \_\
#
# C.O.R.A Media Control Module (Emby Integration)
# ================================================================
# Version: 2.3.0
# Unity AI Lab
# Website: https://www.unityailab.com
# GitHub: https://github.com/Unity-Lab-AI
# Contact: unityailabcontact@gmail.com
# Creators: Hackall360, Sponge, GFourteen
# ================================================================
#
# Control Emby media server - play music, videos, search library.
# Requires Emby server and API key configured.
#
# ================================================================
"""

import os
import json
import requests
from pathlib import Path
from typing import Optional, List, Dict, Any


# Config
CONFIG_DIR = Path(__file__).parent.parent / 'config'
MEDIA_CONFIG_FILE = CONFIG_DIR / 'media_config.json'


def load_media_config() -> dict:
    """Load media server configuration.

    Config file should contain:
    {
        "emby_server": "192.168.1.100",
        "emby_port": "8096",
        "emby_api_key": "your-api-key"
    }
    """
    if MEDIA_CONFIG_FILE.exists():
        try:
            with open(MEDIA_CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass

    # Fallback to environment variables
    return {
        'emby_server': os.getenv('EMBY_SERVER', ''),
        'emby_port': os.getenv('EMBY_PORT', '8096'),
        'emby_api_key': os.getenv('EMBY_API_KEY', '')
    }


class EmbyControl:
    """Control Emby media server - play, pause, search, etc."""

    def __init__(self, config: dict = None):
        if config is None:
            config = load_media_config()

        server = config.get('emby_server', '')
        port = config.get('emby_port', '8096')
        self.api_key = config.get('emby_api_key', '')

        self.base_url = f"http://{server}:{port}/emby" if server else ''
        self.headers = {'X-Emby-Token': self.api_key} if self.api_key else {}
        self.configured = bool(server and self.api_key)

    def _check_configured(self) -> dict:
        """Check if Emby is configured."""
        if not self.configured:
            return {
                'success': False,
                'error': 'Emby not configured',
                'hint': f'Create {MEDIA_CONFIG_FILE} with emby_server, emby_port, emby_api_key'
            }
        return None

    def get_sessions(self) -> List[dict]:
        """Get active Emby sessions."""
        if not self.configured:
            return []
        try:
            response = requests.get(
                f"{self.base_url}/../Sessions",
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[EMBY] Error getting sessions: {e}")
        return []

    def get_controllable_session(self) -> tuple:
        """Find a session that supports remote control."""
        sessions = self.get_sessions()
        for session in sessions:
            if session.get('SupportsRemoteControl', False):
                return session['Id'], session.get('DeviceName', 'Unknown')
        return None, None

    def get_user_id(self, prefer_user: str = None) -> Optional[str]:
        """Get user ID for API calls."""
        if not self.configured:
            return None
        try:
            response = requests.get(
                f"{self.base_url}/Users",
                headers=self.headers,
                timeout=10
            )
            if response.status_code != 200:
                return None
            users = response.json()

            if prefer_user:
                for user in users:
                    if user.get('Name', '').lower() == prefer_user.lower():
                        return user['Id']

            return users[0]['Id'] if users else None
        except Exception:
            return None

    def search(self, query: str, media_type: str = None, limit: int = 10) -> List[dict]:
        """Search Emby library."""
        err = self._check_configured()
        if err:
            return []

        user_id = self.get_user_id()
        if not user_id:
            return []

        try:
            url = f"{self.base_url}/Users/{user_id}/Items"
            params = {
                'SearchTerm': query,
                'Recursive': 'true',
                'Limit': limit,
                'Fields': 'PrimaryImageAspectRatio,Overview',
                'api_key': self.api_key
            }
            if media_type:
                params['IncludeItemTypes'] = media_type

            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json().get('Items', [])
        except Exception as e:
            print(f"[EMBY] Search error: {e}")
        return []

    def play(self, item_id: str) -> dict:
        """Play an item by ID."""
        err = self._check_configured()
        if err:
            return err

        session_id, device = self.get_controllable_session()
        if not session_id:
            return {'success': False, 'error': 'No controllable Emby session found'}

        try:
            url = f"{self.base_url}/../Sessions/{session_id}/Playing"
            data = {'ItemIds': item_id, 'PlayCommand': 'PlayNow'}
            response = requests.post(url, headers=self.headers, json=data, timeout=10)

            if response.status_code == 204:
                return {'success': True, 'message': f'Playing on {device}'}
            return {'success': False, 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def control(self, command: str) -> dict:
        """Control playback: Pause, Unpause, Stop, NextTrack, PreviousTrack."""
        err = self._check_configured()
        if err:
            return err

        session_id, device = self.get_controllable_session()
        if not session_id:
            return {'success': False, 'error': 'No controllable session'}

        try:
            url = f"{self.base_url}/../Sessions/{session_id}/Playing/{command}"
            response = requests.post(url, headers=self.headers, timeout=10)

            if response.status_code == 204:
                return {'success': True, 'message': f'{command} on {device}'}
            return {'success': False, 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def now_playing(self) -> str:
        """Get what's currently playing."""
        if not self.configured:
            return "Emby not configured"

        sessions = self.get_sessions()
        for session in sessions:
            if session.get('NowPlayingItem'):
                item = session['NowPlayingItem']
                name = item.get('Name', 'Unknown')
                item_type = item.get('Type', '')
                artist = item.get('Artists', [''])[0] if item.get('Artists') else ''
                is_paused = session.get('PlayState', {}).get('IsPaused', False)
                status = "Paused" if is_paused else "Playing"

                if artist:
                    return f"{status}: {artist} - {name}"
                return f"{status}: {name} ({item_type})"
        return "Nothing playing"

    def search_and_play(self, query: str, media_type: str = "Audio") -> dict:
        """Search and play first result."""
        err = self._check_configured()
        if err:
            return err

        results = self.search(query, media_type)
        if not results:
            return {'success': False, 'error': f"No results for '{query}'"}

        item = results[0]
        item_id = item['Id']
        name = item.get('Name', 'Unknown')
        artist = item.get('Artists', [''])[0] if item.get('Artists') else ''

        result = self.play(item_id)
        if result['success']:
            if artist:
                result['playing'] = f"{artist} - {name}"
            else:
                result['playing'] = name
        return result

    def list_playlists(self, limit: int = 50) -> List[dict]:
        """List available playlists."""
        if not self.configured:
            return []

        user_id = self.get_user_id()
        if not user_id:
            return []

        try:
            url = f"{self.base_url}/Users/{user_id}/Items"
            params = {
                'IncludeItemTypes': 'Playlist',
                'Recursive': 'true',
                'Limit': limit,
                'SortBy': 'SortName',
                'api_key': self.api_key
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                items = response.json().get('Items', [])
                return [{'name': i.get('Name'), 'id': i['Id'], 'count': i.get('ChildCount', 0)} for i in items]
        except Exception as e:
            print(f"[EMBY] List playlists error: {e}")
        return []

    def pause(self) -> dict:
        """Pause playback."""
        return self.control('Pause')

    def resume(self) -> dict:
        """Resume playback."""
        return self.control('Unpause')

    def stop(self) -> dict:
        """Stop playback."""
        return self.control('Stop')

    def next_track(self) -> dict:
        """Skip to next track."""
        return self.control('NextTrack')

    def prev_track(self) -> dict:
        """Go to previous track."""
        return self.control('PreviousTrack')


# Global instance
emby = EmbyControl()


# CLI-friendly functions
def play(query: str) -> str:
    """Search and play media."""
    result = emby.search_and_play(query)
    if result['success']:
        return f"[+] Playing: {result.get('playing', 'Unknown')}"
    return f"[!] {result['error']}"


def pause() -> str:
    """Pause playback."""
    result = emby.pause()
    return f"[+] Paused" if result['success'] else f"[!] {result['error']}"


def now() -> str:
    """Get now playing."""
    return emby.now_playing()


# Module test
if __name__ == "__main__":
    print("=" * 50)
    print("  C.O.R.A Media Module Test")
    print("  Unity AI Lab")
    print("=" * 50)

    config = load_media_config()
    if config.get('emby_server'):
        print(f"[+] Emby server: {config['emby_server']}:{config.get('emby_port', '8096')}")
        print(f"[+] Now playing: {emby.now_playing()}")

        playlists = emby.list_playlists()[:5]
        if playlists:
            print(f"[+] Playlists: {len(playlists)}")
            for p in playlists:
                print(f"    - {p['name']} ({p['count']} tracks)")
    else:
        print(f"[!] Emby not configured")
        print(f"    Create {MEDIA_CONFIG_FILE} with:")
        print('    {"emby_server": "IP", "emby_port": "8096", "emby_api_key": "KEY"}')
