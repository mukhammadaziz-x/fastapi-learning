#!/usr/bin/env python3
"""
EduPlatform — Serverni ishga tushirish
Har doim shu faylni run qiling: python run_server.py
"""

import subprocess
import socket
import sys
import os

# Bo'sh port topish
def find_port(start=9000):
    for port in range(start, start + 100):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("0.0.0.0", port))
            s.close()
            return port
        except OSError:
            continue
    return None

def main():
    print("=" * 55)
    print("  EduPlatform — Educational Startup Server")
    print("=" * 55)

    port = find_port(9000)
    if not port:
        print("XATO: Bo'sh port topilmadi!")
        sys.exit(1)

    print(f"\n  Port: {port}")
    print(f"  API:  http://localhost:{port}")
    print(f"  Docs: http://localhost:{port}/docs")
    print(f"\n  To'xtatish: Ctrl+C\n")

    cmd = [
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", str(port),
        "--reload",
    ]

    try:
        subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
    except KeyboardInterrupt:
        print("\n\nServer to'xtatildi.")

if __name__ == "__main__":
    main()

