from pathlib import Path
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
from fixtures import create

HERE = Path(__file__).resolve().parent
RUN = Path('/home/rehearsal/results/restart-ticket-encoder-candidate-v2-2026-10-08')
SELECTED = Path('/home/rehearsal/results/restart-release-jwt-2026-10-04')
PRIOR = HERE.parent / 'restart-ticket-compression-2026-10-08'
STARTUP = HERE.parent / 'restart-genesis-startup-v2-2026-10-08'
ROOTS = {'old': Path('/opt/fusion-toolchain/go'), 'new': Path('/home/rehearsal/results/restart-release-selection-2026-10-04/toolchain/go')}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def inventory(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob('*')) if p.is_file() and '.f12-probe' not in p.parts}


def save():
    (RUN / 'run.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')


def execute(name, argv, cwd, env):
    entry = {'name': name, 'argv': argv, 'cwd': str(cwd), 'started': now()}
    with (RUN / (name+'.stdout.txt')).open('wb') as output, (RUN / (name+'.stderr.txt')).open('wb') as errors:
        entry['exit'] = subprocess.run(argv, cwd=cwd, env=env, stdout=output, stderr=errors).returncode
    entry['finished'] = now()
    record['commands'].append(entry)
    save()
    print(name, entry['exit'], flush=True)
    if entry['exit']:
        raise RuntimeError('command failed: ' + name)


