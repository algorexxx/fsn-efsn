import hashlib
import json
from pathlib import Path
import re

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
base = Path('/home/rehearsal/results/restart-operator-kit-2026-10-04')
outcomes = []
for attempt, expected_exit in [(1, 1), (2, 1), (3, 0), (4, 0)]:
    result = evidence / f'attempt-{attempt}'
    work = base if attempt == 1 else base.with_name(base.name + f'-attempt-{attempt}')
    assert (result / 'build-exit.txt').read_text(encoding='utf-8').strip() == '0'
    for name in ['test-exit.txt', 'exit-code.txt']:
        assert (result / name).read_text(encoding='utf-8').strip() == str(expected_exit)
    expected = json.loads((result / 'source-sha256.json').read_text(encoding='utf-8'))
    actual = {p.relative_to(work / 'source').as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted((work / 'source').rglob('*')) if p.is_file()}
    assert expected == actual, f'attempt {attempt} retained source changed'
    binaries = {}
    for line in (result / 'binaries.sha256').read_text(encoding='utf-8').splitlines():
        digest, name = line.split(None, 1)
        path = Path(name.strip())
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
        binaries[path.name] = digest
    text = (result / 'test.txt').read_text(encoding='utf-8')
    assert 'WARNING: DATA RACE' not in text and '--- SKIP:' not in text and 'panic:' not in text
    outcome = {'attempt': attempt, 'status': 'pass' if expected_exit == 0 else 'failed_setup',
               'exit': expected_exit, 'binaries_sha256': binaries,
               'retained_source_files': len(actual), 'retained_source_and_binary_readback': 'pass'}
    if expected_exit:
        failure = ('small reserve fixture owner 1 has 0 tickets' if attempt == 1
                   else "snapshot_package.py': [Errno 2] No such file or directory")
        assert failure in text and '--- FAIL: TestRestartNodeRehearsal/operator_kit' in text
        outcome['failure'] = failure
    else:
        assert '--- FAIL:' not in text
        passed = re.search(r'--- PASS: TestRestartNodeRehearsal/operator_kit \(([\d.]+)s\)', text)
        assert passed is not None and float(passed[1]) < 480
        restore = re.search(r'verified fresh synthetic restore: bytes=(\d+) manifest=([0-9a-f]{64})', text)
        assert restore is not None and int(restore[1]) < 64 * 1024**2
        final = re.search(r'operator kit: restored height=(\d+) anchor=(0x[0-9a-f]{64}) first purchase=(0x[0-9a-f]{64}) both replenished through=(\d+) final=(\d+) hash=(0x[0-9a-f]{64})', text)
        assert final is not None and int(final[1]) == 24 and int(final[5]) <= 24 + 12 + 64
        for required in ['operator console admin.addPeer(', 'operator console fsntx.buyTicket(',
                         'operator console eth.getTransactionReceipt(', '"mining":true,"buying":true',
                         '"mining":false,"buying":false', 'common head unchanged for 35s',
                         'two distinct live producers and both cold commitments/lookups passed']:
            assert required in text, required
        cold = [json.loads(line.split('OPERATOR_RESULT ', 1)[1]) for line in text.splitlines()
                if 'OPERATOR_RESULT {"number":' in line]
        assert len(cold) == 2 and cold[0] == cold[1]
        assert cold[0] == {'number': int(final[5]), 'hash': final[6], 'mining': False, 'buying': False}
        outcome.update({'seconds': float(passed[1]), 'restored_bytes': int(restore[1]),
                        'manifest_sha256': restore[2], 'anchor_hash': final[2], 'first_purchase': final[3],
                        'replenished_through': int(final[4]), 'final_number': int(final[5]), 'final_hash': final[6],
                        'cold_processes': 2, 'race_reports': 0, 'skips': 0})
    outcomes.append(outcome)

for name in ['operator_kit_linux_test.go', 'node_rehearsal_linux_test.go', 'snapshot_package.py']:
    assert (workspace / 'tests/restart' / name).read_bytes().replace(b'\r\n', b'\n') == (evidence / 'attempt-4/inputs' / name).read_bytes()
assert (evidence / 'run-linux.sh').read_bytes() == (evidence / 'attempt-4/run-linux.sh').read_bytes()
acceptance = {'status': 'pass', 'scope': 'local fresh-restore and actual-console operator workflow',
              'production_changes': False, 'clean_machine_or_final_release_acceptance': False,
              'node_services': 'existing race-instrumented embedded harness with synthetic genesis/anchor and unlocked public keys',
              'funding': '50000 synthetic FSN for each public test owner at genesis; not a real reserve recommendation',
              'final_assertions': ['settled and cold native receipts for every suffix purchase',
                                   'first entrant purchase remains canonical', 'both producers and replenishment remain canonical',
                                   'all three heads and state/ticket commitments agree', 'nonce and saved purchase bytes survive cold restart'],
              'attempts': outcomes, 'final_workspace_test_inputs_match': True}
(evidence / 'acceptance.json').write_text(json.dumps(acceptance, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': acceptance['status'], 'attempts': [(x['attempt'], x['status']) for x in outcomes],
                  'final_seconds': outcomes[-1]['seconds'], 'final_hash': outcomes[-1]['final_hash']}, indent=2))
