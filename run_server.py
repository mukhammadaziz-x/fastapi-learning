#!/usr/bin/env python3
"""
FastAPI Development Server Launcher
Handles port conflicts and firewall issues
"""

import subprocess
import socket
import sys
import time

def is_port_available(port):
    """Check if port is available"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result != 0

def find_available_port(start_port=7000):
    """Find first available port starting from start_port"""
    for port in range(start_port, start_port + 1000):
        if is_port_available(port):
            return port
    return None

def main():
    print("=" * 60)
    print("FastAPI Development Server Launcher")
    print("=" * 60)

    # Find available port
    port = find_available_port(7000)

    if port is None:
        print("ERROR: Could not find any available port!")
        sys.exit(1)

    print(f"\nAvailable port found: {port}")
    print(f"\nStarting FastAPI server...")
    print(f"Documentation will be at: http://127.0.0.1:{port}/docs")
    print(f"\nPress Ctrl+C to stop the server\n")

    # Start server
    cmd = [
        sys.executable,
        "-m", "uvicorn",
        "app.main:app",
        "--host", "127.0.0.1",
        "--port", str(port),
        "--reload"
    ]

    try:
        subprocess.run(cmd, cwd=__file__.replace("run_server.py", ""))
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
        sys.exit(0)

if __name__ == "__main__":
    main()

