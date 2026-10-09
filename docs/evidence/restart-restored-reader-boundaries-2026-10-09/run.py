from pathlib import Path
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUN = Path('/home/rehearsal/results') / HERE.name
PRIOR = HERE.parent / 'restart-ticket-encoder-candidate-v2-2026-10-08'
SOURCE = Path('/home/rehearsal/results') / PRIOR.name / 'recovery'
GO = Path('/home/rehearsal/results/restart-release-selection-2026-10-04/toolchain/go/bin/go')
FIXTURE = REPO / 'internal/recovery/reader_test.go'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob('*')) if p.is_file() and '.f12-probe' not in p.parts}


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def capacity():
    return {p: shutil.disk_usage(p).free for p in ['/home/rehearsal/results', '/mnt/d']}


def save():
    (RUN / 'run.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')


def execute(name, argv, env):
    entry = {'name': name, 'argv': argv, 'cwd': str(SOURCE), 'started': now()}
    with (RUN / (name + '.stdout.txt')).open('wb') as output, (RUN / (name + '.stderr.txt')).open('wb') as errors:
        entry['exit'] = subprocess.run(argv, cwd=SOURCE, env=env, stdout=output, stderr=errors).returncode
    entry['finished'] = now()
    record['commands'].append(entry)
    save()
    print(name, entry['exit'], flush=True)
    assert entry['exit'] == 0, name


if __name__ == '__main__':
    assert not RUN.exists() and not (HERE / 'qualification').exists()
    assert os.getuid() == 1000 and len(sys.argv) == 2
    namespace = os.readlink('/proc/self/ns/net')
    assert sys.argv[1] != namespace
    links = subprocess.check_output(['ip', '-brief', 'link'], text=True)
    assert len(links.splitlines()) == 1 and links.startswith('lo ') and 'DOWN' in links
    initial_capacity = capacity()
    assert initial_capacity['/home/rehearsal/results'] > 21 * 1024**3
    assert initial_capacity['/mnt/d'] > 51 * 1024**3
    RUN.mkdir()
    (RUN / 'bin').mkdir()
    (RUN / 'tmp').mkdir()
    record = {'started': now(), 'uid': os.getuid(), 'namespace': namespace, 'parent_namespace': sys.argv[1], 'links': links, 'capacity_before': initial_capacity, 'commands': [], 'completed': False}
    try:
        os.nice(10)
        record['nice'] = os.nice(0)
        record['investigation_commit'] = subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip()
        assert record['investigation_commit'].startswith('3d754b61')
        record['input_sha256'] = {p.relative_to(REPO).as_posix(): sha(p) for p in [HERE/'run.py', HERE/'launch.py', FIXTURE]}
        checked = 0
        for line in (PRIOR / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
            digest, relative = line.split(None, 1)
            assert sha(PRIOR / relative) == digest, relative
            checked += 1
        record['prior_manifest_sha256'] = sha(PRIOR / 'SHA256SUMS')
        record['prior_files_verified'] = checked
        prior = json.loads((PRIOR / 'qualification/run.json').read_text(encoding='utf-8'))
        expected_source = prior['candidate_inventory']['recovery']
        assert inventory(SOURCE) == expected_source
        record['source'] = str(SOURCE)
        record['source_inventory'] = expected_source
        assert sha(GO) == prior['toolchains']['new']['go_binary_sha256']
        record['go_binary_sha256'] = sha(GO)
        env = os.environ.copy()
        for key in list(env):
            if key.startswith(('GO', 'FUSION_', 'F12_')):
                env.pop(key)
        env.update(PATH=str(GO.parent)+':/usr/bin:/bin', GOENV='off', GOTOOLCHAIN='local', GOWORK='off', GOPROXY='off', GOSUMDB='off', GOFLAGS='-mod=readonly', CGO_ENABLED='1', GOAMD64='v1', GOMAXPROCS='1', GOCACHE='/home/rehearsal/results/restart-release-selection-2026-10-04/repeat-cache', GOMODCACHE='/home/rehearsal/go/pkg/mod', GOTMPDIR=str(RUN/'tmp'), TMPDIR=str(RUN/'tmp'), PYTHONDONTWRITEBYTECODE='1')
        record['go_env'] = json.loads(subprocess.check_output([str(GO), 'env', '-json'], cwd=SOURCE, env=env, text=True))
        assert not (SOURCE / 'internal/recovery/reader_test.go').exists()
        shutil.copyfile(FIXTURE, RUN / 'reader_test.go')
        overlay = {'Replace': {str(SOURCE / 'internal/recovery/reader_test.go'): str(RUN / 'reader_test.go')}}
        (RUN / 'overlay.json').write_text(json.dumps(overlay, indent=2) + '\n', encoding='utf-8')
        binary = RUN / 'bin/reader-tests'
        execute('build', ['timeout', '--kill-after=10s', '3m', str(GO), 'test', '-c', '-p=1', '-trimpath', '-buildvcs=false', '-overlay='+str(RUN/'overlay.json'), '-o', str(binary), './internal/recovery'], env)
        record['test_binary_sha256'] = sha(binary)
        execute('boundaries', ['timeout', '--kill-after=10s', '90s', str(binary), '-test.run=^TestRestoredStartupReaderBoundaries$', '-test.v', '-test.count=1', '-test.timeout=60s'], env)
        assert inventory(SOURCE) == expected_source
        assert sha(GO) == record['go_binary_sha256']
        assert sha(RUN / 'reader_test.go') == sha(FIXTURE)
        assert all(sha(REPO / relative) == digest for relative, digest in record['input_sha256'].items())
        record['source_toolchain_inputs_unchanged'] = True
        record['completed'] = True
    except BaseException as exc:
        record['failure'] = repr(exc)
        raise
    finally:
        record['finished'] = now()
        record['capacity_after'] = capacity()
        record['retained_run_file_bytes'] = sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file())
        save()
        shutil.copytree(RUN, HERE / 'qualification', ignore=shutil.ignore_patterns('bin', 'tmp'))