if __name__ == '__main__':
    assert not RUN.exists() and not (HERE / 'qualification').exists()
    assert os.getuid() == 1000 and len(sys.argv) == 2
    assert sys.argv[1] != os.readlink('/proc/self/ns/net')
    links = subprocess.check_output(['ip', '-brief', 'link'], text=True)
    assert len(links.splitlines()) == 1 and links.startswith('lo ') and 'DOWN' in links
    capacity = {p: shutil.disk_usage(p).free for p in ['/home/rehearsal/results', '/mnt/d']}
    assert capacity['/home/rehearsal/results'] > 30*1024**3 and capacity['/mnt/d'] > 60*1024**3
    format_files = [HERE / name for name in ['encode.go', 'probe.go', 'stdlib_encoder.go', 'candidate_encoder.go']]
    subprocess.run([str(ROOTS['new']/'bin/gofmt'), '-w'] + [str(p) for p in format_files], check=True)
    RUN.mkdir()
    (RUN / 'bin').mkdir()
    (RUN / 'tmp').mkdir()
    record = {'started': now(), 'uid': os.getuid(), 'namespace': os.readlink('/proc/self/ns/net'), 'parent_namespace': sys.argv[1], 'links': links, 'capacity_bytes': capacity, 'commands': [], 'toolchains': {}, 'binary_sha256': {}, 'selected_inventory_sha256': {}, 'candidate_inventory': {}, 'cli_inspections': {}, 'input_sha256': {p.name: sha(p) for p in HERE.iterdir() if p.is_file()}}
    try:
        previous_record = json.loads((PRIOR / 'qualification/run.json').read_text(encoding='utf-8'))
        previous = previous_record['previous_manifest_sha256'].copy()
        previous[PRIOR.name] = sha(PRIOR / 'SHA256SUMS')
        previous['restart-ticket-encoder-candidate-2026-10-08'] = sha(HERE.parent / 'restart-ticket-encoder-candidate-2026-10-08/SHA256SUMS')
        for name, expected in previous.items():
            directory = HERE.parent / name
            assert sha(directory / 'SHA256SUMS') == expected
            for line in (directory / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
                digest, relative = line.split(None, 1)
                assert sha(directory / relative) == digest, (name, relative)
        record['previous_manifest_sha256'] = previous
        environments = {}
        for name, root in ROOTS.items():
            assert sha(root/'bin/go') == previous_record['toolchains'][name]['go_binary_sha256']
            env = os.environ.copy()
            for key in ['GODEBUG', 'GOEXPERIMENT', 'GOENV', 'GOFLAGS', 'GOOS', 'GOARCH', 'GO111MODULE', 'GOROOT']:
                env.pop(key, None)
            env.update(PATH=str(root/'bin')+':/usr/bin:/bin', GOENV='off', GOTOOLCHAIN='local', GOWORK='off', GOPROXY='off', GOSUMDB='off', GOFLAGS='-mod=readonly', CGO_ENABLED='1', GOAMD64='v1', GOMAXPROCS='2', GOCACHE='/home/rehearsal/.cache/go-build' if name=='old' else '/home/rehearsal/results/restart-release-selection-2026-10-04/repeat-cache', GOMODCACHE='/home/rehearsal/go/pkg/mod', GOTMPDIR=str(RUN/'tmp'), TMPDIR=str(RUN/'tmp'), PYTHONDONTWRITEBYTECODE='1')
            environments[name] = env
            record['toolchains'][name] = {'root': str(root), 'go_binary_sha256': sha(root/'bin/go'), 'go_env': json.loads(subprocess.check_output(['go', 'env', '-json'], cwd=SELECTED/'node', env=env, text=True))}
        base_inventories = {}
        for name in ['node', 'recovery']:
            pinned = HERE.parent / 'restart-release-jwt-2026-10-04' / (name+'-inventory.json')
            base_inventories[name] = json.loads(pinned.read_text(encoding='utf-8'))
            assert inventory(SELECTED / name) == base_inventories[name]
            record['selected_inventory_sha256'][name] = sha(pinned)
        execute('prepare', ['python3', str(HERE/'prepare.py')], SELECTED/'node', environments['new'])
        prepared = json.loads((HERE/'preparation.json').read_text(encoding='utf-8'))
        record['prepared_sha256'] = {relative: sha(HERE/relative) for relative in ['preparation.json', 'candidate.patch']}
        record['runtime_input_sha256'] = prepared['candidate_sha256']
        for name, origin in [('baseline','node'), ('node','node'), ('recovery','recovery')]:
            shutil.copytree(SELECTED/origin, RUN/name)
            assert inventory(RUN/name) == base_inventories[origin]
            if name != 'baseline':
                execute(name+'-patch-check', ['git', 'apply', '--check', str(HERE/'candidate.patch')], RUN/name, environments['new'])
                execute(name+'-patch-apply', ['git', 'apply', str(HERE/'candidate.patch')], RUN/name, environments['new'])
                expected = dict(base_inventories[origin], **prepared['candidate_sha256'])
                assert inventory(RUN/name) == expected
                record['candidate_inventory'][name] = expected
        create(RUN/'fixtures')
        record['fixture_sha256'] = inventory(RUN/'fixtures')
        for name in ['baseline', 'node']:
            folder = RUN/name/'.f12-probe'
            folder.mkdir()
            shutil.copyfile(HERE/'probe.go', folder/'main.go')
            shutil.copyfile(HERE/('candidate_encoder.go' if name=='node' else 'stdlib_encoder.go'), folder/'encoder.go')
        for mode, folder, compiler in [('old','baseline','old'), ('new','baseline','new'), ('candidate','node','new')]:
            source = RUN/folder
            env = environments[compiler]
            command = ['timeout', '--kill-after=20s', '7m', 'go', 'build', '-race', '-p=2', '-trimpath', '-buildvcs=false', '-o', str(RUN/'bin'/mode), str(source/'.f12-probe/main.go'), str(source/'.f12-probe/encoder.go')]
            execute(mode+'-build', command, source, env)
            record['binary_sha256'][mode] = sha(RUN/'bin'/mode)
            for kind, input_path in [('payloads',RUN/'fixtures/payloads'), ('tickets',PRIOR/'qualification/vectors'), ('expiry',RUN/'fixtures/expiry.json')]:
                execute(mode+'-'+kind, ['timeout', '--kill-after=10s', '2m', str(RUN/'bin'/mode), kind, str(input_path), str(RUN/(mode+'-'+kind))], source, env)
        for name, folder in [('efsn','node'), ('fsn-recovery','recovery')]:
            execute(name+'-build', ['timeout', '--kill-after=20s', '7m', 'go', 'build', '-p=2', '-trimpath', '-buildvcs=false', '-o', str(RUN/'bin'/name), './cmd/'+name], RUN/folder, environments['new'])
            record['binary_sha256'][name] = sha(RUN/'bin'/name)
            execute(name+'-build-info', ['go', 'version', '-m', str(RUN/'bin'/name)], RUN/folder, environments['new'])
        execute('recovery-help', [str(RUN/'bin/fsn-recovery'), '--help'], RUN/'recovery', environments['new'])
        inspector = RUN/'bin/inspector'
        execute('inspector-build', ['timeout', '--kill-after=20s', '7m', 'go', 'build', '-p=2', '-trimpath', '-buildvcs=false', '-o', str(inspector), str(STARTUP/'probe.go')], RUN/'node', environments['new'])
        record['binary_sha256']['inspector'] = sha(inspector)
        record['startup_input_sha256'] = {name: sha(STARTUP/name) for name in ['probe.go', 'profile.toml']}
        datadir = RUN/'cli-datadir'
        datadir.mkdir()
        console = 'console.log("F12CLI "+JSON.stringify({genesis:eth.getBlock(0),head:eth.blockNumber,network:net.version,mining:eth.mining,autoBuy:fsn.isAutoBuyTicket()}))'
        command = ['timeout', '--kill-after=10s', '45s', str(RUN/'bin/efsn'), '--config', str(STARTUP/'profile.toml'), '--datadir', str(datadir), '--syncmode', 'full', '--networkid', '32659', '--cache', '128', '--maxpeers', '0', '--port', '0', '--nat', 'none', '--nodiscover', '--v5disc=false', '--ipcdisable', '--authrpc.port', '0', '--mine=false', '--autobt=false', '--usb=false', '--exec', console, 'console']
        for phase in ['empty', 'restart']:
            execute('cli-'+phase, command, RUN/'node', environments['new'])
            before = inventory(datadir/'efsn/chaindata')
            execute('cli-'+phase+'-inspect', [str(inspector), str(datadir/'efsn/chaindata')], RUN/'node', environments['new'])
            after = inventory(datadir/'efsn/chaindata')
            assert before == after
            record['cli_inspections'][phase] = {'database_sha256': before, 'unchanged_after_inspection': True, 'restore_marker': (datadir/'efsn/restored.json').exists()}
        for name in ['node', 'recovery']:
            assert inventory(SELECTED/name) == base_inventories[name]
            assert inventory(RUN/name) == record['candidate_inventory'][name]
        assert inventory(RUN/'baseline') == base_inventories['node']
        record['source_inventories_unchanged'] = True
        record['completed'] = True
    except BaseException as exc:
        record['failure'] = repr(exc)
        raise
    finally:
        record['finished'] = now()
        record['remaining_bytes'] = {p: shutil.disk_usage(p).free for p in ['/home/rehearsal/results', '/mnt/d']}
        save()
        shutil.copytree(RUN, HERE/'qualification', ignore=shutil.ignore_patterns('bin', 'tmp', 'baseline', 'node', 'recovery', 'cli-datadir'))
