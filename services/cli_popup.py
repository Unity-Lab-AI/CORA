#!/usr/bin/env python3
"""
C.O.R.A CLI Popup Service
Opens a terminal window where CORA can speak and type to the user in real-time.
Can be triggered on demand from anywhere in the application.
"""

import subprocess
import sys
import os
import threading
import queue
import time
from typing import Optional, Callable
from pathlib import Path

# Message queue for cross-thread communication
_message_queue = queue.Queue()
_cli_process: Optional[subprocess.Popen] = None
_cli_thread: Optional[threading.Thread] = None
_running = False

# Get the project root
PROJECT_ROOT = Path(__file__).parent.parent


def get_cli_script_path() -> Path:
    """Get path to the CLI runner script."""
    return PROJECT_ROOT / "services" / "_cli_runner.py"


def create_cli_runner_script():
    """Create the CLI runner script that runs in the popup terminal."""
    script_path = get_cli_script_path()
    script_content = '''#!/usr/bin/env python3
"""
C.O.R.A CLI Runner - Runs inside the popup terminal window
Receives messages from the main CORA process and displays them.
"""
import sys
import os
import time
import json
import socket
import threading
import msvcrt  # Windows-specific for non-blocking input

# ANSI color codes
CYAN = "\\033[96m"
GREEN = "\\033[92m"
YELLOW = "\\033[93m"
MAGENTA = "\\033[95m"
WHITE = "\\033[97m"
RESET = "\\033[0m"
BOLD = "\\033[1m"

# Socket server for receiving messages
HOST = '127.0.0.1'
PORT = 52849  # CORA port

def print_header():
    """Print the CLI header."""
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{CYAN}{BOLD}")
    print("=" * 60)
    print("  C.O.R.A - Cognitive Operations & Reasoning Assistant")
    print("  Direct Communication Terminal")
    print("=" * 60)
    print(f"{RESET}")
    print(f"{YELLOW}Listening for CORA...{RESET}")
    print(f"{YELLOW}Type 'exit' or 'quit' to close this window{RESET}")
    print("-" * 60)
    print()

def print_cora_message(message: str, emotion: str = "neutral"):
    """Print a message from CORA with styling."""
    emotion_colors = {
        "happy": GREEN,
        "excited": MAGENTA,
        "neutral": CYAN,
        "thinking": YELLOW,
        "sad": WHITE,
    }
    color = emotion_colors.get(emotion, CYAN)
    timestamp = time.strftime("%H:%M:%S")
    print(f"{color}[{timestamp}] CORA:{RESET} {message}")

def print_user_input(message: str):
    """Print user input with styling."""
    timestamp = time.strftime("%H:%M:%S")
    print(f"{GREEN}[{timestamp}] You:{RESET} {message}")

def socket_listener(stop_event):
    """Listen for messages from the main CORA process."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.settimeout(1.0)  # Allow checking stop_event

    try:
        server.bind((HOST, PORT))
        server.listen(1)

        while not stop_event.is_set():
            try:
                conn, addr = server.accept()
                conn.settimeout(0.5)

                while not stop_event.is_set():
                    try:
                        data = conn.recv(4096)
                        if not data:
                            break

                        # Parse message
                        try:
                            msg = json.loads(data.decode('utf-8'))
                            if msg.get('type') == 'message':
                                print_cora_message(msg.get('text', ''), msg.get('emotion', 'neutral'))
                            elif msg.get('type') == 'close':
                                print(f"\\n{YELLOW}CORA closed this terminal.{RESET}")
                                stop_event.set()
                                break
                        except json.JSONDecodeError:
                            # Plain text message
                            print_cora_message(data.decode('utf-8'))
                    except socket.timeout:
                        continue
                    except Exception:
                        break

                conn.close()
            except socket.timeout:
                continue
            except Exception:
                continue

    except OSError as e:
        print(f"{YELLOW}Note: Socket error (port may be in use): {e}{RESET}")
    finally:
        server.close()

def main():
    """Main CLI runner loop."""
    print_header()

    stop_event = threading.Event()

    # Start socket listener in background
    listener = threading.Thread(target=socket_listener, args=(stop_event,), daemon=True)
    listener.start()

    # Main input loop
    try:
        while not stop_event.is_set():
            try:
                user_input = input(f"{GREEN}> {RESET}").strip()

                if user_input.lower() in ('exit', 'quit', 'q'):
                    print(f"\\n{CYAN}Closing CORA terminal...{RESET}")
                    break
                elif user_input:
                    # Echo user input (the message is sent back to main CORA if needed)
                    # For now, just acknowledge
                    pass

            except EOFError:
                break
            except KeyboardInterrupt:
                print(f"\\n{CYAN}Interrupted. Closing...{RESET}")
                break

    finally:
        stop_event.set()
        print(f"\\n{CYAN}Terminal closed.{RESET}")
        time.sleep(0.5)

if __name__ == "__main__":
    main()
'''

    script_path.write_text(script_content, encoding='utf-8')
    return script_path


