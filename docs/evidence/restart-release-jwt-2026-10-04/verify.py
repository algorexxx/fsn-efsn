import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_stream(path):
    content = path.read_text(encoding='utf-8')
    decoder = json.JSONDecoder()
    entries = []
    position = 0
    while position < len(content):
        if content[position].isspace():
            position += 1
            continue
        entry, position = decoder.raw_decode(content, position)
        entries.append(entry)
    return entries


def linked_modules(path):
    return {parts[1]: parts[2:] for line in path.read_text(encoding='utf-8').splitlines()
            if (parts := line.split()) and parts[0] == 'dep'}


evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
previous = evidence.parent / 'restart-release-selection-2026-10-04'
audit = evidence.parent / 'restart-release-followup-2026-10-04'
work = Path('/home/rehearsal/results/restart-release-jwt-2026-10-04')
selected = Path('/home/rehearsal/results/restart-release-selection-2026-10-04')
inputs = json.loads((evidence / 'patch-inputs.json').read_text(encoding='utf-8'))
assert digest(evidence / '08-jwt-dependency.patch') == inputs['patch_sha256']
for name, expected in inputs['after'].items():
    assert hashlib.sha256((workspace / name).read_bytes().replace(b'\r\n', b'\n')).hexdigest() == expected
inventories = {}
for name, folder in [('node', 'source'), ('recovery', 'repeat')]:
    source = work / name
    actual = {p.relative_to(source).as_posix(): digest(p) for p in source.rglob('*') if p.is_file()}
    assert actual == json.loads((evidence / (name + '-inventory.json')).read_text(encoding='utf-8'))
    base = {p.relative_to(selected / folder).as_posix(): digest(p) for p in (selected / folder).rglob('*') if p.is_file()}
    changed = {p for p in set(actual) | set(base) if actual.get(p) != base.get(p)}
    assert changed == {'go.mod', 'go.sum'}
    inventories[name] = {'files': len(actual), 'changed_paths': sorted(changed)}
module_inventory = json.loads((evidence / 'upstream-inventories.json').read_text(encoding='utf-8'))
for version, expected in module_inventory.items():
    directory = Path('/home/rehearsal/go/pkg/mod/github.com/golang-jwt/jwt/v4@' + version)
    assert {p.relative_to(directory).as_posix(): digest(p) for p in directory.rglob('*') if p.is_file()} == expected
assert module_inventory['v4.4.2']['go.mod'] == module_inventory['v4.5.2']['go.mod']
tests = {}
for name in ['baseline-jwt-complete-cache', 'node-package-test', 'upstream-parser-tests']:
    assert (evidence / (name + '-exit.txt')).read_text().strip() == '0'
    output = (evidence / (name + '.txt')).read_text(encoding='utf-8')
    assert not any(text in output for text in ['--- FAIL:', '--- SKIP:', 'WARNING: DATA RACE', '[no tests to run]'])
    expected = ['TestSplitToken', 'TestParser_Parse', 'TestSetPadding'] if name == 'upstream-parser-tests' else ['TestJWT']
    for test in expected:
        assert '--- PASS: ' + test + ' (' in output, (name, test)
    tests[name] = {'top_level_passes': re.findall(r'^--- PASS: (\S+)', output, re.M), 'summary': output.splitlines()[-1]}
modules = {}
binaries = {}
for name, original in [('efsn', 'selected'), ('fsn-recovery', 'recovery')]:
    assert (evidence / ('build-' + name + '-exit.txt')).read_text().strip() == '0'
    assert not (evidence / ('build-' + name + '.txt')).read_bytes()
    current = linked_modules(evidence / ('build-info-' + name + '.txt'))
    prior = linked_modules(previous / (original + '-build-info.txt'))
    changed = {key for key in set(prior) | set(current) if prior.get(key) != current.get(key)}
    assert changed == ({'github.com/golang-jwt/jwt/v4'} if name == 'efsn' else set())
    modules[name] = {key: {'before': prior.get(key), 'after': current.get(key)} for key in sorted(changed)}
    binaries[name] = digest(work / 'bin' / name)
    assert binaries[name] == (evidence / ('binary-' + name + '.sha256')).read_text().split()[0]
assert binaries['fsn-recovery'] == (previous / 'recovery-binary.sha256').read_text().split()[0]
scans = {}
for mode in ('binary', 'source'):
    for name in ('efsn', 'fsn-recovery'):
        label = mode + '-' + name
        assert (evidence / (label + '-exit.txt')).read_text().strip() == '0'
        assert not (evidence / (label + '.stderr.txt')).read_bytes()
        entries = read_stream(evidence / (label + '.json'))
        config = [item['config'] for item in entries if 'config' in item]
        assert len(config) == 1 and config[0]['scanner_version'] == 'v1.8.0'
        assert config[0]['db'] == 'file:///home/rehearsal/results/restart-release-followup-2026-10-04/vulndb'
        assert config[0]['db_last_modified'] == '2026-10-01T20:24:15Z'
        assert config[0]['scan_mode'] == mode
        findings = [item['finding'] for item in entries if 'finding' in item]
        ids = {item['osv'] for item in findings}
        old_ids = {item['finding']['osv'] for item in read_stream(audit / (label + '.json')) if 'finding' in item}
        removed = old_ids - ids
        assert not (ids - old_ids)
        assert removed == ({'GO-2024-3250', 'GO-2025-3553'} if name == 'efsn' else set())
        assert not ({'GO-2024-3250', 'GO-2025-3553'} & ids)
        symbol_ids = {item['osv'] for item in findings if item['trace'][0].get('function')}
        expected = {'GO-2026-5970', 'GO-2026-6278'} if name == 'efsn' else {'GO-2026-6278'} if mode == 'binary' else set()
        assert symbol_ids == expected
        scans[label] = {'ids': sorted(ids), 'symbol_ids': sorted(symbol_ids), 'removed_ids': sorted(removed), 'config': config[0]}
network = (evidence / 'scan-network.txt').read_text().strip().splitlines()
assert len(network) == 1 and network[0].split()[:2] == ['lo', 'DOWN']
test_network = (evidence / 'cache-ready-test-network.txt').read_text().strip().splitlines()
assert len(test_network) == 1 and 'LOWER_UP' in test_network[0]
for runner in evidence.glob('*.sh'):
    subprocess.run(['bash', '-n', str(runner)], check=True)
result = {'inventories': inventories, 'tests': tests, 'linked_module_changes': modules,
          'binary_sha256': binaries, 'scans': scans, 'dependency_security_approval': False,
          'full_project_test_pass': False, 'launch_approved': False}
if '--check' in sys.argv:
    assert result == json.loads((evidence / 'acceptance.json').read_text(encoding='utf-8'))
else:
    (evidence / 'acceptance.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print(json.dumps({'tests': {key: value['summary'] for key, value in tests.items()},
                  'linked_module_changes': modules, 'binary_sha256': binaries,
                  'symbol_findings': {key: value['symbol_ids'] for key, value in scans.items()}}, indent=2))
