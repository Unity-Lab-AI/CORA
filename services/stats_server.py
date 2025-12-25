#!/usr/bin/env python3
"""
C.O.R.A Stats Server
Local HTTP server that provides system stats AND setup commands to the web version.
Runs on localhost:11435 (next to Ollama on 11434)

The web version calls this to:
- Get real GPU/CPU/RAM stats from the host machine
- Install Ollama models (ollama pull)
- Install Python requirements (pip install)
- Start Ollama service
"""

import json
import subprocess
import threading
import os
import shutil
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import psutil

# Port for stats server (Ollama is on 11434)
STATS_PORT = 11435


def get_gpu_stats():
    """Get NVIDIA GPU stats using nvidia-smi."""
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu',
             '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(', ')
            if len(parts) >= 5:
                return {
                    'name': parts[0],
                    'utilization': int(parts[1]),
                    'memory_used': int(parts[2]),
                    'memory_total': int(parts[3]),
                    'temperature': int(parts[4]),
                    'available': True
                }
    except Exception:
        pass
    return {'available': False}


def get_system_stats():
    """Get full system stats."""
    # CPU
    cpu_percent = psutil.cpu_percent(interval=0.1)

    # Memory
    mem = psutil.virtual_memory()

    # Disk
    disk = psutil.disk_usage('/')

    # GPU
    gpu = get_gpu_stats()

    return {
        'cpu': {
            'percent': cpu_percent,
            'cores': psutil.cpu_count()
        },
        'memory': {
            'percent': mem.percent,
            'used_gb': round(mem.used / (1024**3), 1),
            'total_gb': round(mem.total / (1024**3), 1)
        },
        'disk': {
            'percent': disk.percent,
            'used_gb': round(disk.used / (1024**3), 1),
            'total_gb': round(disk.total / (1024**3), 1)
        },
        'gpu': gpu,
        'network': {
            'connected': True  # If we can respond, we're connected
        }
    }


# =============================================================================
# SETUP FUNCTIONS - Same logic as CORA.bat
# =============================================================================

def find_ollama():
    """Find Ollama executable."""
    # Check PATH first
    ollama_path = shutil.which('ollama')
    if ollama_path:
        return ollama_path

    # Check common locations (Windows)
    locations = [
        os.path.expandvars(r'%LOCALAPPDATA%\Programs\Ollama\ollama.exe'),
        os.path.expandvars(r'%ProgramFiles%\Ollama\ollama.exe'),
        os.path.expandvars(r'%ProgramFiles(x86)%\Ollama\ollama.exe'),
        os.path.expandvars(r'%USERPROFILE%\Ollama\ollama.exe'),
    ]
    for loc in locations:
        if os.path.exists(loc):
            return loc
    return None


def check_ollama_running():
    """Check if Ollama service is running."""
    try:
        import urllib.request
        req = urllib.request.urlopen('http://localhost:11434/api/tags', timeout=3)
        return req.status == 200
    except:
        return False


def get_ollama_models():
    """Get list of installed Ollama models."""
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            models = []
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if parts:
                        models.append(parts[0])
            return models
    except:
        pass
    return []


def pull_ollama_model(model_name):
    """Pull an Ollama model. Returns (success, output)."""
    try:
        print(f"[SETUP] Pulling model: {model_name}")
        result = subprocess.run(
            ['ollama', 'pull', model_name],
            capture_output=True, text=True, timeout=600  # 10 min timeout for large models
        )
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    except subprocess.TimeoutExpired:
        return False, "Timeout - model download took too long"
    except Exception as e:
        return False, str(e)


