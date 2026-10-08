from pathlib import Path
import hashlib
import importlib.util
import json
import re
import statistics
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
Q = HERE / 'qualification'
spec = importlib.util.spec_from_file_location('qualification_runner', HERE/'run.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
record = json.loads((Q/'run.json').read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert record['completed'] and record['source_inventories_unchanged']
assert 'failure' not in record
assert record['uid'] == 1000 and record['namespace'] != record['parent_namespace']
assert len(record['links'].splitlines()) == 1 and 'DOWN' in record['links']
assert record['tests'] == {'node': runner.NODE_TESTS, 'recovery': runner.RECOVERY_TESTS}
assert len(record['commands']) == 62
assert len(set(c['name'] for c in record['commands'])) == 62
assert all(c['exit'] == 0 for c in record['commands'])
for filename, digest in record['input_sha256'].items():
    assert sha(HERE/filename) == digest
for filename, digest in record['fixture_inputs'].items():
    assert sha(runner.REPO/filename) == digest
for mode, compiler in record['toolchains'].items():
    env = compiler['go_env']
    assert env['GOVERSION'] == ('go1.21.3' if mode=='old' else 'go1.27.1')
    assert env['GOENV'] == '' and env['GOFLAGS'] == '-mod=readonly'
    assert env['GOPROXY'] == 'off' and env['GOSUMDB'] == 'off'
    assert env['GOOS'] == 'linux' and env['GOARCH'] == 'amd64'
    assert env['CGO_ENABLED'] == '1' and env['GOAMD64'] == 'v1'
previous_files = 0
for name, expected in record['previous_manifest_sha256'].items():
    directory = HERE.parent/name
    assert sha(directory/'SHA256SUMS') == expected
    for line in (directory/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        digest, relative = line.split(None, 1)
        assert sha(directory/relative) == digest
        previous_files += 1
assert previous_files == record['previous_files_verified']
helper_bytes = (Q/'helpers_test.go').read_bytes()
for helper in record['extracted_helpers']:
    source = runner.REPO/helper['source']
    assert sha(source) == helper['source_sha256']
    body = b''.join(source.read_bytes().splitlines(keepends=True)[helper['start_line']-1:helper['end_line']])
    assert hashlib.sha256(body).hexdigest() == helper['body_sha256']
    assert helper_bytes.count(body) == 1
assert len(record['extracted_helpers']) == 5
prior = json.loads((runner.PRIOR/'qualification/run.json').read_text(encoding='utf-8'))
for mode in ['old','candidate']:
    for kind in ['node','recovery']:
        expected = json.loads((HERE.parent/'restart-release-jwt-2026-10-04'/(kind+'-inventory.json')).read_text(encoding='utf-8'))
        if mode == 'candidate':
            expected.update(prior['runtime_input_sha256'])
        expected.update({name: digest for name,digest in record['fixture_inputs'].items() if kind=='recovery' or name not in ['tests/restart/'+f for f in runner.RECOVERY_FILES]})
        expected['tests/restart/helpers_test.go'] = sha(Q/'helpers_test.go')
        for bench in (['old','modern'] if mode=='old' else ['candidate']) if kind=='node' else []:
            encoder = (runner.PRIOR/('candidate_encoder.go' if bench=='candidate' else 'stdlib_encoder.go')).read_bytes().replace(b'package main', b'package encoderbench', 1)
            expected['.f12-bench-'+bench+'/encoder.go'] = hashlib.sha256(encoder).hexdigest()
            expected['.f12-bench-'+bench+'/benchmark_test.go'] = sha(HERE/'benchmark_test.go')
        assert record['source_inventories'][mode+'-'+kind] == expected
passed = {}
for mode in ['old','candidate']:
    cases = []
    for kind, tests in [('node',runner.NODE_TESTS), ('recovery',runner.RECOVERY_TESTS)]:
        for test in tests:
            command = mode+'-'+kind+'-'+test
            output = (Q/(command+'.stdout.txt')).read_text(encoding='utf-8')
            errors = (Q/(command+'.stderr.txt')).read_text(encoding='utf-8')
            assert not errors and '--- FAIL:' not in output and '--- SKIP:' not in output and 'DATA RACE' not in output
            assert output.endswith('PASS\n')
            names = re.findall(r'^\s*--- PASS: (\S+) \(', output, re.M)
            assert names.count(test) == 1
            assert all(n == test or n.startswith(test+'/') for n in names)
            cases.extend(names)
    output = (Q/(mode+'-node-snapshot.stdout.txt')).read_text(encoding='utf-8')
    names = re.findall(r'^--- PASS: (\S+) \(', output, re.M)
    assert set(names) == {'TestSnapshotRejectsTruncatedCount', 'TestSnapshotPreservesValidEncoding', 'TestSnapshotRejectsInvalidFraming'}
    assert len(names) == 3 and '\nPASS\n' in output
    assert not (Q/(mode+'-node-snapshot.stderr.txt')).read_bytes()
    cases.extend(names)
    passed[mode] = sorted(cases)
assert passed['old'] == passed['candidate']
comparisons = {}
for kind, test in [('node','TestHistoricalBridgeImportsOnIndependentState'), ('node','TestSingleBackupBlockHandover'), ('recovery','TestRecoveryGuard'), ('recovery','TestRecoveryJournalHandover')]:
    observed = {}
    for mode in ['old','candidate']:
        output = (Q/(mode+'-'+kind+'-'+test+'.stdout.txt')).read_text(encoding='utf-8')
        observed[mode] = re.findall(r'^\s+\w+_test.go:\d+: (.*)$', output, re.M)
    assert observed['old'] and observed['old'] == observed['candidate'], test
    comparisons[test] = observed['old']
samples = {mode: {h: [] for h in ['0','15130080','12000000']} for mode in ['old','modern','candidate']}
for round_number in range(1,6):
    for mode in samples:
        name = 'benchmark-'+str(round_number)+'-'+mode
        output = (Q/(name+'.stdout.txt')).read_text(encoding='utf-8')
        assert output.endswith('PASS\n') and not (Q/(name+'.stderr.txt')).read_bytes()
        rows = [line.split() for line in output.splitlines() if line.startswith('BenchmarkEncode/')]
        assert len(rows) == 3 and {row[0].split('/')[1] for row in rows} == set(samples[mode])
        for row in rows:
            assert len(row) == 10 and row[1] == '100'
            assert row[3] == 'ns/op' and row[7] == 'B/op' and row[9] == 'allocs/op'
            samples[mode][row[0].split('/')[1]].append({'round':round_number, 'ns_per_op':float(row[2]), 'bytes_per_op':int(row[6]), 'allocs_per_op':int(row[8])})
medians = {mode: {height: {field: statistics.median(sample[field] for sample in values) for field in ['ns_per_op','bytes_per_op','allocs_per_op']} for height,values in heights.items()} for mode,heights in samples.items()}
ratios = {height: {field: medians['candidate'][height][field]/medians['old'][height][field] for field in ['ns_per_op','bytes_per_op','allocs_per_op']} for height in samples['old']}
result = {'pass':True, 'commands':len(record['commands']), 'started':record['started'], 'finished':record['finished'], 'previous_files_verified':previous_files, 'passed_test_names':passed, 'top_level_tests_per_selection':sum('/' not in name for name in passed['old']), 'subtests_per_selection':sum('/' in name for name in passed['old']), 'deterministic_log_comparisons':comparisons, 'benchmark_samples':samples, 'benchmark_medians':medians, 'candidate_over_old':ratios, 'remaining_bytes':record['remaining_bytes']}
(HERE/'verification.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ['passed_test_names','deterministic_log_comparisons','benchmark_samples']}, indent=2))
