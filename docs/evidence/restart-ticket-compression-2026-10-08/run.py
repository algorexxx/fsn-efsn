from pathlib import Path
import datetime
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
RUN = Path('/home/rehearsal/results/restart-ticket-compression-2026-10-08')
SOURCE = Path('/home/rehearsal/results/restart-release-jwt-2026-10-04/node')
ROOTS = {'old': Path('/opt/fusion-toolchain/go'), 'new': Path('/home/rehearsal/results/restart-release-selection-2026-10-04/toolchain/go')}
PRIOR = HERE.parent / 'restart-genesis-startup-v2-2026-10-08'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def save():
    (RUN / 'run.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')


def execute(name, argv, env):
    entry = {'name': name, 'argv': argv, 'cwd': str(SOURCE), 'started': now()}
    with (RUN / (name + '.stdout.txt')).open('wb') as out, (RUN / (name + '.stderr.txt')).open('wb') as err:
        entry['exit'] = subprocess.run(argv, cwd=SOURCE, env=env, stdout=out, stderr=err).returncode
    entry['finished'] = now()
    record['commands'].append(entry)
    save()
    print(name, entry['exit'], flush=True)
    if entry['exit']:
        raise RuntimeError('command failed: ' + name)


def inventory(directory, phase):
    rows = []
    for file in sorted(directory.iterdir()):
        assert file.is_file() and not file.is_symlink(), str(file)
        stat = file.stat()
        rows.append([file.name, stat.st_size, stat.st_mtime_ns])
    data = (json.dumps(rows, separators=(',', ':')) + '\n').encode('utf-8')
    (RUN / ('backup-metadata.' + phase + '.json.gz')).write_bytes(gzip.compress(data, mtime=0))
    return {'files': len(rows), 'logical_bytes': sum(x[1] for x in rows), 'metadata_sha256': hashlib.sha256(data).hexdigest()}


