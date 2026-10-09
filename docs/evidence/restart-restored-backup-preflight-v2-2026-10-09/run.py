from pathlib import Path
import importlib.util
import json
import os
import shutil
import subprocess
import sys

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
RUN=Path('/home/rehearsal/results')/HERE.name
PRIOR=HERE.parent/'restart-restored-startup-candidate-2026-10-09'
RETAINED=Path('/home/rehearsal/results')/PRIOR.name
REPLAY=HERE.parent/'restart-ticket-encoder-job-4500000-v2-2026-10-09'
HELPER=HERE.parent/'restart-ticket-encoder-replay-100000-2026-10-08/run.py'
GO=Path('/home/rehearsal/results/restart-release-selection-2026-10-04/toolchain/go/bin/go')
spec=importlib.util.spec_from_file_location('retained_helpers',HELPER)
h=importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
h.RUN=RUN


def execute(name,argv,env):
    free={p:shutil.disk_usage(p).free for p in ['/home/rehearsal/results','/mnt/d']}
    assert free['/home/rehearsal/results']>20*1024**3 and free['/mnt/d']>50*1024**3
    entry={'name':name,'argv':argv,'started':h.now(),'free_bytes':free}
    with (RUN/(name+'.stdout.txt')).open('wb') as output,(RUN/(name+'.stderr.txt')).open('wb') as errors:
        entry['exit']=subprocess.run(argv,cwd=RETAINED/'node/tests/restart',env=env,stdout=output,stderr=errors).returncode
    entry['finished']=h.now()
    entry['output_bytes_after']=sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file())
    record['commands'].append(entry)
    h.save()
    print(name,entry['exit'],flush=True)
    assert entry['output_bytes_after']<256*1024**2
    assert entry['exit']==0,name
    return (RUN/(name+'.stdout.txt')).read_text(encoding='utf-8')


assert os.getuid()==1000 and len(sys.argv)==4 and not RUN.exists() and not (HERE/'qualification').exists()
net,mnt=os.readlink('/proc/self/ns/net'),os.readlink('/proc/self/ns/mnt')
assert net!=sys.argv[1] and mnt!=sys.argv[2]
view=Path(sys.argv[3])
assert os.statvfs(view).f_flag & os.ST_RDONLY
links=subprocess.check_output(['ip','-brief','link'],text=True)
assert len(links.splitlines())==1 and links.startswith('lo ') and 'DOWN' in links
for p in Path('/proc').iterdir():
    if p.name.isdigit():
        try: assert (p/'comm').read_text(encoding='utf-8').strip() not in ['efsn','replay-tests','observer']
        except (FileNotFoundError,ProcessLookupError): pass
free={p:shutil.disk_usage(p).free for p in ['/home/rehearsal/results','/mnt/d']}
assert free['/home/rehearsal/results']>21*1024**3 and free['/mnt/d']>51*1024**3
RUN.mkdir()
(RUN/'tmp').mkdir()
record={'started':h.now(),'uid':os.getuid(),'namespace':net,'parent_namespace':sys.argv[1],'mount_namespace':mnt,'parent_mount_namespace':sys.argv[2],'backup_mount':h.mount_description(view),'links':links,'capacity_before':free,'completed':False,'commands':[],'input_sha256':h.inventory(HERE),'helper_sha256':h.sha(HELPER),'locks':'parent holds actual backup LOCK shared and replay run lock exclusive; observer uses LevelDB read-only shared lock'}
h.record=record
try:
    os.nice(10)
    prior=json.loads((PRIOR/'qualification/run.json').read_text(encoding='utf-8'))
    replay=json.loads((REPLAY/'qualification/run.json').read_text(encoding='utf-8'))
    assert json.loads((REPLAY/'completion.json').read_text(encoding='utf-8'))['verified_pass']
    for directory in [PRIOR,REPLAY]:
        for line in (directory/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
            digest,relative=line.split(None,1)
            assert h.sha(directory/relative)==digest
    record['prior_manifest_sha256']={p.name:h.sha(p/'SHA256SUMS') for p in [PRIOR,REPLAY]}
    record['source_inventory']=h.inventory(RETAINED/'node')
    assert record['source_inventory']==prior['build_source_inventory']
    assert h.sha(GO)==prior['go_binary_sha256']
    record['go_binary_sha256']=prior['go_binary_sha256']
    record['backup_before']=h.metadata(view,'backup-before')
    assert record['backup_before']==replay['backup_after']
    env={k:v for k,v in os.environ.items() if not k.startswith(('GO','FUSION_','F12_'))}
    env.update(PATH=str(GO.parent)+':/usr/bin:/bin',GOENV='off',GOTOOLCHAIN='local',GOWORK='off',GOPROXY='off',GOSUMDB='off',GOFLAGS='-mod=readonly',CGO_ENABLED='1',GOAMD64='v1',GOMAXPROCS='1',GOCACHE='/home/rehearsal/results/restart-release-selection-2026-10-04/repeat-cache',GOMODCACHE='/home/rehearsal/go/pkg/mod',GOTMPDIR=str(RUN/'tmp'),TMPDIR=str(RUN/'tmp'))
    record['go_env']=json.loads(subprocess.check_output([str(GO),'env','-json'],cwd=RETAINED/'node',env=env,text=True))
    overlay={'Replace':{str(RETAINED/'node/tests/restart/seed_test.go'):str(HERE/'check_test.go')}}
    (RUN/'overlay.json').write_text(json.dumps(overlay,indent=2)+'\n',encoding='utf-8')
    execute('build',['timeout','--kill-after=10s','5m',str(GO),'test','-p=1','-trimpath','-buildvcs=false','-overlay='+str(RUN/'overlay.json'),'-c','-o',str(RUN/'check-tests'),'.'],env)
    record['observer_sha256']=h.sha(RUN/'check-tests')
    output=execute('check',['timeout','--kill-after=10s','3m',str(RUN/'check-tests'),'-test.run=^TestCompleteBackupStartupPreflight$','-test.v','-test.timeout=2m'],dict(env,FUSION_STARTUP_BACKUP_VIEW=str(view)))
    values=[json.loads(line.split('BACKUPSTARTUP ',1)[1]) for line in output.splitlines() if 'BACKUPSTARTUP ' in line]
    assert len(values)==1 and values[0]['startup_check_passed']
    record['observation']=values[0]
    assert h.inventory(RETAINED/'node')==record['source_inventory']
    assert h.sha(RUN/'check-tests')==record['observer_sha256']
    assert h.inventory(HERE)==record['input_sha256'] and h.sha(HELPER)==record['helper_sha256']
    record['identities_unchanged']=True
    record['completed']=True
except BaseException as exc:
    record['failure']=repr(exc)
    raise
finally:
    record['backup_after']=h.metadata(view,'backup-after')
    record['backup_metadata_unchanged']=record.get('backup_before')==record['backup_after']
    if not record['backup_metadata_unchanged']: record['completed']=False
    record['finished']=h.now()
    record['capacity_after']={p:shutil.disk_usage(p).free for p in ['/home/rehearsal/results','/mnt/d']}
    h.save()
    shutil.copytree(RUN,HERE/'qualification',ignore=shutil.ignore_patterns('check-tests','tmp'))
