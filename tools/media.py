"""
# ================================================================
#   ____   ___   ____      _
#  / ___| / _ \ |  _ \    / \
# | |    | | | || |_) |  / _ \
# | |___ | |_| ||  _ <  / ___ \
#  \____| \___/ |_| \_\/_/   \_\
#
# C.O.R.A Media Control Module
# ================================================================
# Version: 2.5.0
# Unity AI Lab
# Website: https://www.unityailab.com
# GitHub: https://github.com/Unity-Lab-AI
# Contact: unityailabcontact@gmail.com
# Creators: Hackall360, Sponge, GFourteen
# ================================================================
#
# Media control with multiple backends:
# 1. System Media Keys - Control ANY playing app (Spotify, VLC, etc)
# 2. Local File Playback - Play MP3/MP4 files directly
# 3. YouTube Playback - Play YouTube URLs
# 4. Emby (optional) - Control Emby media server if configured
#
# ================================================================
"""

import os
import re
import subprocess
import webbrowser
from pathlib import Path
from typing import Optional, List, Dict, Any
import json

# ================================================================
# CONFIGURATION
# ================================================================

CONFIG_DIR = Path(__file__).parent.parent / 'config'
MEDIA_CONFIG_FILE = CONFIG_DIR / 'media_config.json'

# Supported media extensions
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac', '.wma'}
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm'}
MEDIA_EXTENSIONS = AUDIO_EXTENSIONS | VIDEO_EXTENSIONS


def load_media_config() -> dict:
    """Load media configuration."""
    default_config = {
        'default_backend': 'system',  # system, local, emby
        'youtube_method': 'browser',  # browser, mpv, vlc
        'local_player': 'default',    # default, mpv, vlc
        'emby_server': '',
        'emby_port': '8096',
        'emby_api_key': ''
    }

    if MEDIA_CONFIG_FILE.exists():
        try:
            with open(MEDIA_CONFIG_FILE, 'r') as f:
                config = json.load(f)
                default_config.update(config)
        except Exception:
            pass

    return default_config


# ================================================================
# SYSTEM MEDIA KEYS - Control ANY playing app
# ================================================================

