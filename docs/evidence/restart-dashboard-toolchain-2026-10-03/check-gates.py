import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
frontend = root / 'tmp/fsn-stats-auth/react-frontend'
linux_root = '/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/'
wsl = ['wsl', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--']
node = linux_root + 'tmp/dashboard-runtime-review/v24.21.0/node'
base = {'REACT_APP_STATS_API_PATH': '/stats-api', 'REACT_APP_STATS_POLL_INTERVAL_MS': '250', 'REACT_APP_STATS_REQUEST_TIMEOUT_MS': '1000'}
cases = [
    ('valid-settings', {}, 0, ''),
    ('missing-path', {'REACT_APP_STATS_API_PATH': None}, 1, 'REACT_APP_STATS_API_PATH must be a same-origin path'),
    ('foreign-path', {'REACT_APP_STATS_API_PATH': 'https://example.invalid/nodes'}, 1, 'REACT_APP_STATS_API_PATH must be a same-origin path'),
    ('missing-poll', {'REACT_APP_STATS_POLL_INTERVAL_MS': None}, 1, 'REACT_APP_STATS_POLL_INTERVAL_MS must be a positive integer'),
    ('zero-timeout', {'REACT_APP_STATS_REQUEST_TIMEOUT_MS': '0'}, 1, 'REACT_APP_STATS_REQUEST_TIMEOUT_MS must be a positive integer'),
]
results = []
for label, changes, expected_exit, expected_text in cases:
    values = {**base, **changes}
    command = wsl + ['env'] + [arg for key in base for arg in ['-u', key]] + [key + '=' + value for key, value in values.items() if value is not None] + [node, '--input-type=module', '-e', "await import('./rsbuild.config.mjs')"]
    result = subprocess.run(command, cwd=frontend, stdin=subprocess.DEVNULL, capture_output=True, timeout=45, creationflags=subprocess.CREATE_NO_WINDOW)
    (bundle / (label + '.txt')).write_bytes(result.stdout + result.stderr)
    assert result.returncode == expected_exit and expected_text.encode() in result.stdout + result.stderr, label
    results.append({'name': label, 'exit': result.returncode, 'expected_exit': expected_exit, 'expected_text': expected_text})
fixtures = frontend / 'test'
fixtures.mkdir(exist_ok=True)
lint_cases = [
    ('valid.jsx', "import React from 'react'; export default function View() { return <img alt=\"node\" src=\"node.svg\" />; }\n", 0, ''),
    ('undefined.jsx', "export default missingNode;\n", 1, 'no-undef'),
    ('accessibility.jsx', "import React from 'react'; export default function View() { return <img src=\"node.svg\" />; }\n", 1, 'alt-text'),
    ('strict.jsx', "import React from 'react'; export default function View(a, a) { return <div />; }\n", 1, ''),
]
for name, source, expected_exit, expected_text in lint_cases:
    fixture = fixtures / ('toolchain-' + name)
    assert not fixture.exists()
    fixture.write_text(source, encoding='utf-8')
    fixture_results = []
    for tool, config in [('oxlint', '.oxlintrc.json'), ('eslint', 'eslint.config.cjs')]:
        binary = 'node_modules/oxlint/bin/oxlint' if tool == 'oxlint' else 'node_modules/eslint/bin/eslint.js'
        command = wsl + [node, binary, '--config', config, '--no-ignore', '--max-warnings=0', 'test/toolchain-' + name]
        result = subprocess.run(command, cwd=frontend, stdin=subprocess.DEVNULL, capture_output=True, timeout=45, creationflags=subprocess.CREATE_NO_WINDOW)
        fixture_results.append(result)
    output = b'\n'.join(r.stdout + r.stderr for r in fixture_results)
    fixture.unlink()
    (bundle / ('lint-' + name + '.txt')).write_bytes(output)
    exit_code = max(r.returncode for r in fixture_results)
    assert exit_code == expected_exit and expected_text.encode() in output, (name, output)
    results.append({'name': name, 'source': source, 'tool_exits': [r.returncode for r in fixture_results], 'exit': exit_code, 'expected_exit': expected_exit, 'expected_text': expected_text})
(bundle / 'gate-checks.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
print('Passed', len(results), 'build configuration and lint gate checks')
