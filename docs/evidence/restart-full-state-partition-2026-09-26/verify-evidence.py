import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
working = workspace / 'tmp/full-state-partition-2026-09-26'


def git(*args):
    return subprocess.check_output(['git', '-c', 'core.safecrlf=false', *args], cwd=workspace).decode().strip()


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def retain(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert digest(source) == digest(target), target
    else:
        shutil.copyfile(source, target)


def read(name):
    return (evidence / name).read_text(encoding='utf-8')


baseline = git('rev-parse', '92a561b')
assert baseline in read('environment.txt') and 'go version go1.21.3 linux/amd64' in read('environment.txt')
for prefix, binary in [('', 'full-state-partition-tests'), ('diagnostic-', 'full-state-partition-diagnostic-tests')]:
    assert read(prefix + 'build.txt') == ''
    assert read(prefix + 'binary.sha256').split()[0] == digest(workspace / 'tmp' / binary)
data = read('partition-race.txt')
diagnostic = read('diagnostic-race.txt')
for content, exit_file, test in [(data, 'partition-exit.txt', 'TestFullStatePartitionRepair'), (diagnostic, 'diagnostic-exit.txt', 'TestFullStatePartitionColdDiagnosis')]:
    assert int(read(exit_file)) == 1 and content.endswith('FAIL\n')
    assert 'WARNING: DATA RACE' not in content and '--- SKIP:' not in content
    assert content.count('--- FAIL:') == 1 and f'--- FAIL: {test} (' in content
for name in ['prepare-producer', 'prepare-verifier', 'fund-producer', 'fund-verifier']:
    assert f'--- PASS: TestFullStatePartitionRepair/{name} (' in data
for role in ['producer', 'verifier']:
    assert f'--- PASS: TestFullStatePartitionColdDiagnosis/audit-{role} (' in diagnostic
assert 'did not reproduce a stable nonce gap on a common advancing chain' in data
assert 'full-state partition stable gap' not in data and not (working / 'repair').exists()
assert 'stopped fork did not converge through ordinary synchronization; diagnostic retained' in diagnostic
assert diagnostic.count('participant ledger passed:') == 2
assert diagnostic.count('blocks=3 totalRewardWei=937500000000000000; no database opened') == 2
assert 'fromnum=15,085,106' in diagnostic and 'headers=0' in diagnostic
cut = re.search(r'full-state partition isolated duration=([^ ]+) fork=(\d+) heads=(\d+)/(\d+) hashes=(0x[0-9a-f]+)/(0x[0-9a-f]+)', data)
drops = re.search(r'healed partition; netem dropped=(\d+)', data)
assert cut and drops and cut[5] != cut[6] and int(cut[2]) > 15130086 and int(drops[1]) > 0
sync = json.loads((working / 'cold-sync-diagnosis.json').read_text(encoding='utf-8'))
assert sync['Before'] == sync['Automatic'] == sync['After']
assert sync['ExplicitDownloader'] == 'action from bad peer ignored: multiple headers (0) for single request'
assert sync['Before'][0]['TD'] == sync['Before'][1]['TD'] == hex(63370514724)
assert sync['Before'][0]['Hash'] != sync['Before'][1]['Hash']
branches = {}
ledgers = []
for i, role in enumerate(['producer', 'verifier']):
    status = sync['Before'][i]
    assert not status['Mining'] and not status['AutoBuy'] and status['Signatures'] == 0
    assert status['Pending'] == status['Queued'] == 0
    peers = sync['Peers'][i]
    assert len(peers) == 1
    protocol = peers[0]['protocols']['efsn']
    assert protocol['head'] == sync['Before'][1-i]['Hash'] and protocol['difficulty'] == int(status['TD'], 16)
    cold = json.loads((working / f'cold-{role}.json').read_text(encoding='utf-8'))
    assert cold['Header']['hash'] == status['Hash'] and int(cold['TotalDifficulty']) == int(status['TD'], 16)
    assert len(bytes.fromhex(cold['Saved'][2:])) == 117
    assert f"hash={status['Hash']} nonce={cold['Nonce']}" in data
    files = sorted((working / f'cold-{role}').glob('block-*.json'))
    assert len(files) == status['Number'] - 15130080 == 26
    transactions = 0
    branch = []
    for n, path in enumerate(files, 1):
        assert path.name == f'block-{n:02d}.json'
        ledger = json.loads(path.read_text(encoding='utf-8'))
        assert int(ledger['Header']['number'], 16) == 15130080 + n
        if branch:
            assert ledger['Header']['parentHash'] == branch[-1]['Header']['hash']
        for receipt in ledger['Receipts']:
            assert int(receipt['status'], 16) == 1
        transactions += len(ledger['Receipts'])
        branch.append(ledger)
        for suffix in ['.json', '.rlp']:
            retain(path.with_suffix(suffix), evidence / 'artifacts' / role / path.with_suffix(suffix).name)
    assert branch[-1]['Header']['hash'] == status['Hash']
    assert branch[int(cut[3+i]) - 15130080 - 1]['Header']['hash'] == cut[5+i]
    branches[role] = {'blocks': len(files), 'head': status['Hash'], 'transactions': transactions, 'nonce': cold['Nonce'], 'saved_bytes': 117}
    ledgers.append(branch)
    retain(working / f'cold-{role}.json', evidence / f'cold-{role}.json')
fork = int(cut[2]) - 15130080 - 1
assert ledgers[0][:fork] == ledgers[1][:fork]
assert all(left['Header']['hash'] != right['Header']['hash'] for left, right in zip(ledgers[0][fork:], ledgers[1][fork:]))
for name in ['fixture.json', 'handover.json']:
    retain(working / 'producer' / name, evidence / 'artifacts' / name)
retain(working / 'cold-sync-diagnosis.json', evidence / 'cold-sync-diagnosis.json')
manifest = workspace / 'docs/evidence/restart-state-export-2026-09-24/artifact-SHA256SUMS'
assert digest(manifest) == 'a6c86fc58a9f7b482a02b787a337d600e32a447551e45dbe40d210b498341bbf'
entries = [line.split('  ./', 1) for line in manifest.read_text(encoding='utf-8').splitlines()]
assert len(entries) == 230
for expected, relative in entries:
    assert digest(workspace / 'tmp/preserved-head-state' / relative) == expected, relative
capacity = json.loads(read('copy-capacity.json'))
assert capacity['source_files'] == 230 and capacity['copied_bytes'] == 1057634160 and capacity['free_bytes_after_copy'] > 50 * 1024**3
changed = git('diff', '--name-only', baseline).splitlines()
assert not [name for name in changed if (name.endswith('.go') and not name.endswith('_test.go')) or name in ['go.mod', 'go.sum']]
sources = list(json.loads((workspace / 'docs/evidence/restart-full-state-participant-2026-09-26/identities.json').read_text(encoding='utf-8'))['sources'])
sources += ['tests/restart/full_state_partition_linux_test.go', 'tests/restart/full_state_partition_diagnostic_linux_test.go', 'tests/restart/continuous_repair_linux_test.go', 'tests/restart/displaced_purchase_rpc_linux_test.go', 'tests/restart/partition_funds_ledger_linux_test.go', 'core/tx_pool.go', 'eth/sync.go', 'eth/handler.go', 'eth/downloader/downloader.go', 'params/network_params.go']
sources = sorted(set(sources))
identities = {'baseline': baseline, 'runtime_changed': False, 'sources': {name: {'git_blob': git('hash-object', '--path=' + name, name), 'sha256': digest(workspace / name)} for name in sources}}
identities['initial_build_overrides'] = {('tests/restart/' + path.name.removesuffix('.txt')): {'retained_source': path.relative_to(evidence).as_posix(), 'sha256': digest(path)} for path in sorted((evidence / 'initial-sources').glob('*.go.txt'))}
identities['diagnostic_only_test'] = 'tests/restart/full_state_partition_diagnostic_linux_test.go'
results = {'live_seconds': float(re.search(r'^--- FAIL: TestFullStatePartitionRepair \(([0-9.]+)s\)', data, re.M)[1]), 'diagnostic_seconds': float(re.search(r'^--- FAIL: TestFullStatePartitionColdDiagnosis \(([0-9.]+)s\)', diagnostic, re.M)[1]), 'recovery_success': False, 'manual_repair_reached': False, 'test_exits': [1, 1], 'isolated': cut.groups(), 'packet_drops': int(drops[1]), 'branches': branches, 'cold_branch_accounting_passed': True, 'matching_canonical_heads': False, 'stopped_total_difficulty': 63370514724, 'first_missing_binary_probe': 15085106, 'source_files_unchanged': 230}
for name, content in [('results.json', results), ('identities.json', identities)]:
    (evidence / name).write_text(json.dumps(content, indent=2) + '\n', encoding='utf-8', newline='\n')
files = sorted(path for path in evidence.rglob('*') if path.is_file() and path.name != 'SHA256SUMS')
(evidence / 'SHA256SUMS').write_text(''.join(f'{digest(path)}  {path.relative_to(evidence).as_posix()}\n' for path in files), encoding='utf-8', newline='\n')
print(f'Verified two retained failures, both 26-block cold ledgers, connected equal-weight peers, missing ancestor probe, 230 unchanged source files, {len(sources)} source identities and {len(files)} evidence hashes')
