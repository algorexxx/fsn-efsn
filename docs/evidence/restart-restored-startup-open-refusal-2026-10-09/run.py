from pathlib import Path
import datetime
import fcntl
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
RUN = Path('/home/rehearsal/results') / HERE.name
PRIOR = HERE.parent/'restart-restored-startup-positive-2026-10-09'
SEED = Path('/home/rehearsal/results')/PRIOR.name/'valid'
BUILD = Path('/home/rehearsal/results/restart-restored-startup-candidate-2026-10-09')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root):
    return {p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob('*')) if p.is_file()}


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def capacity():
    return {p:shutil.disk_usage(p).free for p in ['/home/rehearsal/results','/mnt/d']}


def save():
    (RUN/'run.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')


if __name__ == '__main__':
    assert not RUN.exists() and not (HERE/'qualification').exists()
    assert os.getuid()==1000 and len(sys.argv)==2
    namespace = os.readlink('/proc/self/ns/net')
    links = subprocess.check_output(['ip','-brief','link'],text=True)
    assert namespace != sys.argv[1] and len(links.splitlines())==1 and links.startswith('lo ') and 'DOWN' in links
    free = capacity()
    assert free['/home/rehearsal/results']>21*1024**3 and free['/mnt/d']>51*1024**3
    RUN.mkdir()
    record = {'started':now(),'uid':os.getuid(),'namespace':namespace,'parent_namespace':sys.argv[1],'links':links,'capacity_before':free,'input_sha256':inventory(HERE),'commands':[],'cases':{},'completed':False}
    try:
        os.nice(10)
        for line in (PRIOR/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
            digest,relative=line.split(None,1)
            assert sha(PRIOR/relative)==digest
        record['prior_manifest_sha256']=sha(PRIOR/'SHA256SUMS')
        prior=json.loads((PRIOR/'qualification/run.json').read_text(encoding='utf-8'))
        assert prior['completed']
        binary=BUILD/'bin/efsn'
        assert sha(binary)==prior['binary_sha256']['efsn']
        record['binary_sha256']=sha(binary)
        with (SEED/'efsn/chaindata/LOCK').open('rb') as source_lock:
            fcntl.flock(source_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            assert inventory(SEED)==prior['final_fixture_inventory']
            record['source_lock_held_during_copy']=True
            for case in ['locked','unreadable','malformed_current','corrupt_manifest']:
                shutil.copytree(SEED,RUN/case)
            assert inventory(SEED)==prior['final_fixture_inventory']
        record['source_unchanged']=True
        env={k:v for k,v in os.environ.items() if not k.startswith(('GO','FUSION_','F12_'))}
        env.update(GOMAXPROCS='1',GOPROXY='off',GOSUMDB='off',GOTOOLCHAIN='local')
        for case in ['locked','unreadable','malformed_current','corrupt_manifest']:
            directory=RUN/case
            db=directory/'efsn/chaindata'
            if case=='malformed_current':
                (db/'CURRENT').write_bytes(b'invalid-current\n')
            if case=='corrupt_manifest':
                target=(db/'CURRENT').read_text(encoding='utf-8').strip()
                assert target.startswith('MANIFEST-') and '/' not in target and '\\' not in target
                (db/target).write_bytes(b'not a LevelDB manifest\n')
            before=inventory(db)
            mode=db.stat().st_mode & 0o777
            lock=None
            try:
                if case=='locked':
                    lock=(db/'LOCK').open('rb')
                    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                if case=='unreadable':
                    db.chmod(0)
                args=['timeout','--kill-after=10s','45s',str(binary),'--config',str(BUILD/'profile.toml'),'--datadir',str(directory),'--syncmode','full','--gcmode','archive','--networkid','32659','--cache','64','--maxpeers','0','--port','0','--nat','none','--nodiscover','--v5disc=false','--ipcdisable','--authrpc.port','0','--mine=false','--autobt=false','--usb=false','--exec','console.log("UNEXPECTED_STARTED")','console']
                entry={'name':case,'argv':args,'started':now()}
                with (RUN/(case+'.stdout.txt')).open('wb') as output,(RUN/(case+'.stderr.txt')).open('wb') as errors:
                    entry['exit']=subprocess.run(args,cwd=BUILD/'node',env=dict(env,FUSION_STARTUP_TEST_PROFILE=str(directory/'profile.json')),stdout=output,stderr=errors).returncode
                entry['finished']=now()
                record['commands'].append(entry)
                save()
            finally:
                if case=='unreadable': db.chmod(mode)
                if lock is not None: lock.close()
            text=(RUN/(case+'.stdout.txt')).read_text(encoding='utf-8')+(RUN/(case+'.stderr.txt')).read_text(encoding='utf-8')
            reason='existing database required:' if case=='unreadable' else 'read-only database open:'
            assert entry['exit']==1 and 'restored startup: '+reason in text,(case,text)
            if case=='unreadable': assert 'permission denied' in text
            assert 'UNEXPECTED_STARTED' not in text and 'Initialising Ethereum protocol' not in text
            after=inventory(db)
            assert before==after and db.stat().st_mode & 0o777 == mode,case
            record['cases'][case]={'cold_files_before':before,'cold_files_after':after,'mode_before':mode,'mode_after':db.stat().st_mode & 0o777,'unchanged':True,'expected_reason':reason}
            save()
            print(case,'pass',flush=True)
        assert sha(binary)==record['binary_sha256'] and inventory(HERE)==record['input_sha256']
        record['binary_inputs_unchanged']=True
        record['completed']=True
    except BaseException as exc:
        record['failure']=repr(exc)
        raise
    finally:
        record['finished']=now()
        record['capacity_after']=capacity()
        save()
        shutil.copytree(RUN,HERE/'qualification',ignore=shutil.ignore_patterns('locked','unreadable','malformed_current','corrupt_manifest'))
