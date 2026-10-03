import json
import os
from pathlib import Path
import subprocess

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
environment = os.environ.copy()
environment['BROWSER_SCENARIO_FILE'] = str(workspace / 'tmp/dashboard-browser-freshness-scenario.json')
arguments = ['C:/Program Files/nodejs/node.exe', 'test/fixtures/browser-server.cjs']
with (evidence / 'browser.stdout.txt').open('wb') as stdout, (evidence / 'browser.stderr.txt').open('wb') as stderr:
    process = subprocess.run(arguments, cwd=workspace / 'tmp/fsn-stats-auth', env=environment,
                             stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                             creationflags=subprocess.CREATE_NO_WINDOW)
(evidence / 'browser-process.json').write_text(json.dumps({'arguments': arguments, 'exit': process.returncode}) + '\n', encoding='utf-8')
