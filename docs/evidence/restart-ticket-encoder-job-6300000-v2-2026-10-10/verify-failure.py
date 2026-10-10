from pathlib import Path
import datetime
import hashlib
import json

here = Path(__file__).resolve().parent
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
verified = {}
for relative in ('inputs/SHA256SUMS', 'LAUNCH_SHA256SUMS',
                 'OUTPUT_SHA256SUMS', 'PREPARED_SHA256SUMS', 'SHA256SUMS'):
    manifest = here / relative
    count = 0
    for line in manifest.read_text(encoding='utf-8').splitlines():
        expected, name = line.split(None, 1)
        target = (manifest.parent / name).resolve()
        assert target.is_relative_to(here), name
        assert digest(target) == expected, name
        count += 1
    verified[relative] = dict(files=count, sha256=digest(manifest))

completion = json.loads((here / 'completion.json').read_bytes())
run = json.loads((here / 'qualification/run.json').read_bytes())
status = json.loads((here / 'qualification/status.json').read_bytes())
host = json.loads((here / 'host-dispatch-finished.json').read_bytes())
capacity = json.loads((here / 'capacity-review.json').read_bytes())
assert completion['exit'] == host['exit'] == 1
assert completion['verified_pass'] is False
assert completion['automatic_continuation'] is False
assert run['completed'] is False and status['completed'] is False
assert [command['exit'] for command in run['commands']] == [0, 0, 0, 0, 1]
checks = run['additional_preservation_checks']
assert len(checks) == 10 and all(value is True for value in checks.values())
for key in ('backup_unchanged', 'baselines_unchanged', 'selected_unchanged',
            'candidate_unchanged', 'inputs_unchanged'):
    assert run[key] is True, key
assert status['observed_height'] == 5976608
assert status['observed_height_is_provisional'] is True
assert status['stop_reason'] is None
assert not (here / 'STOP').exists()
assert not (here / 'verification.json').exists()
log = (here / 'qualification/replay.stdout.txt').read_text(encoding='utf-8')
assert 'replay stopped before next batch: /mnt/d has 53563531264 bytes free, reserve 53687091200' in log
assert '--- FAIL: TestPreservedHistoryReplay' in log
entries = capacity['Entries']
assert len(entries) == 14
assert sum(entry['Files'] for entry in entries) == 9191
assert sum(entry['LogicalBytes'] for entry in entries) == 13630973746
assert all(entry['ReparseEntries'] == 0 for entry in entries)
assert 'FusionRehearsal' not in capacity['RunningDistributions']

result = dict(
    verified_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    failure_evidence_integrity_passed=True,
    job_completed_successfully=False,
    saved_endpoint_verified=False,
    scope='Sealed failure records, stop classification and capacity proposal only; no database opened or hashed.',
    manifests=verified,
    script_sha256=digest(Path(__file__).resolve()),
)
output = here / 'failure-evidence-verification.json'
assert not output.exists(), 'Preserve existing verification record'
output.write_bytes((json.dumps(result, indent=2) + '\n').encode('utf-8'))
print(json.dumps(result))
