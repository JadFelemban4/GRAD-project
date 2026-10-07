"""Launch the built learning environment; supervise only the process we create."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser

HERE = Path(__file__).resolve().parent
URL = 'http://127.0.0.1:8765'

def healthy():
    try:
        with urllib.request.urlopen(URL + '/api/meta', timeout=1) as response:
            meta = json.load(response)
        with urllib.request.urlopen(URL, timeout=1) as response:
            page = response.read(8192).decode('utf-8')
        return meta.get('bridge', {}).get('simulation_only') and '<div id="root"></div>' in page and ('مختبر السوبرا' in page or 'Supra Lab' in page)
    except (OSError, ValueError, urllib.error.URLError):
        return False

def main():
    parser = argparse.ArgumentParser(description='Open the local Supra learning lab')
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--check', action='store_true', help='Verify an already-running local app, then exit')
    args = parser.parse_args()
    if args.check:
        print('Local app healthy' if healthy() else 'Local app is not running with its built frontend')
        return 0 if healthy() else 1
    if not (HERE / 'dist' / 'index.html').is_file():
        print(f'Build the frontend first: cd "{HERE}"; npm ci; npm run build', file=sys.stderr)
        return 1
    child = None
    try:
        if not healthy():
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
            child = subprocess.Popen([sys.executable, '-m', 'backend.server'], cwd=HERE, env=env)
            for _ in range(100):
                if child.poll() is not None:
                    print('The bridge exited. Check that port 8765 is free and Python dependencies are installed.', file=sys.stderr)
                    return 1
                if healthy():
                    break
                time.sleep(.2)
            else:
                print('The bridge did not become healthy. Read the messages above.', file=sys.stderr)
                return 1
        print(f'Supra Lab is ready: {URL}\nKeep this terminal open. Ctrl+C stops the server started by this launcher.')
        if not args.no_browser:
            webbrowser.open(URL)
        if child:
            child.wait()
        return 0
    except KeyboardInterrupt:
        return 0
    finally:
        if child and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()

if __name__ == '__main__':
    raise SystemExit(main())
