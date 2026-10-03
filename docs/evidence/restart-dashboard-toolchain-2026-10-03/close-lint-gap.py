import json
import subprocess
import urllib.request
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
frontend = root / 'tmp/fsn-stats-auth/react-frontend'
manifest = json.loads((frontend / 'package.json').read_text(encoding='utf-8'))
registry = json.loads((bundle / 'registry.json').read_text(encoding='utf-8'))
with urllib.request.urlopen('https://registry.npmjs.org/eslint/' + registry['eslint']['latest'], timeout=45) as response:
    eslint = json.load(response)
(bundle / 'eslint-current.json').write_text(json.dumps(eslint, indent=2) + '\n', encoding='utf-8')
manifest['devDependencies']['eslint'] = eslint['version']
manifest['devDependencies']['globals'] = registry['globals']['selected']['version']
manifest['scripts']['lint'] = 'oxlint src --max-warnings=0 && eslint src --max-warnings=0'
(frontend / 'package.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
(frontend / 'eslint.config.cjs').write_text('''const globals = require('globals');

module.exports = [
    {ignores: ['src/js/**']},
    {
        files: ['**/*.js', '**/*.jsx'],
        languageOptions: {
            sourceType: 'module',
            parserOptions: {ecmaFeatures: {jsx: true}},
            globals: {...globals.browser, ...globals.node, ...globals.jest}
        },
        rules: {'no-undef': 'error'}
    }
];
''', encoding='utf-8')
prefix = json.loads((bundle / 'install.json').read_text(encoding='utf-8'))['command'][:-4]
records = []
for label, args in [('lint-gap-resolution', ['install', '--package-lock-only', '--ignore-scripts', '--no-audit', '--no-fund']), ('lint-gap-install', ['ci', '--ignore-scripts', '--no-audit', '--no-fund']), ('lint-gap-audit', ['audit', '--json'])]:
    command = prefix + args
    with (bundle / (label + '.stdout.txt')).open('wb') as stdout, (bundle / (label + '.stderr.txt')).open('wb') as stderr:
        completed = subprocess.run(command, cwd=frontend, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=600, creationflags=subprocess.CREATE_NO_WINDOW)
    records.append({'name': label, 'command': command, 'exit': completed.returncode})
    print(label, completed.returncode, flush=True)
    assert completed.returncode == 0
(bundle / 'lint-gap-install.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
