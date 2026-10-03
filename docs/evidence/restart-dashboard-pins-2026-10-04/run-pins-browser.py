import json
import os
import subprocess
import sys
import time
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
assert sys.argv[1] in ['baseline', 'final']
output = bundle / ('pins-' + sys.argv[1] + ('-' + sys.argv[2] if len(sys.argv) > 2 else ''))
output.mkdir(exist_ok=False)
control = root / 'tmp/dashboard-browser-pins-preferences.json'
control.write_text('{"mode":"ready","nodeId":"synthetic-alpha"}\n', encoding='utf-8', newline='\n')
environment = dict(os.environ, BROWSER_SCENARIO_FILE=str(control), NODE_PATH='C:/Users/Peter/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules')
node = 'C:/Program Files/nodejs/node.exe'
record = {'passed': False}
with (output / 'server.stdout.txt').open('wb') as stdout, (output / 'server.stderr.txt').open('wb') as stderr:
    server = subprocess.Popen([node, 'test/fixtures/browser-server.cjs'], cwd=dashboard, env=environment, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        deadline = time.monotonic() + 15
        while not (output / 'server.stdout.txt').stat().st_size:
            assert server.poll() is None and time.monotonic() < deadline
            time.sleep(0.1)
        with (output / 'browser.stdout.txt').open('wb') as check_out, (output / 'browser.stderr.txt').open('wb') as check_err:
            result = subprocess.run([node, str(bundle / 'pins-browser.cjs'), sys.argv[1], output.name], cwd=dashboard, env=environment, stdin=subprocess.DEVNULL, stdout=check_out, stderr=check_err, timeout=100, creationflags=subprocess.CREATE_NO_WINDOW)
        record['browser_exit'] = result.returncode
        assert result.returncode == 0
        record['passed'] = True
    finally:
        control.write_text('{"mode":"stop"}\n', encoding='utf-8', newline='\n')
        record['server_exit'] = server.wait(timeout=15)
        record['server_stopped'] = server.poll() is not None
        (output / 'process.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(record))
