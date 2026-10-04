import hashlib
import json
import statistics
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


baseline = read(bundle / 'baseline.json')
for name, value in baseline['source_sha256'].items():
    assert digest(root / name) == value, name

windows = bundle / 'attempt-1/windows'
linux = bundle / 'attempt-1/linux'
for path in [windows / 'test-exit.txt', windows / 'backlog-exit.txt', linux / 'test-exit.txt', linux / 'backlog-ordinary-exit.txt', linux / 'backlog-race-exit.txt']:
    assert path.read_text(encoding='utf-8').strip() == '0', path
for name, value in read(windows / 'sources.json').items():
    assert digest(root / name) == value, name
for line in (linux / 'sources.sha256').read_text(encoding='utf-8').splitlines():
    value, name = line.split('  ', 1)
    assert digest(root / name) == value, name
assert (linux / 'history_backlog_test.go.txt').read_bytes() == (root / 'internal/observe/history_backlog_test.go').read_bytes()

sources = {'windows': windows / 'backlog.json', 'linux': linux / 'backlog-ordinary.json', 'linux_race': linux / 'backlog-race.json'}
summary = {}
exports = set()
for name, path in sources.items():
    result = read(path)
    assert [(s['Blocks'], s['Height']) for s in result['Samples']] == [(128, 157), (1024, 1053), (4096, 4125)]
    assert len(result['Batches']) == 32 and result['DisplacedBlocks'] == 64
    assert result['FinalStatus'] == result['RestoredStatus']
    assert result['FinalStatus']['MaxBytes'] == 16777216
    assert result['FinalStatus']['LogicalBytes'] < 16777216
    assert result['ExportSHA256'] == result['RestoredExportSHA256']
    exports.add(result['ExportSHA256'])
    timeline = result['RestoredTimeline']
    assert timeline['Status'] == 'complete_for_retained_prefix'
    assert timeline['Through']['Number'] == 4125 and timeline['BaselineSequence'] == 1
    assert timeline['Events'] == []
    changes = [i for i in result['RestoredStatus']['Incidents'] if i['Kind'] == 'canonical_history_change' and i['Node'] == 'node-2']
    assert len(changes) == 1 and changes[0]['Status'] == 'acknowledged'
    assert changes[0]['LastReview']['Action'] == 'acknowledge'
    assert set(result['RPCMethods']) == {'eth_chainId', 'net_version', 'eth_getBlockByNumber', 'eth_getRawTransactionByBlockHashAndIndex', 'eth_getTransactionReceipt'}
    assert result['RPCMethods']['eth_getRawTransactionByBlockHashAndIndex'] == 4160
    assert result['RPCMethods']['eth_getTransactionReceipt'] == 4160
    summary[name] = {
        'timeline_samples': [{'blocks': s['Blocks'], 'logical_bytes': s['LogicalBytes'], 'median_ms': statistics.median(o['Nanoseconds'] for o in s['Operations']) / 1000000, 'median_allocated_bytes': statistics.median(o['AllocatedBytes'] for o in s['Operations'])} for s in result['Samples']],
        'backfill_median_ms': statistics.median(o['Nanoseconds'] for o in result['Batches']) / 1000000,
        'backfill_max_ms': max(o['Nanoseconds'] for o in result['Batches']) / 1000000,
        'replacement_ms': result['ForkOperation']['Nanoseconds'] / 1000000,
        'final_logical_bytes': result['FinalStatus']['LogicalBytes'],
        'closed_copy_bytes': result['CopiedBytes'],
        'closed_copy_files': result['CopiedFiles'],
    }
assert len(exports) == 1
fixture = root / 'docs/evidence/restart-observer-mining-2026-09-27/attempt-3/mining'
record = {
    'verified': True,
    'unchanged_existing_source_files': len(baseline['source_sha256']),
    'extension_blocks': 4096,
    'replacement_blocks': 64,
    'export_sha256': next(iter(exports)),
    'fixture_sha256': {name: digest(fixture / name) for name in ['ipc-config.json', 'cold-history-export.jsonl', 'ledger-29.json']},
    'results': summary,
    'consensus_validity_tested': False,
    'rolling_retention_implemented': False,
    'alert_delivery_tested': False,
}
(bundle / 'verification.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record, indent=2))
