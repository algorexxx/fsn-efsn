import difflib
import hashlib
import json
from pathlib import Path
import re

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
base = Path('/home/rehearsal/results/restart-automatic-sync-2026-10-04')
names = ['compatible_catchup', 'anchored_refusal', 'unanchored_control']
outcomes = []
inventories = []
for attempt in [1, 2]:
    result = evidence / f'attempt-{attempt}'
    work = base if attempt == 1 else base.with_name(base.name + '-attempt-2')
    for name in ['build-exit.txt', 'test-exit.txt', 'exit-code.txt']:
        assert (result / name).read_text(encoding='utf-8').strip() == '0'
    expected = json.loads((result / 'source-sha256.json').read_text(encoding='utf-8'))
    inventories.append(expected)
    actual = {p.relative_to(work / 'source').as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted((work / 'source').rglob('*')) if p.is_file()}
    assert expected == actual, f'attempt {attempt} retained source changed'
    digest = hashlib.sha256((work / 'bin/restart-tests').read_bytes()).hexdigest()
    assert (result / 'binary.sha256').read_text(encoding='utf-8').split()[0] == digest
    text = (result / 'test.txt').read_bytes().decode('utf-8', errors='replace')
    for forbidden in ['WARNING: DATA RACE', '--- FAIL:', '--- SKIP:', 'panic:']:
        assert forbidden not in text, forbidden
    cases = {}
    for name in names:
        match = re.search(r'--- PASS: TestRestartNodeRehearsal/unknown_heavier_automatic_sync/' + name + r' \(([\d.]+)s\)', text)
        assert match is not None, name
        sync = re.search(r'automatic sync result=' + name + r' elapsed=([\d.]+)s offeredTD=(\d+) initialTD=(\d+)', text)
        assert sync is not None and float(sync[1]) < 90 and int(sync[2]) > int(sync[3])
        cases[name] = {'pass_seconds': float(match[1]), 'sync_seconds': float(sync[1]),
                       'offered_td': int(sync[2]), 'initial_td': int(sync[3])}
    duration = re.search(r'--- PASS: TestRestartNodeRehearsal/unknown_heavier_automatic_sync \(([\d.]+)s\)', text)
    assert duration is not None and float(duration[1]) < 360
    assert 'observed automatic downloader rejection:' in text
    assert 'have 0x0e1729d1ef69c183066be945a88de16e78ccb7bd8fffc885fe1952a4ba9e4e41, want 0xf19f36203f28da4e88d15c8b433e49624867fff74bc855dbab21f2b82df21925' in text
    assert text.count('live/cold canonical transactions, receipts, three heads, state and ticket commitments agree') == 3
    outcomes.append({'attempt': attempt, 'status': 'pass', 'seconds': float(duration[1]),
                     'cases': cases, 'binary_sha256': digest, 'retained_source_files': len(actual),
                     'retained_source_and_binary_readback': 'pass', 'skips': 0, 'race_reports': 0})

assert inventories[0].keys() == inventories[1].keys()
assert [name for name in inventories[0] if inventories[0][name] != inventories[1][name]] == ['tests/restart/automatic_sync_linux_test.go']
first = (evidence / 'attempt-1/inputs/automatic_sync_linux_test.go').read_text(encoding='utf-8').splitlines(keepends=True)
final = (evidence / 'attempt-2/inputs/automatic_sync_linux_test.go').read_text(encoding='utf-8').splitlines(keepends=True)
assert len(first) == len(final)
for before, after in zip(first, final):
    if before != after:
        assert 't.Logf(' in before or 't.Fatalf(' in before
        assert before.replace('.Hash()', '.Hash().Hex()').replace('.Root()', '.Root().Hex()').replace('.MixDigest()', '.MixDigest().Hex()') == after
(evidence / 'test-log-formatting.patch').write_text(''.join(difflib.unified_diff(first, final, fromfile='attempt-1/automatic_sync_linux_test.go', tofile='attempt-2/automatic_sync_linux_test.go')), encoding='utf-8')
for name in ['automatic_sync_linux_test.go', 'node_rehearsal_linux_test.go']:
    assert (workspace / 'tests/restart' / name).read_bytes().replace(b'\r\n', b'\n') == (evidence / 'attempt-2/inputs' / name).read_bytes()
assert (evidence / 'run-linux.sh').read_bytes() == (evidence / 'attempt-2/run-linux.sh').read_bytes()
acceptance = {'status': 'pass', 'scope': 'R8 bounded complete-ancestry unknown-heavier automatic full-sync investigation',
              'production_changes': False, 'final_release_acceptance': False,
              'attempts': outcomes, 'only_inter_attempt_source_change': 'test hash log/failure formatting',
              'final_workspace_test_inputs_match': True}
(evidence / 'acceptance.json').write_text(json.dumps(acceptance, indent=2) + '\n', encoding='utf-8')
print(json.dumps(acceptance, indent=2))
