from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent/'restart-restored-startup-candidate-2026-10-09'
r = json.loads((HERE/'qualification/run.json').read_text(encoding='utf-8'))
p = json.loads((PRIOR/'qualification/run.json').read_text(encoding='utf-8'))
assert r['completed'] and 'failure' not in r
assert r['sources_binaries_prior_cases_unchanged'] and r['original_refusal_files_still_match']
assert r['binary_sha256'] == p['binary_sha256']
assert r['namespace'] != r['parent_namespace']
assert len(r['links'].splitlines())==1 and r['links'].startswith('lo ') and 'DOWN' in r['links']
assert [(c['name'],c['exit']) for c in r['commands']] == [('seed',0),('below-anchor',0),('restored',0),('advance',0),('restarted',0)]
expected = r['expected_heads']
observations = []
for phase,head in [('below-anchor','parent'),('restored','parent'),('advance','child'),('restarted','child')]:
    output = (HERE/'qualification'/(phase+'.stdout.txt')).read_text(encoding='utf-8')
    errors = (HERE/'qualification'/(phase+'.stderr.txt')).read_text(encoding='utf-8')
    value = {'head':expected[head+'_height'],'hash':expected[head],'mining':False,'autoBuy':False}
    assert [json.loads(line.split('RESTOREDCLI ',1)[1]) for line in output.splitlines() if line.startswith('RESTOREDCLI ')] == [value]
    assert 'panic:' not in errors and 'Blockchain manager stopped' in errors
    assert errors.index('readonly=true') < errors.index('Initialising Ethereum protocol')
    if phase == 'advance':
        assert 'IMPORTED true' in output
    observations.append({'phase':phase,**value})
assert observations == r['observations']
assert hashlib.sha256((PRIOR/'SHA256SUMS').read_bytes()).hexdigest() == r['prior_manifest_sha256']
for relative,digest in r['input_sha256'].items():
    assert hashlib.sha256((HERE/relative).read_bytes()).hexdigest()==digest
result = {'verified_pass':True,'positive_phases':observations,'prior_refusal_cases_reused':15,'scope':'synthetic archive-mode actual CLI startup/import/restart; no complete restored-history or pruning-mode acceptance','run_sha256':hashlib.sha256((HERE/'qualification/run.json').read_bytes()).hexdigest()}
(HERE/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'verified_pass':True,'positive_phases':len(observations),'prior_refusal_cases_reused':15}))
