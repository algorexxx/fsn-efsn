from pathlib import Path
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
RUN = Path('/home/rehearsal/results') / HERE.name
PRIOR = HERE.parent/'restart-restored-startup-candidate-2026-10-09'
RETAINED = Path('/home/rehearsal/results') / PRIOR.name
SOURCE = Path('/home/rehearsal/results/restart-ticket-encoder-candidate-v2-2026-10-08/node')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root):
    return {p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob('*')) if p.is_file() and '.f12-probe' not in p.parts}


def capacity():
    return {p:shutil.disk_usage(p).free for p in ['/home/rehearsal/results','/mnt/d']}


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def save():
    (RUN/'run.json').write_text(json.dumps(record, indent=2)+'\n',encoding='utf-8')


def execute(name, argv, env):
    free = capacity()
    assert free['/home/rehearsal/results'] > 20*1024**3 and free['/mnt/d'] > 50*1024**3
    entry = {'name':name,'argv':argv,'cwd':str(RETAINED/'node/tests/restart'),'started':now(),'free_bytes':free}
    with (RUN/(name+'.stdout.txt')).open('wb') as output, (RUN/(name+'.stderr.txt')).open('wb') as errors:
        entry['exit'] = subprocess.run(argv,cwd=entry['cwd'],env=env,stdout=output,stderr=errors).returncode
    entry['finished'] = now()
    record['commands'].append(entry)
    save()
    print(name,entry['exit'],flush=True)
    assert entry['exit'] == 0,name
    return (RUN/(name+'.stdout.txt')).read_text(encoding='utf-8')


if __name__ == '__main__':
    assert not RUN.exists() and not (HERE/'qualification').exists()
    assert os.getuid() == 1000 and len(sys.argv) == 2
    namespace = os.readlink('/proc/self/ns/net')
    assert namespace != sys.argv[1]
    links = subprocess.check_output(['ip','-brief','link'],text=True)
    assert len(links.splitlines()) == 1 and links.startswith('lo ') and 'DOWN' in links
    free = capacity()
    assert free['/home/rehearsal/results'] > 21*1024**3 and free['/mnt/d'] > 51*1024**3
    RUN.mkdir()
    record = {'started':now(),'uid':os.getuid(),'namespace':namespace,'parent_namespace':sys.argv[1],'links':links,'capacity_before':free,'commands':[],'observations':[],'completed':False,'input_sha256':inventory(HERE)}
    try:
        os.nice(10)
        for line in (PRIOR/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
            digest,relative = line.split(None,1)
            assert sha(PRIOR/relative) == digest
        record['prior_manifest_sha256'] = sha(PRIOR/'SHA256SUMS')
        prior = json.loads((PRIOR/'qualification/run.json').read_text(encoding='utf-8'))
        assert inventory(SOURCE) == prior['source_inventory']
        assert inventory(RETAINED/'node') == prior['build_source_inventory']
        for name,digest in prior['binary_sha256'].items():
            assert sha(RETAINED/'bin'/name) == digest
        record['binary_sha256'] = prior['binary_sha256']
        record['prior_cases_before'] = inventory(RETAINED/'cases')
        for name,evidence in prior['refusals'].items():
            assert inventory(RETAINED/'cases'/name/'efsn/chaindata') == evidence['cold_files_after']
        record['original_refusal_files_still_match'] = True
        env = {k:v for k,v in os.environ.items() if not k.startswith(('GO','FUSION_','F12_'))}
        env.update(GOMAXPROCS='1',GOPROXY='off',GOSUMDB='off',GOTOOLCHAIN='local')
        directory = RUN/'valid'
        execute('seed', ['timeout','--kill-after=10s','90s',str(RETAINED/'bin/seed-tests'),'-test.run=^TestPrepareRestoredStartup$','-test.v','-test.timeout=60s'],dict(env,FUSION_STARTUP_TEST_DIRECTORY=str(directory),FUSION_STARTUP_TEST_CASE='valid'))
        expected = json.loads((directory/'expected.json').read_text(encoding='utf-8'))
        record['expected_heads'] = expected
        profile = json.loads((directory/'profile.json').read_text(encoding='utf-8'))
        below = json.loads(json.dumps(profile))
        below['Anchor']['Number'],below['Anchor']['Hash'] = expected['child_height'],expected['child']
        (RUN/'below-anchor.json').write_text(json.dumps(below,indent=2)+'\n',encoding='utf-8')
        common_args = ['timeout','--kill-after=10s','45s',str(RETAINED/'bin/efsn'),'--config',str(RETAINED/'profile.toml'),'--datadir',str(directory),'--syncmode','full','--gcmode','archive','--networkid','32659','--cache','64','--maxpeers','0','--port','0','--nat','none','--nodiscover','--v5disc=false','--ipcdisable','--authrpc.port','0','--mine=false','--autobt=false','--usb=false']
        query = 'console.log("RESTOREDCLI "+JSON.stringify({head:eth.blockNumber,hash:eth.getBlock("latest").hash,mining:eth.mining,autoBuy:fsn.isAutoBuyTicket()}))'
        for phase,head in [('below-anchor','parent'),('restored','parent'),('advance','child'),('restarted','child')]:
            chosen = RUN/'below-anchor.json' if phase=='below-anchor' else directory/'profile.json'
            js = query
            if phase == 'advance':
                js = 'console.log("IMPORTED "+admin.importChain('+json.dumps(str(directory/'child.rlp'))+'));'+query
            output = execute(phase,common_args+['--exec',js,'console'],dict(env,FUSION_STARTUP_TEST_PROFILE=str(chosen)))
            entries = [json.loads(line.split('RESTOREDCLI ',1)[1]) for line in output.splitlines() if line.startswith('RESTOREDCLI ')]
            assert len(entries)==1 and entries[0]=={'head':expected[head+'_height'],'hash':expected[head],'mining':False,'autoBuy':False}, entries
            if phase == 'advance':
                assert 'IMPORTED true' in output
            record['observations'].append({'phase':phase,**entries[0]})
            save()
        assert inventory(SOURCE)==prior['source_inventory'] and inventory(RETAINED/'node')==prior['build_source_inventory']
        assert inventory(RETAINED/'cases')==record['prior_cases_before']
        assert inventory(HERE)==record['input_sha256']
        for name,digest in record['binary_sha256'].items():
            assert sha(RETAINED/'bin'/name)==digest
        record['final_fixture_inventory'] = inventory(directory)
        record['sources_binaries_prior_cases_unchanged'] = True
        record['completed'] = True
    except BaseException as exc:
        record['failure'] = repr(exc)
        raise
    finally:
        record['finished'] = now()
        record['capacity_after'] = capacity()
        save()
        shutil.copytree(RUN,HERE/'qualification',ignore=shutil.ignore_patterns('valid'))
