from pathlib import Path
import hashlib
import json

HERE=Path(__file__).resolve().parent
r=json.loads((HERE/'qualification/run.json').read_text(encoding='utf-8'))
names=['locked','unreadable','malformed_current','corrupt_manifest']
assert r['completed'] and 'failure' not in r
assert r['source_lock_held_during_copy'] and r['source_unchanged'] and r['binary_inputs_unchanged']
assert [(c['name'],c['exit']) for c in r['commands']]==[(n,1) for n in names]
assert set(r['cases'])==set(names)
for name in names:
    case=r['cases'][name]
    text=''.join((HERE/'qualification'/(name+'.'+suffix+'.txt')).read_text(encoding='utf-8') for suffix in ['stdout','stderr'])
    assert 'restored startup: '+case['expected_reason'] in text
    assert 'UNEXPECTED_STARTED' not in text and 'Initialising Ethereum protocol' not in text
    assert case['cold_files_before']==case['cold_files_after'] and case['mode_before']==case['mode_after'] and case['unchanged']
assert r['namespace']!=r['parent_namespace'] and 'DOWN' in r['links'] and len(r['links'].splitlines())==1
for relative,digest in r['input_sha256'].items():
    assert hashlib.sha256((HERE/relative).read_bytes()).hexdigest()==digest
result={'verified_pass':True,'cases_verified':names,'binary_sha256':r['binary_sha256'],'run_sha256':hashlib.sha256((HERE/'qualification/run.json').read_bytes()).hexdigest()}
(HERE/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