class SystemMediaControl:
    """
    Control system media playback using keyboard media keys.
    Works with Spotify, VLC, YouTube in browser, Windows Media Player, etc.
    """

    def __init__(self):
        self.available = False
        self._init_backend()

    def _init_backend(self):
        """Initialize the best available backend for media keys."""
        # Try pycaw for Windows audio control
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            self.available = True
            self._backend = 'pycaw'
            return
        except ImportError:
            pass

        # Fallback: use keyboard simulation
        try:
            import keyboard
            self.available = True
            self._backend = 'keyboard'
            return
        except ImportError:
            pass

        # Fallback: use pyautogui
        try:
            import pyautogui
            self.available = True
            self._backend = 'pyautogui'
            return
        except ImportError:
            pass

        # Final fallback: use ctypes directly for Windows
        try:
            import ctypes
            self.available = True
            self._backend = 'ctypes'
        except:
            self._backend = None

    def _send_media_key(self, key_code: int) -> bool:
        """Send a media key press using Windows API."""
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32

            # Virtual key codes for media keys
            VK_MEDIA_PLAY_PAUSE = 0xB3
            VK_MEDIA_NEXT_TRACK = 0xB0
            VK_MEDIA_PREV_TRACK = 0xB1
            VK_MEDIA_STOP = 0xB2
            VK_VOLUME_MUTE = 0xAD
            VK_VOLUME_DOWN = 0xAE
            VK_VOLUME_UP = 0xAF

            KEYEVENTF_EXTENDEDKEY = 0x0001
            KEYEVENTF_KEYUP = 0x0002

            # Key down
            user32.keybd_event(key_code, 0, KEYEVENTF_EXTENDEDKEY, 0)
            # Key up
            user32.keybd_event(key_code, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)

            return True
        except Exception as e:
            print(f"[MEDIA] Key send error: {e}")
            return False

    def play_pause(self) -> dict:
        """Toggle play/pause."""
        VK_MEDIA_PLAY_PAUSE = 0xB3
        success = self._send_media_key(VK_MEDIA_PLAY_PAUSE)
        return {'success': success, 'action': 'play_pause'}

    def play(self) -> dict:
        """Play (same as play_pause for most apps)."""
        return self.play_pause()

    def pause(self) -> dict:
        """Pause (same as play_pause for most apps)."""
        return self.play_pause()

    def stop(self) -> dict:
        """Stop playback."""
        VK_MEDIA_STOP = 0xB2
        success = self._send_media_key(VK_MEDIA_STOP)
        return {'success': success, 'action': 'stop'}

    def next_track(self) -> dict:
        """Skip to next track."""
        VK_MEDIA_NEXT_TRACK = 0xB0
        success = self._send_media_key(VK_MEDIA_NEXT_TRACK)
        return {'success': success, 'action': 'next'}

    def prev_track(self) -> dict:
        """Go to previous track."""
        VK_MEDIA_PREV_TRACK = 0xB1
        success = self._send_media_key(VK_MEDIA_PREV_TRACK)
        return {'success': success, 'action': 'previous'}

    def volume_up(self, steps: int = 2) -> dict:
        """Increase volume."""
        VK_VOLUME_UP = 0xAF
        for _ in range(steps):
            self._send_media_key(VK_VOLUME_UP)
        return {'success': True, 'action': 'volume_up', 'steps': steps}

    def volume_down(self, steps: int = 2) -> dict:
        """Decrease volume."""
        VK_VOLUME_DOWN = 0xAE
        for _ in range(steps):
            self._send_media_key(VK_VOLUME_DOWN)
        return {'success': True, 'action': 'volume_down', 'steps': steps}

    def mute(self) -> dict:
        """Toggle mute."""
        VK_VOLUME_MUTE = 0xAD
        success = self._send_media_key(VK_VOLUME_MUTE)
        return {'success': success, 'action': 'mute'}

    def set_volume(self, level: int) -> dict:
        """Set volume to specific level (0-100)."""
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))

            # Convert 0-100 to 0.0-1.0
            volume.SetMasterVolumeLevelScalar(level / 100.0, None)
            return {'success': True, 'action': 'set_volume', 'level': level}
        except ImportError:
            return {'success': False, 'error': 'pycaw not installed. Run: pip install pycaw'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_volume(self) -> int:
        """Get current volume level (0-100)."""
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))

            return int(volume.GetMasterVolumeLevelScalar() * 100)
        except:
            return -1


# ================================================================
# LOCAL FILE PLAYBACK
# ================================================================

