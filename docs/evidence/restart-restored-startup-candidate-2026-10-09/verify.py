from pathlib import Path
import hashlib
import json
import runpy

HERE = Path(__file__).resolve().parent
r = json.loads((HERE/'qualification/run.json').read_text(encoding='utf-8'))
cases = runpy.run_path(str(HERE/'run.py'))['CASES']
commands = {c['name']:c for c in r['commands']}
assert not r['completed'] and r['failure'] == "AssertionError('restored')"
assert commands['restored']['exit'] == 2
assert '(*BlockChain).Stop' in (HERE/'qualification/restored.stderr.txt').read_text(encoding='utf-8')
assert set(r['refusals']) == set(cases)
for name, error in cases.items():
    result = r['refusals'][name]
    text = ''.join((HERE/'qualification'/(name+'.'+suffix+'.txt')).read_text(encoding='utf-8') for suffix in ['stdout','stderr'])
    assert commands[name]['exit'] == 1 and error in text
    assert result['cold_files_before'] == result['cold_files_after'] and result['unchanged']
    assert 'Initialising Ethereum protocol' not in text and 'Starting peer-to-peer node' not in text and 'RESTOREDCLI ' not in text
for name, digest in r['input_sha256'].items():
    assert hashlib.sha256((HERE/name).read_bytes()).hexdigest() == digest
result = {'verified_pass': False, 'negative_cases_verified': 15, 'positive_path': 'failed during shutdown; see preserved panic', 'runtime_candidate_selected': False, 'run_sha256':hashlib.sha256((HERE/'qualification/run.json').read_bytes()).hexdigest()}
(HERE/'verification.json').write_text(json.dumps(result, indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
