from pathlib import Path
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
r = json.loads((HERE/'qualification/run.json').read_text(encoding='utf-8'))
assert r['completed'] and 'failure' not in r and r['sources_binaries_inputs_unchanged']
assert r['namespace'] != r['parent_namespace'] and r['uid']==1000
assert len(r['links'].splitlines())==1 and r['links'].startswith('lo ') and 'DOWN' in r['links']
assert [(c['name'],c['exit']) for c in r['commands']] == [(n,0) for n in ['seed-build','seed','restored','advance','restarted','cold']]
assert all(c['output_bytes_after'] < 256*1024**2 for c in r['commands'])
assert all(c['free_bytes']['/home/rehearsal/results'] > 20*1024**3 and c['free_bytes']['/mnt/d'] > 50*1024**3 for c in r['commands'])
observations = []
for phase, head in [('restored','parent'),('advance','child'),('restarted','child')]:
    output = (HERE/'qualification'/(phase+'.stdout.txt')).read_text(encoding='utf-8')
    errors = (HERE/'qualification'/(phase+'.stderr.txt')).read_text(encoding='utf-8')
    want = dict(r['expected'][head],mining=False,autoBuy=False)
    assert [json.loads(line.split('RESTOREDCLI ',1)[1]) for line in output.splitlines() if line.startswith('RESTOREDCLI ')] == [want]
    assert 'panic:' not in errors and 'Blockchain manager stopped' in errors
    assert errors.index('readonly=true') < errors.index('Initialising Ethereum protocol')
    assert 'Failed to commit recent state trie' not in errors and 'Dangling trie nodes' not in errors
    writes = [int(n.replace(',','')) for n in re.findall(r'Writing cached state to disk[^\n]*block=([0-9,]+)',errors)]
    assert writes == [want['head'],want['head']-1,want['head']-127]
    if phase=='advance': assert 'IMPORTED true' in output
    observations.append({'phase':phase,**want,'shutdown_heights':writes})
assert observations == r['observations']
cold = (HERE/'qualification/cold.stdout.txt').read_text(encoding='utf-8')
assert [json.loads(line.split('PRUNINGCOLD ',1)[1]) for line in cold.splitlines() if 'PRUNINGCOLD ' in line] == [r['cold_observations']]
assert [v['head'] for v in r['cold_observations']] == [130,129,3]
assert r['cold_observations'][:2] == [r['expected']['child'],r['expected']['parent']]
assert r['cold_files_before']==r['cold_files_after'] and r['cold_files_before']
for relative,digest in r['input_sha256'].items():
    assert hashlib.sha256((HERE/relative).read_bytes()).hexdigest()==digest
result = {'verified_pass':True,'phases':observations,'cold_state_heights':[130,129,3],'scope':'complete small synthetic ancestry, normal pruning CLI startup/import/shutdown/restart; no complete backup or post-legacy history acceptance','run_sha256':hashlib.sha256((HERE/'qualification/run.json').read_bytes()).hexdigest()}
(HERE/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'verified_pass':True,'cli_phases':3,'cold_state_heights':[130,129,3]}))
