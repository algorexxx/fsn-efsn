import difflib
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stream(path):
    text = path.read_text(encoding='utf-8')
    decoder = json.JSONDecoder()
    offset = 0
    values = []
    while offset < len(text):
        if text[offset].isspace():
            offset += 1
            continue
        value, offset = decoder.raw_decode(text, offset)
        values.append(value)
    return values


def modules(path):
    return {parts[1]: parts[2:] for line in path.read_text(encoding='utf-8').splitlines()
            if (parts := line.split()) and parts[0] == 'dep'}


def build_settings(path):
    return dict(parts[1].split('=', 1) for line in path.read_text(encoding='utf-8').splitlines()
                if (parts := line.split()) and parts[0] == 'build' and '=' in parts[1])


evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
work = Path('/home/rehearsal/results/restart-release-text-2026-10-04')
base = Path('/home/rehearsal/results/restart-release-jwt-2026-10-04')
previous = evidence.parent / 'restart-release-jwt-2026-10-04'
assert (evidence / 'scans-finished.txt').exists()
assert (evidence / 'completion-finished.txt').exists()
inventories = {}
for name in ('node', 'recovery'):
    old = {p.relative_to(base / name).as_posix(): digest(p) for p in (base / name).rglob('*') if p.is_file()}
    assert old == json.loads((previous / (name + '-inventory.json')).read_text(encoding='utf-8'))
    new = {p.relative_to(work / name).as_posix(): digest(p) for p in (work / name).rglob('*') if p.is_file()}
    changed = sorted(p for p in old.keys() | new.keys() if old.get(p) != new.get(p))
    assert changed == ['go.mod', 'go.sum']
    inventories[name] = {'base_inventory_sha256': digest(previous / (name + '-inventory.json')),
                         'changed_files': {p: {'before': old[p], 'after': new[p]} for p in changed},
                         'unchanged_files': len(new) - 2}
for name in ('go.mod', 'go.sum'):
    assert (work / 'node' / name).read_bytes() == (work / 'recovery' / name).read_bytes()
    assert (workspace / name).read_bytes().replace(b'\r\n', b'\n') == (base / 'node' / name).read_bytes()
patch = ''.join(''.join(difflib.unified_diff((base / 'node' / name).read_text(encoding='utf-8').splitlines(True),
                                          (work / 'node' / name).read_text(encoding='utf-8').splitlines(True),
                                          fromfile='a/' + name, tofile='b/' + name)) for name in ('go.mod', 'go.sum'))
tests = {}
for file in sorted(evidence.glob('*-exit.txt')):
    label = file.name.removesuffix('-exit.txt')
    log = evidence / (label + '.txt')
    text = log.read_text(encoding='utf-8') if log.exists() else ''
    tests[label] = {'exit': int(file.read_text()), 'package_results': re.findall(r'^(?:ok|FAIL|\?)[ \t]+.*$', text, re.M),
                    'passed_top_level': re.findall(r'^--- PASS: (\S+)', text, re.M),
                    'skipped_top_level': re.findall(r'^--- SKIP: (\S+)', text, re.M),
                    'failed_top_level': re.findall(r'^--- FAIL: (\S+)', text, re.M)}
for name in ('console', 'eth-tracers-js'):
    assert (evidence / ('baseline-' + name + '.txt')).read_bytes() == (evidence / ('candidate-complete-' + name + '.txt')).read_bytes()
    assert tests['baseline-' + name]['exit'] == tests['candidate-complete-' + name]['exit'] == 1
for name in ('baseline-internal-jsre', 'candidate-internal-jsre', 'upstream-text-tests'):
    assert tests[name]['exit'] == 0 and tests[name]['passed_top_level']
