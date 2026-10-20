"""Finite offline candidate acceptance; all new build/data files stay on C:."""
from pathlib import Path
import datetime
import fcntl
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUN = REPO / 'tmp' / HERE.name
PRIOR = HERE.parent / 'restart-ticket-encoder-regressions-2026-10-08'
SOURCE = Path('/home/rehearsal/results') / PRIOR.name / 'candidate-recovery'
GO = Path('/home/rehearsal/results/restart-release-selection-2026-10-04/toolchain/go/bin/go')
COMPLETED = HERE.parent / 'restart-ticket-encoder-full-state-operator-2026-10-20'
GIB = 1024**3
START = time.monotonic()
record = {'started': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'commands': [], 'completed': False}


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        while chunk := source.read(4 * 1024**2):
            digest.update(chunk)
    return digest.hexdigest()


def inventory(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob('*')) if p.is_file()}


def metadata(root):
    return {p.relative_to(root).as_posix(): [p.stat().st_size, p.stat().st_mtime_ns]
            for p in sorted(root.rglob('*')) if p.is_file()}


def save():
    (RUN / 'run.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')


def manifest(root, name, pin):
    assert sha(root / name) == pin
    count = 0
    for line in (root / name).read_text(encoding='utf-8').splitlines():
        digest, relative = line.split(None, 1)
        assert not Path(relative).is_absolute() and '..' not in Path(relative).parts
        assert sha(root / relative) == digest, relative
        count += 1
    return count


def sample(phase):
    free = {p: shutil.disk_usage(p).free for p in ['/home/rehearsal', '/mnt/d', '/mnt/c']}
    for path, floor in [('/home/rehearsal', 20), ('/mnt/d', 50), ('/mnt/c', 40)]:
        assert free[path] > floor * GIB, ('reserve', path, free[path])
    assert time.monotonic() - START < 2100, 'cooperative whole-job deadline'
    # Size sampling only, never content hashing while a child can write.
    total = 0
    for path in RUN.rglob('*'):
        try:
            if path.is_file():
                total += path.stat().st_size
        except FileNotFoundError:
            pass  # Compiler temporary files can disappear between directory/stat.
    assert total < 4 * GIB, '4 GiB disposable-work allocation ceiling'
    with (RUN / 'resources.jsonl').open('a', encoding='utf-8') as output:
        output.write(json.dumps({'time': now(), 'phase': phase, 'free_bytes': free,
                                 'run_logical_bytes': total, 'elapsed_seconds': time.monotonic() - START}) + '\n')
    return free


def execute(name, args, env, cwd, seconds):
    sample(name + '-before')
    entry = {'name': name, 'argv': ['timeout', '--kill-after=20s', str(seconds) + 's'] + args,
             'cwd': str(cwd), 'started': now()}
    begin = time.monotonic()
    with (RUN / (name + '.stdout.txt')).open('xb') as output, (RUN / (name + '.stderr.txt')).open('xb') as error:
        process = subprocess.Popen(entry['argv'], cwd=cwd, env=env, stdout=output,
                                   stderr=error, start_new_session=True)
        try:
            while process.poll() is None:
                try:
                    process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    sample(name)
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
            entry.update(finished=now(), exit=process.returncode,
                         elapsed_seconds=time.monotonic() - begin)
            record['commands'].append(entry)
            save()
    assert process.returncode == 0, name
    sample(name + '-after')
    print(name + ' passed', flush=True)
    return (RUN / (name + '.stdout.txt')).read_text(encoding='utf-8')


