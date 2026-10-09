from pathlib import Path
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / 'qualification'
run = json.loads((OUTPUT / 'run.json').read_text(encoding='utf-8'))
text = (OUTPUT / 'boundaries.stdout.txt').read_text(encoding='utf-8')
expected = {'complete_mainnet': True, 'empty_database': False, 'missing_datong': False, 'split_heads': False, 'missing_head_header': False, 'foreign_genesis_same_chain_id': True, 'wrong_chain_id': True, 'changed_fork_config': True, 'missing_head_state': True, 'missing_head_body': True}
observations = [json.loads(line.split('reader boundary observation: ', 1)[1]) for line in text.splitlines() if 'reader boundary observation: ' in line]
assert run['completed'] and 'failure' not in run
assert run['source_toolchain_inputs_unchanged']
assert [(c['name'], c['exit']) for c in run['commands']] == [('build', 0), ('boundaries', 0)]
assert len(observations) == len(expected)
assert {o['case']: o['reader_accepted'] for o in observations} == expected
assert all(o['database_unchanged'] for o in observations)
assert set(re.findall(r'--- PASS: TestRestoredStartupReaderBoundaries/(\w+)', text)) == set(expected)
assert re.search(r'^--- PASS: TestRestoredStartupReaderBoundaries ', text, re.M)
assert text.rstrip().endswith('PASS') and '--- FAIL:' not in text
for observation in observations:
    for field, case in [('foreign_genesis', 'foreign_genesis_same_chain_id'), ('wrong_chain_id', 'wrong_chain_id'), ('changed_fork_config', 'changed_fork_config'), ('missing_head_state', 'missing_head_state'), ('missing_head_body', 'missing_head_body')]:
        assert observation[field] == (observation['case'] == case)
assert run['namespace'] != run['parent_namespace']
assert len(run['links'].splitlines()) == 1 and run['links'].startswith('lo ') and 'DOWN' in run['links']
for relative, digest in run['input_sha256'].items():
    path = OUTPUT / 'reader_test.go' if relative == 'internal/recovery/reader_test.go' else HERE / Path(relative).name
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, relative
result = {'verified_pass': True, 'scope': 'candidate recovery Reader characterization only; no service startup gate implemented', 'case_count': len(observations), 'observations': observations, 'source_file_count': len(run['source_inventory']), 'prior_files_verified': run['prior_files_verified'], 'run_sha256': hashlib.sha256((OUTPUT/'run.json').read_bytes()).hexdigest()}
(HERE / 'verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps({key: result[key] for key in ['verified_pass', 'case_count', 'source_file_count', 'prior_files_verified']}))