linked = {}
settings = {}
scans = {}
imports = {}
binaries = {}
for name in ('efsn', 'fsn-recovery'):
    assert tests['build-complete-' + name]['exit'] == 0
    assert not (evidence / ('build-complete-' + name + '.txt')).read_bytes()
    old, new = modules(previous / ('build-info-' + name + '.txt')), modules(evidence / ('build-info-' + name + '.txt'))
    linked[name] = {p: {'before': old.get(p), 'after': new.get(p)} for p in old.keys() | new.keys() if old.get(p) != new.get(p)}
    old_settings = build_settings(previous / ('build-info-' + name + '.txt'))
    new_settings = build_settings(evidence / ('build-info-' + name + '.txt'))
    settings[name] = {p: {'before': old_settings.get(p), 'after': new_settings.get(p)}
                      for p in old_settings.keys() | new_settings.keys() if old_settings.get(p) != new_settings.get(p)}
    assert set(settings[name]) == {'DefaultGODEBUG'}
    binaries[name] = digest(work / 'bin' / name)
    assert binaries[name] == (evidence / ('binary-' + name + '.sha256')).read_text().split()[0]
    imports[name] = {p['ImportPath']: [i for i in p.get('Imports', []) if i.startswith(('golang.org/x/text', 'golang.org/x/sync'))]
                     for p in stream(evidence / ('dependencies-' + name + '.txt'))
                     if not p['ImportPath'].startswith(('golang.org/x/text', 'golang.org/x/sync'))
                     and any(i.startswith(('golang.org/x/text', 'golang.org/x/sync')) for i in p.get('Imports', []))}
    for mode in ('binary', 'source'):
        label = mode + '-' + name
        assert tests[label]['exit'] == 0
        entries = stream(evidence / (label + '.json'))
        findings = [v['finding'] for v in entries if 'finding' in v]
        old_ids = {v['finding']['osv'] for v in stream(previous / (label + '.json')) if 'finding' in v}
        ids = {v['osv'] for v in findings}
        assert 'GO-2026-5970' not in ids
        scans[label] = {'removed_ids': sorted(old_ids - ids), 'added_ids': sorted(ids - old_ids),
                        'remaining_ids': sorted(ids), 'symbol_ids': sorted({v['osv'] for v in findings if v['trace'][0].get('function')}),
                        'config': [v['config'] for v in entries if 'config' in v]}
assert len((evidence / 'scan-network.txt').read_text().strip().splitlines()) == 1
assert (evidence / 'scan-network.txt').read_text().split()[:2] == ['lo', 'DOWN']
result = {'status': 'experimental-not-selected', 'inventories': inventories, 'tests': tests,
          'linked_module_changes': linked, 'build_settings_changes': settings, 'external_importers': imports, 'binaries': binaries,
          'scans': scans, 'console': json.loads((evidence / 'console-runtime-result.json').read_text(encoding='utf-8')),
          'main_module_language_change': {'before': '1.18', 'after': '1.25.0', 'accepted': False},
          'full_regression_pass': False, 'historical_compatibility_established': False, 'launch_approved': False}
for file in evidence.glob('*.sh'):
    subprocess.run(['bash', '-n', str(file)], check=True)
if '--check' in sys.argv:
    assert patch == (evidence / '09-text-experimental.patch').read_text(encoding='utf-8')
    assert result == json.loads((evidence / 'review.json').read_text(encoding='utf-8'))
else:
    (evidence / '09-text-experimental.patch').write_text(patch, encoding='utf-8')
    (evidence / 'review.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    license_bytes = Path('/home/rehearsal/go/pkg/mod/golang.org/x/text@v0.39.0/LICENSE').read_bytes()
    license_path = evidence / 'upstream-fix/LICENSE'
    if license_path.exists():
        assert license_path.read_bytes() == license_bytes
    else:
        license_path.write_bytes(license_bytes)
print(json.dumps({'status': result['status'], 'linked_changes': linked, 'external_importers': imports,
                  'symbols': {k: v['symbol_ids'] for k, v in scans.items()}, 'binaries': binaries}, indent=2))