def qualify(source_view):
    global SOURCE
    SOURCE = source_view
    assert os.getuid() == 1000 and source_view.is_dir()
    assert os.statvfs(source_view).f_flag & os.ST_RDONLY
    assert not RUN.exists(), 'preserve existing attempt'
    links = json.loads(subprocess.check_output(['ip', '-j', 'link', 'show'], text=True))
    assert len(links) == 1 and links[0]['ifname'] == 'lo' and 'UP' not in links[0]['flags']
    assert os.readlink('/proc/self/ns/net') != sys.argv[2]
    os.nice(10)
    RUN.mkdir()
    for name in ['bin', 'tmp', 'cache', 'fixtures', 'artifacts']:
        (RUN / name).mkdir()
    record.update(uid=os.getuid(), netns=os.readlink('/proc/self/ns/net'),
                  parent_netns=sys.argv[2], interfaces=links, source_view=str(source_view))
    try:
        record['capacity_before'] = sample('start')
        assert record['capacity_before']['/mnt/c'] > 50 * GIB
        record['investigation_commit'] = subprocess.check_output(
            ['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip()
        record['input_sha256'] = {name: sha(HERE / name) for name in
                                   [line.split(None, 1)[1] for line in (HERE / 'INPUT_SHA256SUMS').read_text().splitlines()]}
        for line in (HERE / 'INPUT_SHA256SUMS').read_text().splitlines():
            digest, name = line.split(None, 1)
            assert sha(HERE / name) == digest
        record['input_manifest_sha256'] = sha(HERE / 'INPUT_SHA256SUMS')
        record['completed_operator_files_verified'] = manifest(COMPLETED, 'SHA256SUMS', '9e0fc4b36679a5dae9779c3d021ade2d2c3ee6cff0caf5ab1043bb3b9f60052a')
        assert read(COMPLETED / 'completion.json')['verified_pass'] and read(COMPLETED / 'verification.json')['passed']
        record['prior_files_verified'] = manifest(PRIOR, 'SHA256SUMS', '59bea0c464a9a089518e3454c646b381369691f3f4e00ee774730a4c8c2b400c')
        prior = read(PRIOR / 'qualification/run.json')
        expected = read(HERE / 'retained-source-inventory.json')
        assert expected == prior['source_inventories']['candidate-recovery']
        assert inventory(SOURCE) == expected
        assert sha(GO) == prior['toolchains']['modern']['go_binary_sha256'] == '30969f97169d7f43fe6a085873d75613adc21e30818a8c61d95bd27275df4624'
        record['go_binary_sha256'] = sha(GO)
        record['retained_source_inventory_sha256'] = sha(HERE / 'retained-source-inventory.json')
        node = RUN / 'recovery'
        node.mkdir()
        build_expected = {}
        for name, digest in expected.items():
            if name.startswith('tests/restart/'):
                continue
            target = node / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SOURCE / name, target)
            build_expected[name] = digest
        for path in sorted((HERE / 'harness').iterdir()):
            name = 'tests/restart/' + path.name
            (node / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, node / name)
            build_expected[name] = sha(path)
        context = 'docs/evidence/restart-full-state-2026-09-24/context.rlp'
        (node / context).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / context, node / context)
        build_expected[context] = sha(REPO / context)
        assert build_expected[context] == '6ed278667f6bbe15833a6feb0cf0524ee8575d3ddb24e14cd76c6974668ad8cd'
        assert inventory(node) == build_expected
        record['build_source_inventory'] = build_expected
        env = {k: v for k, v in os.environ.items() if not k.startswith(('GO', 'FUSION_', 'F12_'))}
        env.update(PATH=str(GO.parent) + ':/usr/bin:/bin', GOENV='off', GOTOOLCHAIN='local',
                   GOWORK='off', GOPROXY='off', GOSUMDB='off', GOFLAGS='-mod=readonly',
                   CGO_ENABLED='1', GOAMD64='v1', GOMAXPROCS='1', GOMEMLIMIT='512MiB',
                   GOCACHE=str(RUN / 'cache'), GOMODCACHE='/home/rehearsal/go/pkg/mod',
                   GOTMPDIR=str(RUN / 'tmp'), TMPDIR=str(RUN / 'tmp'), PYTHONDONTWRITEBYTECODE='1')
        record['go_env'] = json.loads(subprocess.check_output([str(GO), 'env', '-json'], cwd=node, env=env, text=True))
        save()
        execute('harness-build', [str(GO), 'test', '-c', '-race', '-p=1', '-trimpath', '-buildvcs=false',
                                  '-o', str(RUN / 'bin/approval-tests'), './tests/restart'], env, node, 900)
        record['binary_sha256'] = inventory(RUN / 'bin')
        save()
        test_env = dict(env, FUSION_APPROVAL_RETAINED_ROOT=str(RUN / 'fixtures'))
        pattern = '^Test(ApprovedOfflineProcessCuts|ApprovedOfflineRefusals|KeystorePreflightLocksAndUncertain)$'
        output = execute('approved-cuts', [str(RUN / 'bin/approval-tests'), '-test.run=' + pattern,
                         '-test.v', '-test.count=1', '-test.timeout=900s'], test_env, node / 'tests/restart', 960)
        errors = (RUN / 'approved-cuts.stderr.txt').read_text(encoding='utf-8')
        for test in ['ApprovedOfflineProcessCuts', 'ApprovedOfflineRefusals', 'KeystorePreflightLocksAndUncertain']:
            assert '--- PASS: Test' + test + ' (' in output
        assert '--- SKIP:' not in output and 'WARNING: DATA RACE' not in output + errors and 'panic:' not in output + errors
        assert output.count('exact recovery without another callback; independent cold ledgers agree') == 9
        for cut in ['reservation', 'signature']:
            assert '--- PASS: TestApprovedOfflineProcessCuts/' + cut + ' (' in output
        for refusal in ['policy_quota', 'policy_parent', 'policy_executable', 'policy_config',
                        'purchase_owner', 'parent', 'purchase_bytes', 'unsigned_bytes']:
            assert '--- PASS: TestApprovedOfflineRefusals/' + refusal + ' (' in output
        assert 'credential validation holds both locks; wrong password permits a later attempt; unfinished signature refuses key access' in output
        # The harness and all its children have exited; these inventories are cold.
        record['closed_fixture_hashes'] = inventory(RUN / 'fixtures')
        record['retained_cases'] = sorted(path.name for path in (RUN / 'fixtures').iterdir())
        assert len(record['retained_cases']) == 7
        assert inventory(SOURCE) == expected and inventory(node) == build_expected
        assert sha(GO) == record['go_binary_sha256'] and inventory(RUN / 'bin') == record['binary_sha256']
        assert all(sha(HERE / name) == digest for name, digest in record['input_sha256'].items())
        record['preservation_pass'] = True
        record['completed'] = True
        print('Approved process cuts, refusals and credential-lock acceptance passed', flush=True)
    except BaseException as exc:
        record['failure'] = repr(exc)
        raise
    finally:
        record.update(finished=now(), elapsed_seconds=time.monotonic() - START)
        record['capacity_after'] = {p: shutil.disk_usage(p).free for p in ['/home/rehearsal', '/mnt/d', '/mnt/c']}
        save()
        # Retain every fixture in place, including failed cases; copy small reviewable records.
        fixtures = RUN / 'fixtures'
        for path in fixtures.rglob('*'):
            if path.is_file() and (path.name.startswith(('step-', 'policy-')) or path.suffix == '.rlp'):
                target = RUN / 'artifacts' / path.relative_to(fixtures)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
        destination = HERE / 'qualification'
        assert not destination.exists()
        destination.mkdir()
        for path in RUN.iterdir():
            if path.is_file():
                shutil.copyfile(path, destination / path.name)
        shutil.copytree(RUN / 'artifacts', destination / 'artifacts')


def interrupted(signum, frame):
    raise TimeoutError('worker interrupted by signal ' + str(signum))


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, interrupted)
    assert len(sys.argv) == 3
    qualify(Path(sys.argv[1]))
