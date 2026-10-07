from pathlib import Path
import datetime
import difflib
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
RUN = Path('/home/rehearsal/results/restart-state-rollback-candidate-2026-10-07-v2')
TOOLCHAIN = Path('/home/rehearsal/results/restart-release-selection-2026-10-04/toolchain/go')
CACHE = Path('/home/rehearsal/results/restart-release-selection-2026-10-04/repeat-cache')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


if __name__ == '__main__':
    assert not RUN.exists(), 'Use a fresh run directory; do not overwrite evidence.'
    assert not (HERE / 'candidate-v2.patch').exists(), 'Candidate already frozen.'
    capacity = {p: shutil.disk_usage(p).free for p in ['/home/rehearsal/results', '/mnt/d']}
    assert capacity['/home/rehearsal/results'] > 30 * 1024**3 and capacity['/mnt/d'] > 60 * 1024**3, capacity
    assert len(sys.argv) == 2 and sys.argv[1].startswith('net:[') and os.readlink('/proc/self/ns/net') != sys.argv[1], 'A private network namespace is required for this run.'
    manifest = json.loads((HERE / 'base-inputs.json').read_text(encoding='utf-8'))
    inputs = sorted((HERE / 'inputs').rglob('*.go'))
    subprocess.run([str(TOOLCHAIN / 'bin/gofmt'), '-w', *map(str, inputs)], check=True)
    patch = []
    for src in inputs:
        relative = src.relative_to(HERE / 'inputs').as_posix()
        original = b''
        if relative in manifest['files']:
            entry = manifest['files'][relative]
            for label in entry['trees']:
                base = Path(manifest['trees'][label]['path']) / relative
                assert sha(base) == entry['sha256'], str(base)
                original = base.read_bytes()
        before = original.decode('utf-8').splitlines(keepends=True)
        after = src.read_text(encoding='utf-8').splitlines(keepends=True)
        patch.extend(difflib.unified_diff(before, after, fromfile='a/' + relative if original else '/dev/null', tofile='b/' + relative))
    (HERE / 'candidate-v2.patch').write_text(''.join(patch), encoding='utf-8', newline='\n')
    RUN.mkdir()
    (RUN / 'tmp').mkdir()
    (RUN / 'bin').mkdir()
    env = os.environ.copy()
    for key in ['GODEBUG', 'GOEXPERIMENT', 'GOENV', 'GOFLAGS', 'GOOS', 'GOARCH']:
        env.pop(key, None)
    env.update(PATH=str(TOOLCHAIN / 'bin') + ':/usr/bin:/bin', GOENV='off', GOTOOLCHAIN='local', GOWORK='off', GOPROXY='off', GOSUMDB='off', GOFLAGS='-mod=readonly', CGO_ENABLED='1', GOAMD64='v1', GOMAXPROCS='2', GOCACHE=str(CACHE), GOMODCACHE='/home/rehearsal/go/pkg/mod', GOTMPDIR=str(RUN / 'tmp'))
    record = {'started': now(), 'capacity_bytes': capacity, 'network_namespace': os.readlink('/proc/self/ns/net'), 'parent_network_namespace': sys.argv[1], 'links': subprocess.check_output(['ip', '-brief', 'link'], text=True), 'go_version': subprocess.check_output([str(TOOLCHAIN / 'bin/go'), 'version'], text=True), 'uid': os.getuid(), 'go_env_by_selection': {label: json.loads(subprocess.check_output(['go', 'env', '-json'], cwd=tree['path'], env=env, text=True)) for label, tree in manifest['trees'].items()}, 'input_sha256': {p.relative_to(HERE).as_posix(): sha(p) for p in inputs}, 'patch_sha256': sha(HERE / 'candidate-v2.patch'), 'commands': []}
    write_json(RUN / 'run.json', record)
    for label, tree in manifest['trees'].items():
        base = Path(tree['path'])
        assert sha(base / 'go.mod') == tree['go.mod'] and sha(base / 'go.sum') == tree['go.sum'], label
        replacements = {}
        for src in inputs:
            relative = src.relative_to(HERE / 'inputs').as_posix()
            if relative in manifest['files'] and label not in manifest['files'][relative]['trees']:
                continue
            replacements[str(base / relative)] = str(src)
        write_json(RUN / (label + '-overlay.json'), {'Replace': replacements})
    commands = [
        ('params', 'node', ['test', '-race', '-p=2', '-count=1', '-timeout=2m', '-v', './params']),
        ('build-node', 'node', ['build', '-p=2', '-o', str(RUN / 'bin/efsn'), './cmd/efsn']),
        ('build-recovery', 'recovery', ['build', '-p=2', '-o', str(RUN / 'bin/fsn-recovery'), './cmd/fsn-recovery']),
    ]
    for name, label, args in commands:
        cmd = ['timeout', '--kill-after=20s', '7m', 'go', args[0], '-overlay=' + str(RUN / (label + '-overlay.json')), *args[1:]]
        started = now()
        with (RUN / (name + '.txt')).open('w', encoding='utf-8') as out:
            result = subprocess.run(cmd, cwd=manifest['trees'][label]['path'], env=env, stdout=out, stderr=subprocess.STDOUT)
        record['commands'].append({'name': name, 'cwd': manifest['trees'][label]['path'], 'argv': cmd, 'started': started, 'finished': now(), 'exit': result.returncode})
        write_json(RUN / 'run.json', record)
        print(name, 'exit', result.returncode, flush=True)
        if result.returncode != 0:
            break
        assert shutil.disk_usage('/home/rehearsal/results').free > 30 * 1024**3, 'Stop below capacity floor.'
    record['finished'] = now()
    record['binary_sha256'] = {p.name: sha(p) for p in (RUN / 'bin').iterdir() if p.is_file()}
    write_json(RUN / 'run.json', record)
    output = HERE / 'qualification-v2'
    output.mkdir()
    for p in RUN.iterdir():
        if p.is_file():
            shutil.copyfile(p, output / p.name)
    for relative, entry in manifest['files'].items():
        for label in entry['trees']:
            assert sha(Path(manifest['trees'][label]['path']) / relative) == entry['sha256'], relative
    sys.exit(record['commands'][-1]['exit'])
