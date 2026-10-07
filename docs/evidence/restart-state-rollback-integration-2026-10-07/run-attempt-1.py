from pathlib import Path
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
CANDIDATE = HERE.parent / 'restart-state-rollback-candidate-2026-10-07'
RUN = Path('/home/rehearsal/results/restart-state-rollback-integration-2026-10-07')
TOOLCHAIN = Path('/home/rehearsal/results/restart-release-selection-2026-10-04/toolchain/go')
CACHE = Path('/home/rehearsal/results/restart-release-selection-2026-10-04/repeat-cache')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


if __name__ == '__main__':
    assert not RUN.exists(), 'Use a fresh directory; preserve prior evidence.'
    assert os.getuid() == 1000
    assert len(sys.argv) == 2 and sys.argv[1].startswith('net:[') and os.readlink('/proc/self/ns/net') != sys.argv[1]
    capacity = {p: shutil.disk_usage(p).free for p in ['/home/rehearsal/results', '/mnt/d']}
    assert capacity['/home/rehearsal/results'] > 30 * 1024**3 and capacity['/mnt/d'] > 60 * 1024**3
    for line in (CANDIDATE / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        expected, relative = line.split(None, 1)
        assert sha(CANDIDATE / relative) == expected, relative
    manifest = json.loads((CANDIDATE / 'base-inputs.json').read_text(encoding='utf-8'))
    source = Path(manifest['trees']['recovery']['path'])
    for name in ['go.mod', 'go.sum']:
        assert sha(source / name) == manifest['trees']['recovery'][name]
    for relative, entry in manifest['files'].items():
        if 'recovery' in entry['trees']:
            assert sha(source / relative) == entry['sha256'], relative
    tests = [HERE / 'startup_recovery_test.go', HERE / 'config_vectors_test.go']
    subprocess.run([str(TOOLCHAIN / 'bin/gofmt'), '-w', *map(str, tests)], check=True)
    overlay = json.loads((CANDIDATE / 'qualification-v2/recovery-overlay.json').read_text(encoding='utf-8'))
    for path in tests:
        overlay['Replace'][str(source / 'internal/recovery' / ('f11_' + path.name))] = str(path)
    RUN.mkdir()
    (RUN / 'tmp').mkdir()
    (RUN / 'overlay.json').write_text(json.dumps(overlay, indent=2) + '\n', encoding='utf-8')
    env = os.environ.copy()
    for key in ['GODEBUG', 'GOEXPERIMENT', 'GOENV', 'GOFLAGS', 'GOOS', 'GOARCH']:
        env.pop(key, None)
    env.update(PATH=str(TOOLCHAIN / 'bin') + ':/usr/bin:/bin', GOENV='off', GOTOOLCHAIN='local', GOWORK='off', GOPROXY='off', GOSUMDB='off', GOFLAGS='-mod=readonly', CGO_ENABLED='1', GOAMD64='v1', GOMAXPROCS='2', GOCACHE=str(CACHE), GOMODCACHE='/home/rehearsal/go/pkg/mod', GOTMPDIR=str(RUN / 'tmp'), TMPDIR=str(RUN / 'tmp'))
    cmd = ['timeout', '--kill-after=20s', '7m', 'go', 'test', '-overlay=' + str(RUN / 'overlay.json'), '-race', '-p=2', '-count=1', '-timeout=2m', '-run', '^TestF11', '-v', './internal/recovery']
    record = {'started': now(), 'capacity_bytes': capacity, 'uid': os.getuid(), 'network_namespace': os.readlink('/proc/self/ns/net'), 'parent_network_namespace': sys.argv[1], 'links': subprocess.check_output(['ip', '-brief', 'link'], text=True), 'source': str(source), 'candidate_commit': '8357c5fe', 'candidate_manifest_sha256': sha(CANDIDATE / 'SHA256SUMS'), 'overlay_input_sha256': {k: sha(Path(v)) for k, v in overlay['Replace'].items()}, 'go_env': json.loads(subprocess.check_output(['go', 'env', '-json'], cwd=source, env=env, text=True)), 'argv': cmd}
    (RUN / 'run.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    with (RUN / 'tests.txt').open('w', encoding='utf-8') as out:
        result = subprocess.run(cmd, cwd=source, env=env, stdout=out, stderr=subprocess.STDOUT)
    record.update(exit=result.returncode, finished=now(), remaining_bytes=shutil.disk_usage('/home/rehearsal/results').free)
    (RUN / 'run.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    for relative, entry in manifest['files'].items():
        if 'recovery' in entry['trees']:
            assert sha(source / relative) == entry['sha256'], relative
    output = HERE / 'qualification'
    output.mkdir()
    for path in RUN.iterdir():
        if path.is_file():
            shutil.copyfile(path, output / path.name)
    print('integration exit', result.returncode)
    sys.exit(result.returncode)