def open_cli_popup(title: str = "C.O.R.A Terminal") -> bool:
    """
    Open a new terminal window for CORA to communicate with the user.

    Args:
        title: Window title for the terminal

    Returns:
        True if successfully opened, False otherwise
    """
    global _cli_process, _running

    if _running and _cli_process and _cli_process.poll() is None:
        # Already running
        return True

    # Create the runner script if needed
    script_path = create_cli_runner_script()

    try:
        if sys.platform == 'win32':
            # Windows: Use start cmd with new window
            _cli_process = subprocess.Popen(
                f'start "{title}" cmd /k python "{script_path}"',
                shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        elif sys.platform == 'darwin':
            # macOS: Use osascript to open Terminal
            apple_script = f'''
            tell application "Terminal"
                do script "python3 '{script_path}'"
                activate
            end tell
            '''
            _cli_process = subprocess.Popen(['osascript', '-e', apple_script])
        else:
            # Linux: Try common terminals
            terminals = [
                ['gnome-terminal', '--', 'python3', str(script_path)],
                ['konsole', '-e', 'python3', str(script_path)],
                ['xfce4-terminal', '-e', f'python3 {script_path}'],
                ['xterm', '-e', f'python3 {script_path}'],
            ]

            for term_cmd in terminals:
                try:
                    _cli_process = subprocess.Popen(term_cmd)
                    break
                except FileNotFoundError:
                    continue
            else:
                print("No supported terminal found")
                return False

        _running = True
        time.sleep(0.5)  # Give terminal time to start
        return True

    except Exception as e:
        print(f"Failed to open CLI popup: {e}")
        return False


def send_to_cli(message: str, emotion: str = "neutral") -> bool:
    """
    Send a message to the CLI popup window.

    Args:
        message: Text to display in the CLI
        emotion: Emotion for styling (happy, excited, neutral, thinking, sad)

    Returns:
        True if sent successfully, False otherwise
    """
    import socket
    import json

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        sock.connect(('127.0.0.1', 52849))

        msg = json.dumps({
            'type': 'message',
            'text': message,
            'emotion': emotion,
            'timestamp': time.time()
        })
        sock.send(msg.encode('utf-8'))
        sock.close()
        return True

    except (ConnectionRefusedError, socket.timeout, OSError):
        # CLI not running or not ready
        return False


def close_cli_popup() -> bool:
    """
    Close the CLI popup window.

    Returns:
        True if closed successfully, False otherwise
    """
    global _cli_process, _running

    # Try to send close message first
    try:
        import socket
        import json
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        sock.connect(('127.0.0.1', 52849))
        sock.send(json.dumps({'type': 'close'}).encode('utf-8'))
        sock.close()
    except:
        pass

    # Force kill if still running
    if _cli_process:
        try:
            _cli_process.terminate()
        except:
            pass
        _cli_process = None

    _running = False
    return True


def is_cli_open() -> bool:
    """Check if CLI popup is currently open."""
    global _cli_process, _running

    if not _running:
        return False

    if _cli_process and _cli_process.poll() is not None:
        _running = False
        return False

    # Also check if socket is listening
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex(('127.0.0.1', 52849))
        sock.close()
        return result == 0
    except:
        return False


def speak_in_cli(message: str, emotion: str = "neutral", also_tts: bool = True):
    """
    Display message in CLI and optionally speak it with TTS.

    Args:
        message: Text to display and speak
        emotion: Emotion for styling and TTS
        also_tts: Whether to also speak the message via TTS
    """
    # Open CLI if not already open
    if not is_cli_open():
        open_cli_popup()
        time.sleep(1.0)  # Wait for window to open

    # Send to CLI
    send_to_cli(message, emotion)

    # TTS if enabled
    if also_tts:
        try:
            from voice.tts import speak_async
            speak_async(message)
        except ImportError:
            pass  # TTS not available


# Convenience function for cora.py integration
def cli_say(message: str, emotion: str = "neutral"):
    """
    Quick function for CORA to say something in the CLI popup.
    Opens the popup if not already open.
    """
    speak_in_cli(message, emotion, also_tts=True)


def cli_type(message: str, emotion: str = "neutral"):
    """
    Quick function for CORA to type something in the CLI popup without TTS.
    Opens the popup if not already open.
    """
    speak_in_cli(message, emotion, also_tts=False)


# Test function
if __name__ == "__main__":
    print("Testing CLI Popup...")

    if open_cli_popup():
        print("CLI opened successfully!")
        time.sleep(2)

        # Send test messages
        send_to_cli("Hello! This is CORA speaking through the CLI popup.", "happy")
        time.sleep(1)
        send_to_cli("I can display messages in real-time here.", "neutral")
        time.sleep(1)
        send_to_cli("This terminal stays open for direct communication.", "thinking")

        print("Messages sent. CLI will stay open until user closes it.")
    else:
        print("Failed to open CLI")
