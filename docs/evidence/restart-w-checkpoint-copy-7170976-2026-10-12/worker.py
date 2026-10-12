from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / 'restart-ticket-encoder-stopped-7170976-2026-10-12'
PRIOR_SHA = 'd7bad96b8fbe3f0b30f7aee4878e205d314cf1bcdb350440c92e2337c2baefcf'
HELPER = HERE.parents[2] / 'tests/restart/snapshot_package.py'
assert hashlib.sha256(HELPER.read_bytes()).hexdigest() == 'c5e44d9dbb53b74bc2f36ea78a24ae5dcff89dfee77a4a292e8e27cdea87bf35'
spec = importlib.util.spec_from_file_location('snapshot_helpers', HELPER)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
START = time.monotonic()
LAST_STATUS = 0.0

def status(phase, count=0, total_bytes=0, force=False):
    global LAST_STATUS
    if not force and time.monotonic() - LAST_STATUS < 30:
        return
    assert time.monotonic() - START < 12600, 'cooperative phase deadline reached'
    free = {p: shutil.disk_usage(p).free for p in ['/home/rehearsal', '/mnt/d', '/mnt/w']}
    for path, gib in [('/home/rehearsal', 20), ('/mnt/d', 50), ('/mnt/w', 100)]:
        assert free[path] > gib * 1024**3, ('reserve reached', path, free[path])
    record = {'time': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'phase': phase,
              'files': count, 'bytes': total_bytes, 'free_bytes': free, 'elapsed_seconds': time.monotonic() - START}
    with (HERE / 'progress.jsonl').open('a', encoding='utf-8') as file:
        file.write(json.dumps(record) + '\n')
    LAST_STATUS = time.monotonic()

def files(root):
    assert root.resolve() == root and root.is_dir()
    rows = {}
    for path in sorted(root.iterdir()):
        info = path.lstat()
        assert stat.S_ISREG(info.st_mode) and not path.is_symlink()
        assert helper.FILE_NAME.fullmatch(path.name) or path.name == 'replay-identity.json', path.name
        rows[path.name] = {'size': info.st_size, 'mtime_ns': info.st_mtime_ns, 'mode': stat.S_IMODE(info.st_mode)}
    return rows

def expected():
    assert helper.digest(PRIOR / 'SHA256SUMS') == PRIOR_SHA
    for line in (PRIOR / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        digest, relative = line.split(None, 1)
        assert helper.digest(PRIOR / relative) == digest, relative
    prior = helper.read_json(PRIOR / 'qualification/run.json')
    assert prior['completed'] and prior['inspect_passed'] and helper.read_json(PRIOR / 'verification.json')['pass']
    assert prior['inspection_height'] == 7170976 and len(prior['target_before_cold_sha256']) == 22501
    return prior

def copy(source, destination, prior):
    assert os.statvfs(source).f_flag & os.ST_RDONLY
    assert not destination.exists()
    before = files(source)
    hashes = prior['target_before_cold_sha256']
    assert set(before) == set(hashes)
    size = sum(row['size'] for row in before.values())
    helper.check_space(destination.parent, size, 20 * 1024**3)
    helper.check_space(Path('/mnt/w'), size, 100 * 1024**3)
    helper.write_json(HERE / 'source-metadata.json', before)
    destination.mkdir(mode=0o700)
    total = 0
    for count, (name, info) in enumerate(before.items(), 1):
        digest = hashlib.sha256()
        with (source / name).open('rb') as reader, (destination / name).open('xb') as writer:
            while chunk := reader.read(helper.BLOCK):
                writer.write(chunk)
                digest.update(chunk)
                total += len(chunk)
                status('copy-and-source-hash', count - 1, total)
            writer.flush()
            os.fsync(writer.fileno())
            os.fchmod(writer.fileno(), info['mode'])
        assert digest.hexdigest() == hashes[name], name
        os.utime(destination / name, ns=(info['mtime_ns'], info['mtime_ns']))
    directory = os.open(destination, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)
    assert files(source) == before
    assert files(destination) == before
    status('copied', len(before), total, True)
    helper.write_json(HERE / 'copy-result.json', {'completed': True, 'source_hashes_match_sealed_inventory': True,
                       'source_metadata_unchanged': True, 'files': len(before), 'bytes': total,
                       'prior_manifest_sha256': PRIOR_SHA, 'destination': str(destination)})

def verify(source, destination, prior):
    assert os.statvfs(source).f_flag & os.ST_RDONLY
    assert os.statvfs(destination).f_flag & os.ST_RDONLY
    before = helper.read_json(HERE / 'source-metadata.json')
    assert files(source) == before and files(destination) == before
    total = 0
    for count, (name, digest) in enumerate(prior['target_before_cold_sha256'].items(), 1):
        assert helper.digest(destination / name) == digest, name
        total += before[name]['size']
        status('verify-after-reattach', count, total)
    runtime = Path('/home/rehearsal/results')
    observer = runtime / PRIOR.name / 'bin/observer'
    replay = runtime / 'restart-ticket-encoder-job-7200000-2026-10-12/bin/replay-tests'
    assert helper.digest(observer) == prior['observer_binary_sha256']
    assert helper.digest(replay) == prior['binary_sha256']
    env = dict(os.environ, FUSION_RESTART_INSPECT_REPLAY_DIR=str(destination),
               FUSION_RESTART_INSPECT_REPLAY_HEIGHT='7170976', GOMAXPROCS='2')
    for name, binary, test in [('cold-head', replay, 'TestPreservedReplayHeadReadOnly'),
                                ('cold-details', observer, 'TestCandidateReplayColdDetails')]:
        args = ['timeout', '--kill-after=10s', '5m', str(binary), '-test.run=^' + test + '$',
                '-test.v', '-test.count=1', '-test.timeout=4m']
        with (HERE / (name + '.stdout.txt')).open('xb') as output, (HERE / (name + '.stderr.txt')).open('xb') as error:
            result = subprocess.run(args, stdout=output, stderr=error, env=env)
        helper.write_json(HERE / (name + '.json'), {'argv': args, 'exit': result.returncode})
        assert result.returncode == 0, name
    output = (HERE / 'cold-details.stdout.txt').read_text(encoding='utf-8')
    matches = re.findall(r'candidate endpoint observation: (\{.*\})', output)
    assert len(matches) == 1
    observed = json.loads(matches[0])
    assert observed == prior['endpoint_observations']['cold-details']
    assert files(source) == before and files(destination) == before
    assert helper.digest(observer) == prior['observer_binary_sha256']
    assert helper.digest(replay) == prior['binary_sha256']
    status('verified', len(before), total, True)
    helper.write_json(HERE / 'verification.json', {'pass': True, 'files': len(before), 'bytes': total,
                      'destination_hashes_match_sealed_inventory': True, 'source_metadata_unchanged': True,
                      'destination_metadata_unchanged_after_cold_reads': True, 'endpoint': observed,
                      'observer_binary_sha256': prior['observer_binary_sha256'], 'replay_binary_sha256': prior['binary_sha256']})

if __name__ == '__main__':
    assert os.getuid() == 1000 and len(sys.argv) == 4
    interfaces = json.loads(subprocess.check_output(['ip', '-j', 'link', 'show'], text=True))
    assert len(interfaces) == 1 and interfaces[0]['ifname'] == 'lo' and 'UP' not in interfaces[0]['flags']
    status(sys.argv[1] + '-start', force=True)
    prior = expected()
    assert sys.argv[1] in ['copy', 'verify']
    (copy if sys.argv[1] == 'copy' else verify)(Path(sys.argv[2]), Path(sys.argv[3]), prior)
