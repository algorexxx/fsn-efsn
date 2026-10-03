import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

bundle = Path(__file__).resolve().parent
node = 'C:/Program Files/nodejs/node.exe'
environment = {**os.environ, 'NODE_PATH': 'C:/Users/Peter/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules'}
subprocess.run([sys.executable, str(bundle / 'set-browser-scenario.py'), 'ready'], check=True, creationflags=subprocess.CREATE_NO_WINDOW)
server = subprocess.Popen([sys.executable, str(bundle / 'serve.py')], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
browser_exit = None
try:
    deadline = time.monotonic() + 10
    while not (bundle / 'browser.stdout.txt').exists() or not (bundle / 'browser.stdout.txt').read_bytes():
        if time.monotonic() > deadline or server.poll() is not None:
            raise RuntimeError('Browser fixture did not start')
        time.sleep(0.1)
    with (bundle / 'browser-check.stdout.txt').open('wb') as output, (bundle / 'browser-check.stderr.txt').open('wb') as error:
        result = subprocess.run([node, str(bundle / 'browser-check.cjs')], env=environment, stdin=subprocess.DEVNULL, stdout=output, stderr=error, timeout=90, creationflags=subprocess.CREATE_NO_WINDOW)
    browser_exit = result.returncode
finally:
    subprocess.run([sys.executable, str(bundle / 'set-browser-scenario.py'), 'stop'], check=True, creationflags=subprocess.CREATE_NO_WINDOW)
    server_exit = server.wait(timeout=15)
started = json.loads((bundle / 'browser.stdout.txt').read_text(encoding='utf-8').splitlines()[0])
url = urlparse(started['url'])
with socket.socket() as probe:
    probe.settimeout(5)
    refusal = probe.connect_ex((url.hostname, url.port))
(bundle / 'browser-run.json').write_text(json.dumps({'browser_exit': browser_exit, 'server_exit': server_exit, 'listener_probe': refusal}, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'browser_exit': browser_exit, 'server_exit': server_exit, 'listener_probe': refusal}), flush=True)
sys.exit(0 if browser_exit == 0 and server_exit == 0 and refusal == 10061 else 1)
