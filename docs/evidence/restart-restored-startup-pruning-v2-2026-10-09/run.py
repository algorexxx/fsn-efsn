from pathlib import Path
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent/'restart-restored-startup-candidate-2026-10-09'
RETAINED = Path('/home/rehearsal/results')/PRIOR.name
RUN = Path('/home/rehearsal/results')/HERE.name
GO = Path('/home/rehearsal/results/restart-release-selection-2026-10-04/toolchain/go/bin/go')
HELPER = HERE.parent/'restart-restored-startup-positive-2026-10-09/run.py'
spec = importlib.util.spec_from_file_location('retained_positive_helpers', HELPER)
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)


def execute(name, argv, env):
    output = h.execute(name, argv, env)
    size = sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file())
    record['commands'][-1]['output_bytes_after'] = size
    h.save()
    assert size < 256*1024**2, 'small fixture exceeded 256 MiB'
    return output


if __name__ == '__main__':
    assert not RUN.exists() and not (HERE/'qualification').exists()
    assert os.getuid() == 1000 and len(sys.argv) == 2
    namespace = os.readlink('/proc/self/ns/net')
    links = subprocess.check_output(['ip','-brief','link'],text=True)
    assert namespace != sys.argv[1]
    assert len(links.splitlines()) == 1 and links.startswith('lo ') and 'DOWN' in links
    free = h.capacity()
    assert free['/home/rehearsal/results'] > 21*1024**3 and free['/mnt/d'] > 51*1024**3
    RUN.mkdir()
    (RUN/'tmp').mkdir()
    record = {'started':h.now(),'uid':os.getuid(),'namespace':namespace,'parent_namespace':sys.argv[1],'links':links,'capacity_before':free,'commands':[],'observations':[],'completed':False,'input_sha256':h.inventory(HERE),'helper_sha256':h.sha(HELPER)}
    h.RUN, h.record = RUN, record
    try:
        os.nice(10)
        for line in (PRIOR/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
            digest, relative = line.split(None,1)
            assert h.sha(PRIOR/relative) == digest
        prior = json.loads((PRIOR/'qualification/run.json').read_text(encoding='utf-8'))
        assert h.inventory(RETAINED/'node') == prior['build_source_inventory']
        assert h.sha(RETAINED/'bin/efsn') == prior['binary_sha256']['efsn']
        assert h.sha(GO) == prior['go_binary_sha256']
        record['prior_manifest_sha256'] = h.sha(PRIOR/'SHA256SUMS')
        record['cli_sha256'] = prior['binary_sha256']['efsn']
        record['go_binary_sha256'] = prior['go_binary_sha256']
        record['source_inventory'] = prior['build_source_inventory']
        env = {k:v for k,v in os.environ.items() if not k.startswith(('GO','FUSION_','F12_'))}
        env.update(PATH=str(GO.parent)+':/usr/bin:/bin',GOENV='off',GOTOOLCHAIN='local',GOWORK='off',GOPROXY='off',GOSUMDB='off',GOFLAGS='-mod=readonly',CGO_ENABLED='1',GOAMD64='v1',GOMAXPROCS='1',GOCACHE='/home/rehearsal/results/restart-release-selection-2026-10-04/repeat-cache',GOMODCACHE='/home/rehearsal/go/pkg/mod',GOTMPDIR=str(RUN/'tmp'),TMPDIR=str(RUN/'tmp'),PYTHONDONTWRITEBYTECODE='1')
        record['go_env'] = json.loads(subprocess.check_output([str(GO),'env','-json'],cwd=RETAINED/'node',env=env,text=True))
        overlay = {'Replace':{str(RETAINED/'node/tests/restart/seed_test.go'):str(HERE/'seed_test.go')}}
        (RUN/'overlay.json').write_text(json.dumps(overlay,indent=2)+'\n',encoding='utf-8')
        execute('seed-build',['timeout','--kill-after=10s','5m',str(GO),'test','-p=1','-trimpath','-buildvcs=false','-overlay='+str(RUN/'overlay.json'),'-c','-o',str(RUN/'seed-tests'),'.'],env)
        record['seed_binary_sha256'] = h.sha(RUN/'seed-tests')
        directory = RUN/'valid'
        env['FUSION_STARTUP_TEST_DIRECTORY'] = str(directory)
        execute('seed',['timeout','--kill-after=10s','90s',str(RUN/'seed-tests'),'-test.run=^TestPreparePruningStartup$','-test.v','-test.timeout=60s'],env)
        expected = json.loads((directory/'expected.json').read_text(encoding='utf-8'))
        record['expected'] = expected
        assert expected['ancestor_count'] == 130 and expected['parent']['head'] == 129 and expected['child']['head'] == 130
        env['FUSION_STARTUP_TEST_PROFILE'] = str(directory/'profile.json')
        args = ['timeout','--kill-after=10s','45s',str(RETAINED/'bin/efsn'),'--config',str(RETAINED/'profile.toml'),'--datadir',str(directory),'--syncmode','full','--gcmode','full','--networkid','32659','--cache','64','--maxpeers','0','--port','0','--nat','none','--nodiscover','--v5disc=false','--ipcdisable','--authrpc.port','0','--mine=false','--autobt=false','--usb=false']
        query = 'var b=eth.getBlock("latest");console.log("RESTOREDCLI "+JSON.stringify({head:b.number,hash:b.hash,root:b.stateRoot,tickets:b.mixHash,mining:eth.mining,autoBuy:fsn.isAutoBuyTicket()}))'
        for phase, head in [('restored','parent'),('advance','child'),('restarted','child')]:
            js = query if phase != 'advance' else 'console.log("IMPORTED "+admin.importChain('+json.dumps(str(directory/'child.rlp'))+'));'+query
            output = execute(phase,args+['--exec',js,'console'],env)
            errors = (RUN/(phase+'.stderr.txt')).read_text(encoding='utf-8')
            entries = [json.loads(line.split('RESTOREDCLI ',1)[1]) for line in output.splitlines() if line.startswith('RESTOREDCLI ')]
            want = dict(expected[head],mining=False,autoBuy=False)
            assert entries == [want], entries
            assert 'panic:' not in errors and 'Blockchain manager stopped' in errors
            assert errors.index('readonly=true') < errors.index('Initialising Ethereum protocol')
            writes = [int(n.replace(',','')) for n in re.findall(r'Writing cached state to disk[^\n]*block=([0-9,]+)',errors)]
            assert writes == [want['head'],want['head']-1,want['head']-127], writes
            assert 'Failed to commit recent state trie' not in errors and 'Dangling trie nodes' not in errors
            if phase == 'advance': assert 'IMPORTED true' in output
            record['observations'].append({'phase':phase,**want,'shutdown_heights':writes})
            h.save()
        record['cold_files_before'] = h.inventory(directory/'efsn/chaindata')
        output = execute('cold',['timeout','--kill-after=10s','45s',str(RUN/'seed-tests'),'-test.run=^TestInspectPruningStartup$','-test.v','-test.timeout=30s'],env)
        cold = [json.loads(line.split('PRUNINGCOLD ',1)[1]) for line in output.splitlines() if 'PRUNINGCOLD ' in line]
        assert len(cold)==1 and [v['head'] for v in cold[0]] == [130,129,3]
        assert cold[0][0]==expected['child'] and cold[0][1]==expected['parent']
        record['cold_observations'] = cold[0]
        record['cold_files_after'] = h.inventory(directory/'efsn/chaindata')
        assert record['cold_files_before']==record['cold_files_after']
        assert h.inventory(RETAINED/'node') == record['source_inventory']
        assert h.sha(RETAINED/'bin/efsn')==record['cli_sha256'] and h.sha(RUN/'seed-tests')==record['seed_binary_sha256']
        assert h.inventory(HERE)==record['input_sha256'] and h.sha(HELPER)==record['helper_sha256']
        record['sources_binaries_inputs_unchanged'] = True
        record['completed'] = True
    except BaseException as exc:
        record['failure'] = repr(exc)
        raise
    finally:
        record['finished'] = h.now()
        record['capacity_after'] = h.capacity()
        h.save()
        shutil.copytree(RUN,HERE/'qualification',ignore=shutil.ignore_patterns('valid','seed-tests','tmp'))
