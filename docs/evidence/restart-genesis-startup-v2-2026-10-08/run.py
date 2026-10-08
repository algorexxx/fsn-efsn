from pathlib import Path
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
RUN = Path('/home/rehearsal/results/restart-genesis-startup-v2-2026-10-08')
SELECTED = Path('/home/rehearsal/results/restart-release-jwt-2026-10-04')
SOURCE = SELECTED / 'node'
CANDIDATE = HERE.parent / 'restart-state-rollback-candidate-2026-10-07'
API = HERE.parent / 'restart-state-rollback-api-2026-10-08'
GO = Path('/home/rehearsal/results/restart-release-selection-2026-10-04/toolchain/go')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def inventory(path):
    return {p.relative_to(path).as_posix(): sha(p) for p in sorted(path.rglob('*')) if p.is_file()}


def execute(name, command, record, env):
    entry = {'name': name, 'argv': command, 'started': now()}
    with (RUN / (name + '.stdout.txt')).open('wb') as stdout, (RUN / (name + '.stderr.txt')).open('wb') as stderr:
        entry['exit'] = subprocess.run(command, cwd=SOURCE, env=env, stdout=stdout, stderr=stderr).returncode
    entry['finished'] = now()
    record['commands'].append(entry)
    (RUN / 'run.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(name, entry['exit'], flush=True)
    return entry['exit'] == 0


if __name__ == '__main__':
    assert not RUN.exists(), 'Preserve earlier evidence; use a new directory.'
    assert os.getuid() == 1000 and len(sys.argv) == 2
    namespace = os.readlink('/proc/self/ns/net')
    assert namespace != sys.argv[1] and namespace.startswith('net:[')
    capacity = {p: shutil.disk_usage(p).free for p in ['/home/rehearsal/results', '/mnt/d']}
    assert capacity['/home/rehearsal/results'] > 30 * 1024**3 and capacity['/mnt/d'] > 60 * 1024**3
    prior = read_json(API / 'qualification/run.json')['previous_manifest_sha256']
    prior[API.name] = sha(API / 'SHA256SUMS')
    prior['restart-genesis-startup-2026-10-08'] = sha(HERE.parent / 'restart-genesis-startup-2026-10-08/SHA256SUMS')
    for name, expected in prior.items():
        directory = HERE.parent / name
        assert sha(directory / 'SHA256SUMS') == expected
        for line in (directory / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
            digest, relative = line.split(None, 1)
            assert sha(directory / relative) == digest, (name, relative)
    inputs = read_json(CANDIDATE / 'base-inputs.json')
    for relative, item in inputs['files'].items():
        if 'node' in item['trees']:
            assert sha(SOURCE / relative) == item['sha256'], relative
    candidate_record = read_json(CANDIDATE / 'qualification-v2/run.json')
    binaries = {
        'baseline': SELECTED / 'bin/efsn',
        'candidate': Path('/home/rehearsal/results/restart-state-rollback-candidate-2026-10-07-v2/bin/efsn'),
    }
    expected_binary = {
        'baseline': read_json(HERE.parent / 'restart-release-jwt-2026-10-04/acceptance.json')['binary_sha256']['efsn'],
        'candidate': candidate_record['binary_sha256']['efsn'],
    }
    for selection, binary in binaries.items():
        assert sha(binary) == expected_binary[selection]
    subprocess.run([str(GO / 'bin/gofmt'), '-w', str(HERE / 'probe.go')], check=True)
    RUN.mkdir()
    (RUN / 'bin').mkdir()
    (RUN / 'tmp').mkdir()
    env = os.environ.copy()
    for key in ['GODEBUG', 'GOEXPERIMENT', 'GOENV', 'GOFLAGS', 'GOOS', 'GOARCH']:
        env.pop(key, None)
    env.update(PATH=str(GO / 'bin') + ':/usr/bin:/bin', GOENV='off', GOTOOLCHAIN='local', GOWORK='off', GOPROXY='off', GOSUMDB='off', GOFLAGS='-mod=readonly', CGO_ENABLED='1', GOAMD64='v1', GOMAXPROCS='2', GOCACHE='/home/rehearsal/results/restart-release-selection-2026-10-04/repeat-cache', GOMODCACHE='/home/rehearsal/go/pkg/mod', GOTMPDIR=str(RUN / 'tmp'), TMPDIR=str(RUN / 'tmp'))
    paths = set(read_json(API / 'qualification/run.json')['source_sha256'])
    paths.remove('internal/recovery/chain.go')
    paths.update(['cmd/efsn/main.go', 'cmd/efsn/config.go', 'cmd/utils/flags.go', 'core/genesis_alloc.go', 'common/fsntypes.go', 'common/fsnparams.go'])
    source_hashes = {path: sha(SOURCE / path) for path in sorted(paths) if (SOURCE / path).is_file()}
    record = {'started': now(), 'capacity_bytes': capacity, 'uid': os.getuid(), 'network_namespace': namespace, 'parent_network_namespace': sys.argv[1], 'links': subprocess.check_output(['ip', '-brief', 'link'], text=True), 'source': str(SOURCE), 'source_sha256': source_hashes, 'previous_manifest_sha256': prior, 'binary_sha256': expected_binary, 'input_sha256': {p.name: sha(p) for p in HERE.iterdir() if p.is_file()}, 'go_env': json.loads(subprocess.check_output(['go', 'env', '-json'], cwd=SOURCE, env=env, text=True)), 'commands': [], 'observations': {}}
    unexpected = False
    for selection, binary in binaries.items():
        helper = RUN / 'bin' / (selection + '-probe')
        overlay = read_json(CANDIDATE / 'qualification-v2/node-overlay.json') if selection == 'candidate' else {'Replace': {}}
        retained = RUN / (selection + '-overlay.json')
        retained.write_text(json.dumps(overlay, indent=2) + '\n', encoding='utf-8')
        record.setdefault('overlay_sha256', {})[selection] = {logical: sha(Path(physical)) for logical, physical in overlay['Replace'].items()}
        command = ['timeout', '--kill-after=20s', '7m', 'go', 'build', '-p=2', '-trimpath', '-buildvcs=false', '-overlay=' + str(retained), '-o', str(helper), str(HERE / 'probe.go')]
        if not execute(selection + '-build', command, record, env):
            unexpected = True
            break
        record.setdefault('helper_sha256', {})[selection] = sha(helper)
        if not execute(selection + '-construct', [str(helper)], record, env):
            unexpected = True
            break
        data = RUN / (selection + '-empty-datadir')
        data.mkdir()
        console = 'console.log("F12CLI "+JSON.stringify({genesis:eth.getBlock(0),head:eth.blockNumber,network:net.version,mining:eth.mining,autoBuy:fsn.isAutoBuyTicket()}))'
        command = ['timeout', '--kill-after=10s', '45s', str(binary), '--config', str(HERE / 'profile.toml'), '--datadir', str(data), '--syncmode', 'full', '--networkid', '32659', '--cache', '128', '--maxpeers', '0', '--port', '0', '--nat', 'none', '--nodiscover', '--v5disc=false', '--ipcdisable', '--authrpc.port', '0', '--mine=false', '--autobt=false', '--usb=false', '--exec', console, 'console']
        for phase in ['empty', 'restart']:
            if not execute(selection + '-' + phase, command, record, env):
                unexpected = True
                break
            database = data / 'efsn/chaindata'
            before = inventory(database)
            if not execute(selection + '-' + phase + '-inspect', [str(helper), str(database)], record, env):
                unexpected = True
                break
            after = inventory(database)
            record['observations'][selection + '-' + phase] = {'database_files_before': before, 'database_files_after': after, 'readonly_bytes_unchanged': before == after, 'restored_marker_present': (data / 'efsn/restored.json').exists(), 'datadir_bytes': sum(p.stat().st_size for p in data.rglob('*') if p.is_file())}
            if before != after:
                unexpected = True
                break
        if unexpected:
            break
    record.update(finished=now(), unexpected_result=unexpected, remaining_bytes=shutil.disk_usage(RUN).free)
    (RUN / 'run.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    shutil.copytree(RUN, HERE / 'qualification', ignore=shutil.ignore_patterns('bin', 'tmp', '*-empty-datadir'))
    sys.exit(1 if unexpected else 0)