class LocalMediaPlayer:
    """Play local media files (MP3, MP4, etc)."""

    def __init__(self, preferred_player: str = 'default'):
        """
        Args:
            preferred_player: 'default', 'mpv', 'vlc'
        """
        self.preferred_player = preferred_player
        self.current_process = None

    def _find_player(self) -> tuple:
        """Find available media player. Returns (player_path, player_name)."""
        # Check for mpv
        mpv_paths = [
            r'C:\Program Files\mpv\mpv.exe',
            r'C:\Program Files (x86)\mpv\mpv.exe',
            'mpv'  # In PATH
        ]
        for path in mpv_paths:
            if Path(path).exists() or self._is_in_path('mpv'):
                return (path if Path(path).exists() else 'mpv', 'mpv')

        # Check for VLC
        vlc_paths = [
            r'C:\Program Files\VideoLAN\VLC\vlc.exe',
            r'C:\Program Files (x86)\VideoLAN\VLC\vlc.exe',
            'vlc'
        ]
        for path in vlc_paths:
            if Path(path).exists() or self._is_in_path('vlc'):
                return (path if Path(path).exists() else 'vlc', 'vlc')

        # Fallback to system default
        return ('default', 'default')

    def _is_in_path(self, cmd: str) -> bool:
        """Check if command is in system PATH."""
        try:
            subprocess.run([cmd, '--version'], capture_output=True, timeout=5)
            return True
        except:
            return False

    def play(self, file_path: str) -> dict:
        """Play a local media file."""
        path = Path(file_path)

        if not path.exists():
            return {'success': False, 'error': f'File not found: {file_path}'}

        ext = path.suffix.lower()
        if ext not in MEDIA_EXTENSIONS:
            return {'success': False, 'error': f'Unsupported file type: {ext}'}

        try:
            if self.preferred_player == 'default':
                # Use system default player
                os.startfile(str(path))
                return {
                    'success': True,
                    'message': f'Opened with default player',
                    'file': path.name,
                    'type': 'audio' if ext in AUDIO_EXTENSIONS else 'video'
                }
            else:
                player_path, player_name = self._find_player()

                if player_name == 'default':
                    os.startfile(str(path))
                else:
                    self.current_process = subprocess.Popen(
                        [player_path, str(path)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )

                return {
                    'success': True,
                    'message': f'Playing with {player_name}',
                    'file': path.name,
                    'player': player_name
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def stop(self) -> dict:
        """Stop current playback (if we started it)."""
        if self.current_process:
            try:
                self.current_process.terminate()
                self.current_process = None
                return {'success': True, 'message': 'Stopped playback'}
            except:
                pass
        return {'success': False, 'error': 'No active playback to stop'}


# ================================================================
# YOUTUBE PLAYBACK
# ================================================================

class YouTubePlayer:
    """Play YouTube videos/audio."""

    # YouTube URL patterns
    YT_PATTERNS = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
    ]

    def __init__(self, method: str = 'browser'):
        """
        Args:
            method: 'browser', 'mpv', 'vlc', 'download'
        """
        self.method = method
        self.current_process = None

    def is_youtube_url(self, url: str) -> bool:
        """Check if URL is a YouTube link."""
        for pattern in self.YT_PATTERNS:
            if re.match(pattern, url):
                return True
        return False

    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL."""
        for pattern in self.YT_PATTERNS:
            match = re.match(pattern, url)
            if match:
                return match.group(1)
        return None

    def play(self, url: str, audio_only: bool = False) -> dict:
        """Play a YouTube video."""
        if not self.is_youtube_url(url):
            return {'success': False, 'error': 'Not a valid YouTube URL'}

        video_id = self.extract_video_id(url)
        clean_url = f'https://www.youtube.com/watch?v={video_id}'

        if self.method == 'browser':
            return self._play_in_browser(clean_url)
        elif self.method == 'mpv':
            return self._play_with_mpv(clean_url, audio_only)
        elif self.method == 'vlc':
            return self._play_with_vlc(clean_url)
        else:
            # Default to browser
            return self._play_in_browser(clean_url)

    def _play_in_browser(self, url: str) -> dict:
        """Open YouTube in default browser."""
        try:
            webbrowser.open(url)
            return {
                'success': True,
                'message': 'Opened in browser',
                'url': url,
                'method': 'browser'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _play_with_mpv(self, url: str, audio_only: bool = False) -> dict:
        """Play with mpv (requires mpv + yt-dlp installed)."""
        try:
            cmd = ['mpv']
            if audio_only:
                cmd.extend(['--no-video'])
            cmd.append(url)

            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            return {
                'success': True,
                'message': 'Playing with mpv',
                'url': url,
                'audio_only': audio_only
            }
        except FileNotFoundError:
            return {'success': False, 'error': 'mpv not found. Install mpv and yt-dlp'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _play_with_vlc(self, url: str) -> dict:
        """Play with VLC (requires VLC installed)."""
        vlc_paths = [
            r'C:\Program Files\VideoLAN\VLC\vlc.exe',
            r'C:\Program Files (x86)\VideoLAN\VLC\vlc.exe',
        ]

        vlc_path = None
        for path in vlc_paths:
            if Path(path).exists():
                vlc_path = path
                break

        if not vlc_path:
            return {'success': False, 'error': 'VLC not found'}

        try:
            self.current_process = subprocess.Popen(
                [vlc_path, url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return {
                'success': True,
                'message': 'Playing with VLC',
                'url': url
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def search_and_play(self, query: str, audio_only: bool = False) -> dict:
        """Search YouTube and play first result (requires yt-dlp)."""
        try:
            # Use yt-dlp to search
            result = subprocess.run(
                ['yt-dlp', '--get-id', f'ytsearch1:{query}'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and result.stdout.strip():
                video_id = result.stdout.strip()
                url = f'https://www.youtube.com/watch?v={video_id}'
                return self.play(url, audio_only)
            else:
                return {'success': False, 'error': f'No results for: {query}'}

        except FileNotFoundError:
            # Fallback: open YouTube search in browser
            search_url = f'https://www.youtube.com/results?search_query={query.replace(" ", "+")}'
            webbrowser.open(search_url)
            return {
                'success': True,
                'message': 'Opened YouTube search in browser (install yt-dlp for direct play)',
                'query': query
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}


# ================================================================
# EMBY MEDIA SERVER (Optional)
# ================================================================

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
            import requests
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

    def search(self, query: str, media_type: str = None, limit: int = 10) -> List[dict]:
        """Search Emby library."""
        err = self._check_configured()
        if err:
            return []

        try:
            import requests
            # Get user ID first
            resp = requests.get(f"{self.base_url}/Users", headers=self.headers, timeout=10)
            if resp.status_code != 200:
                return []
            users = resp.json()
            user_id = users[0]['Id'] if users else None
            if not user_id:
                return []

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
            import requests
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
            import requests
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

    def pause(self) -> dict:
        return self.control('Pause')

    def resume(self) -> dict:
        return self.control('Unpause')

    def stop(self) -> dict:
        return self.control('Stop')

    def next_track(self) -> dict:
        return self.control('NextTrack')

    def prev_track(self) -> dict:
        return self.control('PreviousTrack')


# ================================================================
# UNIFIED MEDIA CONTROLLER
# ================================================================

class MediaController:
    """
    Unified media controller - automatically routes to best backend.

    Priority:
    1. YouTube URLs -> YouTubePlayer
    2. Local files -> LocalMediaPlayer
    3. Emby queries (if configured) -> EmbyControl
    4. System media keys -> SystemMediaControl
    """

    def __init__(self, config: dict = None):
        if config is None:
            config = load_media_config()

        self.config = config
        self.system = SystemMediaControl()
        self.local = LocalMediaPlayer(config.get('local_player', 'default'))
        self.youtube = YouTubePlayer(config.get('youtube_method', 'browser'))
        self.emby = EmbyControl(config)

    def play(self, target: str = None) -> dict:
        """
        Smart play - figures out what to do based on input.

        - No target: Toggle play/pause on current app
        - YouTube URL: Open in browser/player
        - File path: Play local file
        - Search query: Search YouTube (or Emby if configured)
        """
        if not target:
            return self.system.play_pause()

        target = target.strip()

        # Check if it's a YouTube URL
        if self.youtube.is_youtube_url(target):
            return self.youtube.play(target)

        # Check if it's a local file
        if Path(target).exists():
            return self.local.play(target)

        # Check if it looks like a file path but doesn't exist
        if '\\' in target or '/' in target or target.endswith(tuple(MEDIA_EXTENSIONS)):
            return {'success': False, 'error': f'File not found: {target}'}

        # It's a search query - try Emby first if configured, then YouTube
        if self.emby.configured:
            results = self.emby.search(target)
            if results:
                item = results[0]
                result = self.emby.play(item['Id'])
                if result['success']:
                    result['source'] = 'emby'
                    result['title'] = item.get('Name', 'Unknown')
                    return result

        # Search YouTube
        return self.youtube.search_and_play(target)

    def pause(self) -> dict:
        """Pause playback."""
        # Try Emby first if configured
        if self.emby.configured:
            result = self.emby.pause()
            if result['success']:
                return result
        # Fall back to system media keys
        return self.system.pause()

    def resume(self) -> dict:
        """Resume playback."""
        return self.system.play_pause()

    def stop(self) -> dict:
        """Stop playback."""
        if self.emby.configured:
            result = self.emby.stop()
            if result['success']:
                return result
        return self.system.stop()

    def next_track(self) -> dict:
        """Next track."""
        if self.emby.configured:
            result = self.emby.next_track()
            if result['success']:
                return result
        return self.system.next_track()

    def prev_track(self) -> dict:
        """Previous track."""
        if self.emby.configured:
            result = self.emby.prev_track()
            if result['success']:
                return result
        return self.system.prev_track()

    def volume_up(self) -> dict:
        """Volume up."""
        return self.system.volume_up()

    def volume_down(self) -> dict:
        """Volume down."""
        return self.system.volume_down()

    def mute(self) -> dict:
        """Toggle mute."""
        return self.system.mute()

    def set_volume(self, level: int) -> dict:
        """Set volume to specific level (0-100)."""
        return self.system.set_volume(level)

    def get_volume(self) -> int:
        """Get current volume."""
        return self.system.get_volume()

    def now_playing(self) -> str:
        """Get what's playing (Emby only for now)."""
        if self.emby.configured:
            return self.emby.now_playing()
        return "Use Spotify/VLC/etc - check your player for now playing info"


# ================================================================
# GLOBAL INSTANCE & CONVENIENCE FUNCTIONS
# ================================================================

_media: MediaController = None


def get_media() -> MediaController:
    """Get or create global media controller."""
    global _media
    if _media is None:
        _media = MediaController()
    return _media


# CLI-friendly functions
def play(target: str = None) -> str:
    """Play media - URL, file, or search query."""
    result = get_media().play(target)
    if result['success']:
        msg = result.get('message', 'Playing')
        if result.get('title'):
            msg += f": {result['title']}"
        elif result.get('file'):
            msg += f": {result['file']}"
        return f"[+] {msg}"
    return f"[!] {result.get('error', 'Failed')}"


def pause() -> str:
    """Pause playback."""
    result = get_media().pause()
    return "[+] Paused" if result['success'] else f"[!] {result.get('error', 'Failed')}"


def resume() -> str:
    """Resume playback."""
    result = get_media().resume()
    return "[+] Resumed" if result['success'] else f"[!] {result.get('error', 'Failed')}"


def stop() -> str:
    """Stop playback."""
    result = get_media().stop()
    return "[+] Stopped" if result['success'] else f"[!] {result.get('error', 'Failed')}"


def next_track() -> str:
    """Next track."""
    result = get_media().next_track()
    return "[+] Next track" if result['success'] else f"[!] {result.get('error', 'Failed')}"


def prev_track() -> str:
    """Previous track."""
    result = get_media().prev_track()
    return "[+] Previous track" if result['success'] else f"[!] {result.get('error', 'Failed')}"


def volume(level: int = None) -> str:
    """Get or set volume."""
    media = get_media()
    if level is not None:
        result = media.set_volume(level)
        if result['success']:
            return f"[+] Volume set to {level}%"
        return f"[!] {result.get('error', 'Failed')}"
    else:
        vol = media.get_volume()
        return f"[+] Volume: {vol}%" if vol >= 0 else "[!] Couldn't get volume"


def mute() -> str:
    """Toggle mute."""
    result = get_media().mute()
    return "[+] Mute toggled" if result['success'] else f"[!] {result.get('error', 'Failed')}"


def now() -> str:
    """Get now playing."""
    return get_media().now_playing()


# ================================================================
# MODULE TEST
# ================================================================

if __name__ == "__main__":
    print("=" * 50)
    print("  C.O.R.A Media Module v2.5.0")
    print("  Unity AI Lab")
    print("=" * 50)
    print()

    config = load_media_config()
    media = MediaController(config)

    print("[System Media Keys]")
    print(f"  Available: {media.system.available}")
    print(f"  Backend: {media.system._backend}")
    print(f"  Volume: {media.get_volume()}%")
    print()

    print("[YouTube Player]")
    print(f"  Method: {config.get('youtube_method', 'browser')}")
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    print(f"  Is YT URL: {media.youtube.is_youtube_url(test_url)}")
    print()

    print("[Local Player]")
    print(f"  Preferred: {config.get('local_player', 'default')}")
    print()

    print("[Emby]")
    if media.emby.configured:
        print(f"  Server: {config.get('emby_server')}:{config.get('emby_port')}")
        print(f"  Now Playing: {media.emby.now_playing()}")
    else:
        print("  Not configured (optional)")
    print()

    print("[Commands]")
    print("  play()              - Toggle play/pause")
    print("  play('song.mp3')    - Play local file")
    print("  play('youtube.com/...')  - Play YouTube")
    print("  play('search query')     - Search & play")
    print("  pause(), resume(), stop()")
    print("  next_track(), prev_track()")
    print("  volume(50), mute()")
    print()
    print("=" * 50)
