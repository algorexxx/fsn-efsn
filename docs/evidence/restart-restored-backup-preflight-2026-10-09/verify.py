from pathlib import Path
import gzip
import hashlib
import json

HERE=Path(__file__).resolve().parent
r=json.loads((HERE/'qualification/run.json').read_text(encoding='utf-8'))
assert r['completed'] and 'failure' not in r and r['identities_unchanged'] and r['backup_metadata_unchanged']
assert r['uid']==1000 and r['namespace']!=r['parent_namespace'] and r['mount_namespace']!=r['parent_mount_namespace']
assert len(r['links'].splitlines())==1 and r['links'].startswith('lo ') and 'DOWN' in r['links']
assert 'ro' in r['backup_mount']['options'].split(',')
assert [(c['name'],c['exit']) for c in r['commands']]==[('build',0),('check',0)]
assert all(c['output_bytes_after']<256*1024**2 for c in r['commands'])
assert all(c['free_bytes']['/home/rehearsal/results']>20*1024**3 and c['free_bytes']['/mnt/d']>50*1024**3 for c in r['commands'])
prior=json.loads((HERE.parent/'restart-restored-startup-candidate-2026-10-09/qualification/run.json').read_text(encoding='utf-8'))
replay=json.loads((HERE.parent/'restart-ticket-encoder-job-4500000-v2-2026-10-09/qualification/run.json').read_text(encoding='utf-8'))
assert r['source_inventory']==prior['build_source_inventory'] and r['go_binary_sha256']==prior['go_binary_sha256']
assert r['backup_before']==r['backup_after']==replay['backup_after']
for phase in ['before','after']:
    raw=gzip.decompress((HERE/'qualification'/('backup-'+phase+'.json.gz')).read_bytes())
    rows=json.loads(raw)
    expected=r['backup_'+phase]
    assert hashlib.sha256(raw).hexdigest()==expected['metadata_sha256']
    assert len(rows)==expected['files'] and sum(row[1] for row in rows)==expected['logical_bytes']
for name,digest in r['input_sha256'].items(): assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==digest
output=(HERE/'qualification/check.stdout.txt').read_text(encoding='utf-8')
assert output.endswith('PASS\n') and '--- SKIP:' not in output and '--- FAIL:' not in output
assert not (HERE/'qualification/check.stderr.txt').read_bytes()
values=[json.loads(line.split('BACKUPSTARTUP ',1)[1]) for line in output.splitlines() if 'BACKUPSTARTUP ' in line]
assert values==[r['observation']]
v=r['observation']
assert v['height']==15130080 and v['genesis']=='0xc2422b1d9d16331be2a5b207c0783027d4419498003f729f4b9e9c5c1838623a'
assert v['hash']=='0xe93ffded087a79097d4309c7831690161db6ed136f4b1a22c4c83a99db80f99f'
assert v['startup_check_passed'] and v['read_only_mount'] and v['test_anchor_only']
result={'verified_pass':True,'observation':v,'backup_metadata':r['backup_after'],'scope':'direct unselected startup check on complete read-only backup; no writable CLI startup, history execution, full-state traversal or recovery/handover acceptance','run_sha256':hashlib.sha256((HERE/'qualification/run.json').read_bytes()).hexdigest()}
(HERE/'verification.json').write_bytes((json.dumps(result,indent=2)+'\n').encode('utf-8'))
print(json.dumps(result,indent=2))
