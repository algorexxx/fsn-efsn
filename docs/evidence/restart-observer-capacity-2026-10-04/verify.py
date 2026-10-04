import hashlib
import json
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


baseline = read(bundle / 'baseline.json')
changed = sorted(name for name, value in baseline['source_sha256'].items() if digest(root / name) != value)
assert changed == ['cmd/fsn-observe/main.go', 'internal/observe/history.go'], changed
windows = bundle / 'attempt-3/windows'
linux = bundle / 'attempt-2/linux'
for path in [windows / 'test-exit.txt', windows / 'build-exit.txt', linux / 'test-exit.txt', linux / 'build-exit.txt', linux / 'backlog-exit.txt']:
    assert path.read_text(encoding='utf-8').strip() == '0', path
for name, value in read(windows / 'sources.json').items():
    assert digest(root / name) == value, name
for line in (linux / 'sources.sha256').read_text(encoding='utf-8').splitlines():
    value, name = line.split('  ', 1)
    assert digest(root / name) == value, name

tests = [
    'TestHistoryCopyResumesExhaustedEvidence',
    'TestHistoryCopyPreservesTicketBaseline',
    'TestHistoryCopyRejectsUnsafeInputs',
    'TestHistoryCopyInterruptedDestinationCannotOpen',
    'TestCommandHistoryCopyIsOfflineAndExplicit',
]
for path in [windows / 'tests.txt', linux / 'tests-race.txt']:
    log = path.read_text(encoding='utf-8')
    assert 'FAIL' not in log, path
    for name in tests:
        assert '--- PASS: ' + name + ' (' in log, name
assert '--- PASS: TestHistoryCopyRejectsSourceAlias (' in (linux / 'tests-race.txt').read_text(encoding='utf-8')
assert '--- SKIP: TestHistoryCopyRejectsSourceAlias (' in (windows / 'tests.txt').read_text(encoding='utf-8')
network = (linux / 'network.txt').read_text(encoding='utf-8').splitlines()
assert len(network) == 1 and network[0].split()[0] == 'lo', network

backlog = read(linux / 'backlog.json')
assert backlog['FinalStatus'] == backlog['RestoredStatus']
assert backlog['ExportSHA256'] == backlog['RestoredExportSHA256']
assert backlog['DisplacedBlocks'] == 64
assert [(s['Blocks'], s['Height']) for s in backlog['Samples']] == [(128, 157), (1024, 1053), (4096, 4125)]
assert backlog['RestoredTimeline']['Status'] == 'complete_for_retained_prefix'
assert backlog['RestoredTimeline']['Through']['Number'] == 4125
assert backlog['FinalStatus']['LogicalBytes'] == 9833913
old_backlog = read(root / 'docs/evidence/restart-observer-backlog-2026-10-04/attempt-1/linux/backlog-ordinary.json')
assert backlog['ExportSHA256'] == old_backlog['ExportSHA256']

for attempt in ['attempt-1', 'attempt-2']:
    failed = bundle / attempt / 'windows'
    assert (failed / 'test-exit.txt').read_text(encoding='utf-8').strip() == '1'
    assert 'Access is denied.' in (failed / 'tests.txt').read_text(encoding='utf-8')
    manifest = read(failed / 'sources.json')
    assert digest(bundle / attempt / 'history_copy.go.txt') == manifest['internal/observe/history_copy.go']

fixture = root / 'docs/evidence/restart-observer-mining-2026-09-27/attempt-3/mining'
result = {
    'verified': True,
    'baseline': baseline['baseline'],
    'changed_existing_source_files': changed,
    'unchanged_existing_source_files': len(baseline['source_sha256']) - len(changed),
    'accepted_windows_attempt': 3,
    'accepted_linux_attempt': 2,
    'windows_suite_and_build': 'passed outside restricted sandbox',
    'linux_race_suite_and_build': 'passed in loopback-only namespace',
    'windows_symlink_case': 'skipped; OS symlink privilege unavailable',
    'linux_symlink_case': 'passed',
    'rejected_windows_sandbox_runs_retained': [1, 2],
    'capacity_cases': tests,
    'backlog_export_sha256': backlog['ExportSHA256'],
    'fixture_sha256': {name: digest(fixture / name) for name in ['ipc-config.json', 'cold-history-export.jsonl', 'ledger-29.json']},
    'rolling_retention_implemented': False,
    'alert_delivery_tested': False,
    'power_loss_publication_tested': False,
}
(bundle / 'verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