def start_ollama_service():
    """Start Ollama service."""
    ollama_exe = find_ollama()
    if not ollama_exe:
        return False, "Ollama not found"

    try:
        # Start in background (Windows: start /min, Unix: nohup)
        if os.name == 'nt':
            subprocess.Popen(
                [ollama_exe, 'serve'],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            subprocess.Popen(
                [ollama_exe, 'serve'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
        return True, "Ollama service started"
    except Exception as e:
        return False, str(e)


def install_requirements():
    """Install Python requirements."""
    try:
        # Find requirements.txt relative to this file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        req_file = os.path.join(project_root, 'requirements.txt')

        if not os.path.exists(req_file):
            # Try config folder
            req_file = os.path.join(project_root, 'config', 'requirements.txt')

        if not os.path.exists(req_file):
            return False, "requirements.txt not found"

        print(f"[SETUP] Installing from: {req_file}")
        result = subprocess.run(
            ['pip', 'install', '-r', req_file],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode == 0:
            return True, "Requirements installed"
        else:
            return False, result.stderr
    except Exception as e:
        return False, str(e)


def get_setup_status():
    """Get full setup status."""
    ollama_exe = find_ollama()
    ollama_running = check_ollama_running()
    models = get_ollama_models() if ollama_running else []

    required_models = ['dolphin-mistral', 'llava', 'qwen2.5-coder']
    model_status = {}
    for req in required_models:
        model_status[req] = any(req in m for m in models)

    return {
        'ollama_installed': ollama_exe is not None,
        'ollama_path': ollama_exe,
        'ollama_running': ollama_running,
        'models_installed': models,
        'required_models': model_status,
        'all_models_ready': all(model_status.values())
    }


class StatsHandler(BaseHTTPRequestHandler):
    """HTTP request handler for stats endpoint."""

    def log_message(self, format, *args):
        """Suppress logging."""
        pass

    def send_json(self, data, status=200):
        """Send JSON response with CORS headers."""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path

        if path == '/stats' or path == '/':
            self.send_json(get_system_stats())
        elif path == '/gpu':
            self.send_json(get_gpu_stats())
        elif path == '/ping':
            self.send_json({'status': 'ok', 'service': 'cora-stats'})
        elif path == '/setup/status':
            self.send_json(get_setup_status())
        elif path == '/setup/models':
            self.send_json({'models': get_ollama_models()})
        else:
            self.send_json({'error': 'unknown endpoint'}, 404)

    def do_POST(self):
        """Handle POST requests for setup commands."""
        parsed = urlparse(self.path)
        path = parsed.path

        # Read POST body if any
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode() if content_length > 0 else ''

        if path == '/setup/start-ollama':
            success, msg = start_ollama_service()
            self.send_json({'success': success, 'message': msg})

        elif path == '/setup/install-requirements':
            success, msg = install_requirements()
            self.send_json({'success': success, 'message': msg})

        elif path.startswith('/setup/pull-model/'):
            model_name = path.replace('/setup/pull-model/', '')
            if not model_name:
                self.send_json({'success': False, 'message': 'No model specified'}, 400)
            else:
                success, msg = pull_ollama_model(model_name)
                self.send_json({'success': success, 'message': msg})

        elif path == '/setup/pull-all':
            # Pull all required models
            results = {}
            for model in ['dolphin-mistral:7b', 'llava', 'qwen2.5-coder:7b']:
                success, msg = pull_ollama_model(model)
                results[model] = {'success': success, 'message': msg}
            all_success = all(r['success'] for r in results.values())
            self.send_json({'success': all_success, 'results': results})

        else:
            self.send_json({'error': 'unknown endpoint'}, 404)

    def do_OPTIONS(self):
        """Handle preflight CORS requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()


def start_server(port=STATS_PORT):
    """Start the stats server."""
    server = HTTPServer(('127.0.0.1', port), StatsHandler)
    print(f"[STATS] Server running on http://localhost:{port}")
    print(f"[STATS] Endpoints:")
    print(f"  GET  /stats              - System stats (CPU, RAM, GPU)")
    print(f"  GET  /setup/status       - Setup status (Ollama, models)")
    print(f"  POST /setup/start-ollama - Start Ollama service")
    print(f"  POST /setup/pull-model/X - Pull Ollama model")
    print(f"  POST /setup/pull-all     - Pull all required models")
    print(f"  POST /setup/install-requirements - Install Python deps")
    server.serve_forever()


def start_server_background(port=STATS_PORT):
    """Start the stats server in a background thread."""
    thread = threading.Thread(target=start_server, args=(port,), daemon=True)
    thread.start()
    return thread


if __name__ == "__main__":
    print("C.O.R.A Stats Server")
    print("=" * 40)
    print(f"Starting on port {STATS_PORT}...")
    print("Press Ctrl+C to stop")
    print()

    # Print initial stats
    stats = get_system_stats()
    print(f"CPU: {stats['cpu']['percent']}%")
    print(f"RAM: {stats['memory']['percent']}%")
    print(f"Disk: {stats['disk']['percent']}%")
    if stats['gpu']['available']:
        print(f"GPU: {stats['gpu']['name']} - {stats['gpu']['utilization']}% ({stats['gpu']['temperature']}°C)")
    else:
        print("GPU: Not available")
    print()

    start_server()
