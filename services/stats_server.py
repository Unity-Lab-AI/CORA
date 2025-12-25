#!/usr/bin/env python3
"""
C.O.R.A Stats Server
Local HTTP server that provides system stats to the web version.
Runs on localhost:11435 (next to Ollama on 11434)

The web version calls this to get real GPU/CPU/RAM stats from the host machine.
"""

import json
import subprocess
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
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


class StatsHandler(BaseHTTPRequestHandler):
    """HTTP request handler for stats endpoint."""

    def log_message(self, format, *args):
        """Suppress logging."""
        pass

    def do_GET(self):
        """Handle GET requests."""
        # CORS headers for browser access
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

        if self.path == '/stats' or self.path == '/':
            stats = get_system_stats()
            self.wfile.write(json.dumps(stats).encode())
        elif self.path == '/gpu':
            gpu = get_gpu_stats()
            self.wfile.write(json.dumps(gpu).encode())
        elif self.path == '/ping':
            self.wfile.write(b'{"status": "ok", "service": "cora-stats"}')
        else:
            self.wfile.write(b'{"error": "unknown endpoint"}')

    def do_OPTIONS(self):
        """Handle preflight CORS requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()


def start_server(port=STATS_PORT):
    """Start the stats server."""
    server = HTTPServer(('127.0.0.1', port), StatsHandler)
    print(f"[STATS] Server running on http://localhost:{port}")
    print(f"[STATS] Endpoints: /stats, /gpu, /ping")
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
