import json
import os
import subprocess
import time
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
node = 'C:/Program Files/nodejs/node.exe'
control = root / 'tmp/dashboard-browser-pins-scenario.json'
environment = dict(os.environ, BROWSER_SCENARIO_FILE=str(control), NODE_PATH='C:/Users/Peter/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules')
control.write_text('{"mode":"ready","nodeId":"synthetic-alpha"}\n', encoding='utf-8', newline='\n')
record = {'passed': False}
with (bundle / 'browser.stdout.txt').open('wb') as stdout, (bundle / 'browser.stderr.txt').open('wb') as stderr:
    server = subprocess.Popen([node, 'test/fixtures/browser-server.cjs'], cwd=dashboard, env=environment, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        deadline = time.monotonic() + 15
        while not (bundle / 'browser.stdout.txt').stat().st_size:
            assert server.poll() is None and time.monotonic() < deadline
            time.sleep(0.1)
        with (bundle / 'browser-check.stdout.txt').open('wb') as check_out, (bundle / 'browser-check.stderr.txt').open('wb') as check_err:
            result = subprocess.run([node, str(bundle / 'browser-check.cjs')], cwd=dashboard, env=environment, stdin=subprocess.DEVNULL, stdout=check_out, stderr=check_err, timeout=100, creationflags=subprocess.CREATE_NO_WINDOW)
        record['browser_exit'] = result.returncode
        assert result.returncode == 0
        record['passed'] = True
    finally:
        control.write_text('{"mode":"stop"}\n', encoding='utf-8', newline='\n')
        record['server_exit'] = server.wait(timeout=15)
        record['server_stopped'] = server.poll() is not None
        (bundle / 'browser-process.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(record))