if __name__ == '__main__':
    assert not RUN.exists() and not (HERE / 'qualification').exists()
    assert os.getuid() == 1000 and len(sys.argv) == 3
    assert sys.argv[1] != os.readlink('/proc/self/ns/net')
    backup = Path(sys.argv[2])
    mount = json.loads(subprocess.check_output(['findmnt', '-J', '-o', 'TARGET,OPTIONS', '-T', str(backup)], text=True))['filesystems'][0]
    assert mount['target'] == str(backup) and 'ro' in mount['options'].split(',')
    links = subprocess.check_output(['ip', '-brief', 'link'], text=True)
    assert len(links.splitlines()) == 1 and links.startswith('lo ') and 'DOWN' in links
    capacity = {p: shutil.disk_usage(p).free for p in ['/home/rehearsal/results', '/mnt/d']}
    assert capacity['/home/rehearsal/results'] > 30*1024**3 and capacity['/mnt/d'] > 60*1024**3
    subprocess.run([str(ROOTS['new'] / 'bin/gofmt'), '-w', str(HERE / 'probe.go')], check=True)
    RUN.mkdir()
    (RUN / 'bin').mkdir()
    (RUN / 'tmp').mkdir()
    record = {'started': now(), 'uid': os.getuid(), 'namespace': os.readlink('/proc/self/ns/net'), 'parent_namespace': sys.argv[1], 'mount': mount, 'backup_source': '/home/rehearsal/data/efsn/chaindata', 'links': links, 'capacity_bytes': capacity, 'source': str(SOURCE), 'input_sha256': {name: sha(HERE / name) for name in ['.gitattributes', 'spec.md', 'probe.go', 'run.py', 'launch.py']}, 'commands': [], 'toolchains': {}, 'binary_sha256': {}}
    try:
        previous = json.loads((PRIOR / 'qualification/run.json').read_text(encoding='utf-8'))['previous_manifest_sha256']
        previous[PRIOR.name] = sha(PRIOR / 'SHA256SUMS')
        for name, expected in previous.items():
            directory = HERE.parent / name
            assert sha(directory / 'SHA256SUMS') == expected
            for line in (directory / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
                digest, relative = line.split(None, 1)
                assert sha(directory / relative) == digest, (name, relative)
        record['previous_manifest_sha256'] = previous
        record['source_sha256'] = {f.relative_to(SOURCE).as_posix(): sha(f) for f in sorted(SOURCE.rglob('*')) if f.is_file() and (f.suffix in ['.go', '.c', '.h', '.s'] or f.name in ['go.mod', 'go.sum'])}
        inherited = json.loads((PRIOR / 'qualification/run.json').read_text(encoding='utf-8'))['source_sha256']
        for relative, expected in inherited.items():
            assert sha(SOURCE / relative) == expected, relative
        record['preservation_marker'] = Path('/home/rehearsal/results/backup-copy-2026-09-23/verified.txt').read_text(encoding='utf-8')
        record['backup_before'] = inventory(backup, 'before')
        environments = {}
        for name, root in ROOTS.items():
            env = os.environ.copy()
            for key in ['GODEBUG', 'GOEXPERIMENT', 'GOENV', 'GOFLAGS', 'GOOS', 'GOARCH', 'GO111MODULE', 'GOROOT']:
                env.pop(key, None)
            env.update(PATH=str(root/'bin')+':/usr/bin:/bin', GOENV='off', GOTOOLCHAIN='local', GOWORK='off', GOPROXY='off', GOSUMDB='off', GOFLAGS='-mod=readonly', CGO_ENABLED='1', GOAMD64='v1', GOMAXPROCS='2', GOCACHE='/home/rehearsal/.cache/go-build' if name=='old' else '/home/rehearsal/results/restart-release-selection-2026-10-04/repeat-cache', GOMODCACHE='/home/rehearsal/go/pkg/mod', GOTMPDIR=str(RUN/'tmp'), TMPDIR=str(RUN/'tmp'))
            environments[name] = env
            record['toolchains'][name] = {'root': str(root), 'go_binary_sha256': sha(root/'bin/go'), 'go_env': json.loads(subprocess.check_output(['go', 'env', '-json'], cwd=SOURCE, env=env, text=True)), 'compression_source_sha256': {f.relative_to(root).as_posix(): sha(f) for folder in ['src/compress/flate', 'src/compress/gzip'] for f in sorted((root/folder).glob('*.go'))}}
        old_files = {p.name: p for p in (ROOTS['old'] / 'src/compress/flate').glob('*.go') if not p.name.endswith('_test.go')}
        new_files = {p.name: p for p in (ROOTS['new'] / 'src/compress/flate').glob('*.go') if not p.name.endswith('_test.go')}
        assert len(old_files) == 7 and len(new_files) == 16 and set(old_files) <= set(new_files)
        overlay = {'Replace': {str(path): str(old_files[name]) if name in old_files else '' for name, path in sorted(new_files.items())}}
        overlay_path = RUN / 'frozen-flate-overlay.json'
        overlay_path.write_text(json.dumps(overlay, indent=2) + '\n', encoding='utf-8')
        record['overlay_sha256'] = sha(overlay_path)
        save()
        for name in ['old', 'new', 'frozen']:
            env = environments['old' if name == 'old' else 'new']
            argv = ['timeout', '--kill-after=20s', '7m', 'go', 'build', '-p=2', '-trimpath', '-buildvcs=false']
            if name == 'frozen':
                argv += ['-overlay', str(overlay_path)]
            argv += ['-o', str(RUN/'bin'/name), str(HERE/'probe.go')]
            execute(name+'-build', argv, env)
            record['binary_sha256'][name] = sha(RUN/'bin'/name)
        execute('export', ['timeout', '--kill-after=10s', '2m', str(RUN/'bin/new'), 'export', str(backup), str(RUN/'vectors')], environments['new'])
        for name in ['old', 'new', 'frozen']:
            execute(name+'-compare', ['timeout', '--kill-after=10s', '2m', str(RUN/'bin'/name), 'compare', str(RUN/'vectors'), str(RUN/name)], environments['old' if name == 'old' else 'new'])
        record['completed'] = True
    except BaseException as exc:
        record['failure'] = repr(exc)
        raise
    finally:
        record['backup_after'] = inventory(backup, 'after')
        record['backup_metadata_unchanged'] = record.get('backup_before') == record['backup_after']
        record['finished'] = now()
        save()
        shutil.copytree(RUN, HERE/'qualification', ignore=shutil.ignore_patterns('bin', 'tmp'))
