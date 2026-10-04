import hashlib
import json
from pathlib import Path
import re
import sys


def read_stream(path):
    source = path.read_text(encoding='utf-8')
    decoder = json.JSONDecoder()
    entries = []
    position = 0
    while position < len(source):
        if source[position].isspace():
            position += 1
            continue
        entry, position = decoder.raw_decode(source, position)
        entries.append(entry)
    return entries


def summarize_scan(evidence, name):
    entries = read_stream(evidence / (name + '.json'))
    configurations = [entry['config'] for entry in entries if 'config' in entry]
    assert len(configurations) == 1
    config = configurations[0]
    assert config['scanner_version'] == 'v1.8.0'
    assert config['db'] == 'file:///home/rehearsal/results/restart-release-followup-2026-10-04/vulndb'
    assert config['db_last_modified'] == '2026-10-01T20:24:15Z'
    assert config['scan_mode'] == name.split('-')[0]
    assert config['scan_level'] == 'symbol'
    assert (evidence / (name + '-exit.txt')).read_text().strip() == '0'
    assert not (evidence / (name + '.stderr.txt')).read_bytes()
    advisories = {entry['osv']['id']: entry['osv'] for entry in entries if 'osv' in entry}
    findings = [entry['finding'] for entry in entries if 'finding' in entry]
    grouped = {}
    for finding in findings:
        first = finding['trace'][0]
        level = 'symbol' if first.get('function') else 'package' if first.get('package') else 'module'
        record = grouped.setdefault(finding['osv'], {
            'id': finding['osv'], 'summary': advisories[finding['osv']]['summary'],
            'review_status': advisories[finding['osv']].get('database_specific', {}).get('review_status'),
            'module': first['module'], 'installed': first.get('version'),
            'listed_fixed': finding.get('fixed_version'), 'levels': {},
        })
        record['levels'][level] = record['levels'].get(level, 0) + 1
    ranks = {'module': 0, 'package': 1, 'symbol': 2}
    for record in grouped.values():
        record['highest_level'] = max(record['levels'], key=ranks.get)
    return {
        'config': config, 'advisory_records_returned': len(advisories),
        'finding_records': len(findings), 'unique_finding_ids': len(grouped),
        'ids_by_highest_level': {
            level: sorted(key for key, value in grouped.items() if value['highest_level'] == level)
            for level in ranks
        },
        'findings': sorted(grouped.values(), key=lambda value: value['id']),
    }


def verify_fixtures(evidence):
    inputs = json.loads((evidence / 'test-inputs.json').read_text(encoding='utf-8'))
    workspace = evidence.parents[2]
    for path, digest in inputs['baseline_overlay'].items():
        assert hashlib.sha256((evidence / 'baseline-tests' / Path(path).name).read_bytes()).hexdigest() == digest
    for path, digest in inputs['after'].items():
        assert hashlib.sha256((workspace / path).read_bytes().replace(b'\r\n', b'\n')).hexdigest() == digest
    assert hashlib.sha256((evidence / '07-discovery-fixtures.patch').read_bytes()).hexdigest() == inputs['patch_sha256']
    pairs = json.loads((evidence / 'converted-vectors.json').read_text(encoding='utf-8'))
    originals = json.loads((evidence / 'original-vectors.json').read_text(encoding='utf-8'))
    assert len(pairs) == len(originals) == 6
    before = (evidence / 'baseline-tests/udp_test.go').read_text(encoding='utf-8')
    expected = before
    for pair, original in zip(pairs, originals):
        assert pair['original'] == original
        old, new = bytes.fromhex(original), bytes.fromhex(pair['fusion'])
        assert old[97] in (1, 2, 3, 4) and new[97] == old[97] + 39
        assert old[98:] == new[98:]
        assert before.count(original) == 1
        expected = expected.replace(original, pair['fusion'])
    assert expected == (workspace / 'p2p/discover/udp_test.go').read_text(encoding='utf-8')
    assert (evidence / 'discovery-before-exit.txt').read_text().strip() == '1'
    before_log = (evidence / 'discovery-before.txt').read_text(encoding='utf-8')
    for name in ('TestParseNode', 'TestForwardCompatibility'):
        assert '--- FAIL: ' + name in before_log
    for name in ('focused', 'package'):
        assert (evidence / ('discovery-' + name + '-exit.txt')).read_text().strip() == '0'
        output = (evidence / ('discovery-' + name + '.txt')).read_text(encoding='utf-8')
        assert 'WARNING: DATA RACE' not in output and '--- FAIL:' not in output
        for test in ('TestParseNode', 'TestNodeString', 'TestForwardCompatibility'):
            assert '--- PASS: ' + test in output
    skipped = re.findall(r'^--- SKIP: (\S+)', output, re.M)
    assert skipped == ['TestRestartPeerAddressLive', 'TestRestartDiscoverySelfLive']
    return {'corrected_vectors': 6, 'payloads_and_expected_objects_unchanged': True, 'opt_in_tests_skipped': skipped}


evidence = Path(__file__).resolve().parent
result = {'discovery': verify_fixtures(evidence), 'scans': {}}
for mode in ('binary', 'source'):
    for target in ('efsn', 'fsn-recovery'):
        name = mode + '-' + target
        result['scans'][name] = summarize_scan(evidence, name)
for name in ('scan-network.txt', 'source-scan-network.txt'):
    network = (evidence / name).read_text(encoding='utf-8').strip().splitlines()
    assert len(network) == 1 and network[0].split()[:2] == ['lo', 'DOWN']
for name in ('efsn', 'fsn-recovery'):
    assert (evidence / ('source-' + name + '-modules-before.sha256')).read_bytes() == (evidence / ('source-' + name + '-modules-after.sha256')).read_bytes()
assert result['scans']['source-efsn']['ids_by_highest_level']['symbol'] == ['GO-2024-3250', 'GO-2025-3553', 'GO-2026-5970', 'GO-2026-6278']
assert result['scans']['source-fsn-recovery']['ids_by_highest_level']['symbol'] == []
if '--check' in sys.argv:
    assert json.loads((evidence / 'scan-summary.json').read_text(encoding='utf-8')) == result
    print('PASS fixture identities, preserved payloads, explicit skips and four offline scan summaries')
else:
    (evidence / 'scan-summary.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    for name, scan in result['scans'].items():
        print(name, {level: len(ids) for level, ids in scan['ids_by_highest_level'].items()})
