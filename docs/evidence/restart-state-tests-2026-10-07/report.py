import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
baseline = Path('/home/rehearsal/results/restart-release-jwt-2026-10-04/node')
candidate = Path('/home/rehearsal/results/restart-release-text-2026-10-04/node')
upstream = 'c5f0174d88ab2b9c3086c6a9cc9ccf38a072992f'
subprocess.run([sys.executable, str(evidence.parent / 'restart-release-text-2026-10-04/report.py'), '--check'], check=True, capture_output=True)
sources = {}
for name in ('core/state/statedb.go', 'core/state/journal.go', 'core/state/state_object.go', 'core/vm/instructions.go', 'core/vm/evm.go', 'core/evm.go', 'common/fork.go'):
    original = subprocess.check_output(['git', '-c', 'safe.directory=' + str(workspace), '-C', str(workspace), 'show', upstream + ':' + name])
    assert original == (baseline / name).read_bytes() == (candidate / name).read_bytes()
    assert original == (workspace / name).read_bytes().replace(b'\r\n', b'\n')
    sources[name] = hashlib.sha256(original).hexdigest()
calls = []
for path in sorted(baseline.rglob('*.go')):
    if path.name.endswith('_test.go'):
        continue
    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if re.search(r'\.Suicide\s*\(', line):
            calls.append({'path': path.relative_to(baseline).as_posix(), 'line': number, 'source': line.strip()})
assert calls == [{'path': 'core/vm/instructions.go', 'line': 839, 'source': 'interpreter.evm.StateDB.Suicide(scope.Contract.Address())'}]
tests = {}
for phase, count in (('api', 4), ('qualified', 5), ('verified', 6)):
    folder = evidence / phase
    assert (folder / 'finished.txt').exists()
    network = (folder / 'network.txt').read_text(encoding='utf-8').strip().splitlines()
    assert len(network) == 1 and network[0].split()[:2] == ['lo', 'DOWN']
    for stage, source in (('baseline', baseline), ('candidate', candidate)):
        overlay = json.loads((folder / (stage + '-overlay.json')).read_text(encoding='utf-8'))['Replace']
        assert len(overlay) == count
        for old, saved in overlay.items():
            assert Path(old).parent == source / 'core/state'
            assert Path(saved).parent == folder and Path(saved).exists()
            if phase == 'qualified':
                assert Path(saved).read_bytes() == (workspace / 'core/state' / Path(saved).name).read_bytes().replace(b'\r\n', b'\n')
        log = (folder / (stage + '.txt')).read_text(encoding='utf-8')
        result = {
            'exit': int((folder / (stage + '-exit.txt')).read_text(encoding='utf-8')),
            'passed_top_level': re.findall(r'^--- PASS: (\S+)', log, re.M),
            'failed_top_level': re.findall(r'^--- FAIL: (\S+)', log, re.M),
            'skipped_top_level': re.findall(r'^--- SKIP: (\S+)', log, re.M),
            'panic': '\npanic:' in log,
        }
        assert result['exit'] == 1 and len(result['passed_top_level']) == 15
        assert not result['skipped_top_level'] and 'WARNING: DATA RACE' not in log
        assert 'OK: 5 passed' in log
        expected = ['TestSnapshotRandom']
        if phase != 'api':
            expected += ['TestSuicideSnapshotRestoresFlag', 'TestSuicideSnapshotPreservesTimeLockAsset']
        if phase == 'verified':
            expected += ['TestSelfdestructParentRollback']
            assert result['panic'] and '(*stateObject).CopyBalances' in log
        else:
            assert not result['panic']
        assert result['failed_top_level'] == expected
        tests[phase + '-' + stage] = result
vector = json.loads((evidence / 'dump-vector.json').read_text(encoding='utf-8'))
fixture = (workspace / 'core/state/state_test.go').read_text(encoding='utf-8')
literal = re.search('want := ' + chr(96) + '(.*?)' + chr(96), fixture, re.S).group(1)
assert json.loads(literal) == vector
assert vector['root'] == '09c81cf1049993c874a455403e5e8440c32ba09a4356f98bb443a127d6a9f2a2'
assert '71edff0130dd2385947095001c73d9e28d862fc286fca2b922ca6f6f3cddfdd2' in (evidence / 'dump-vector.stderr.txt').read_text(encoding='utf-8')
for path in evidence.glob('*.py'):
    ast.parse(path.read_text(encoding='utf-8'))
subprocess.run(['bash', '-n', str(evidence / 'run.sh')], check=True)
result = {
    'status': 'state-tests-compile-with-inherited-rollback-failures',
    'upstream': upstream,
    'unchanged_source_sha256': sources,
    'selected_production_suicide_calls': calls,
    'tests': tests,
    'dump_vector_root': vector['root'],
    'active_test_snapshot': 'qualified',
    'archived_incomplete_evm_probe': 'verified',
    'full_regression_pass': False,
    'production_selection': 'P1-P17+B1+D1',
    'text_upgrade_selected': False,
    'launch_approved': False,
}
if '--check' in sys.argv:
    assert result == json.loads((evidence / 'review.json').read_text(encoding='utf-8'))
else:
    (evidence / 'review.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print(json.dumps({'status': result['status'], 'upstream_source_files_verified': len(sources),
                  'state_tests_per_build': {'passed': 15, 'failed': 3},
                  'evm_probe': 'incomplete, preserved separately'}, indent=2))
