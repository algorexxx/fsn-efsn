from pathlib import Path
import datetime
import fcntl
import hashlib
import importlib.util
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
COPY = HERE.parent / 'restart-restored-backup-copy-2026-10-19'
STARTUP = HERE.parent / 'restart-restored-startup-candidate-2026-10-09'
RETAINED = Path('/home/rehearsal/results') / STARTUP.name
REPLAY = Path('/home/rehearsal/results/restart-ticket-encoder-w-15130080-2026-10-19')
GIB = 1024**3
BEGIN = time.monotonic()
LAST_SAMPLE = 0
IMAGE_VIEW = None


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save(name, value):
    with (HERE / name).open('x', encoding='utf-8') as output:
        output.write(json.dumps(value, indent=2) + '\n')


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as source:
        while chunk := source.read(4 * 1024**2):
            value.update(chunk)
    return value.hexdigest()


def manifest(root, name, expected=None):
    if expected:
        assert digest(root / name) == expected, name
    count = 0
    for line in (root / name).read_text(encoding='utf-8').splitlines():
        sha, relative = line.split(None, 1)
        assert not Path(relative).is_absolute() and '..' not in Path(relative).parts
        assert digest(root / relative) == sha, relative
        count += 1
    return count


def load_copy():
    manifest(COPY, 'SHA256SUMS', '583a515b708a24fc835a7dbe41eb23b2db0d1d230f0a261bd684575095236069')
    spec = importlib.util.spec_from_file_location('sealed_copy_worker', COPY / 'worker.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


copy = load_copy()


def identities():
    assert read(COPY / 'completion.json')['verified_pass']
    assert read(COPY / 'review.json')['pass']
    manifest(STARTUP, 'SHA256SUMS', 'ae1ca81158081fe15169d028fc23ac7bf6e03f0ee9e5e1b9f906c6c6433bf55c')
    prior = read(STARTUP / 'qualification/run.json')
    inventory = {p.relative_to(RETAINED / 'node').as_posix(): digest(p)
                 for p in sorted((RETAINED / 'node').rglob('*'))
                 if p.is_file() and '.f12-probe' not in p.parts}
    assert inventory == prior['build_source_inventory'], 'CLI source changed'
    cli_sha = digest(RETAINED / 'bin/efsn')
    assert cli_sha == prior['binary_sha256']['efsn'] == '07aa74a3f58132e5ff1465152402d5ea3b01738c0017af5dfd5672a75a2550cd'
    assert digest(RETAINED / 'profile.toml') == '340b6110e81bff9c9897d58d76cc61069a84501be260b5562a239f35d091e907'
    assert digest(RETAINED / 'node/params/config.go') == '9487163b485477402f3329fbd29dfe2a8f60494a91f6450d609743d09de929d4'
    expected = copy.expected()
    assert read(HERE / 'expected-endpoint.json') == expected['endpoint_observations']['cold-details']
    for path, sha in [(REPLAY / 'bin/replay-tests', expected['binary_sha256']),
                      (REPLAY / 'bin/observer', expected['observer_binary_sha256']),
                      (REPLAY / 'node/docs/evidence/restart-2026-09-23/responses.json', expected['responses_sha256'])]:
        assert digest(path) == sha, str(path)
    return {'cli_sha256': cli_sha, 'source_files': len(inventory),
            'source_inventory_sha256': hashlib.sha256(json.dumps(inventory, sort_keys=True).encode()).hexdigest(),
            'copy_manifest_sha256': digest(COPY / 'SHA256SUMS'),
            'profile_sha256': digest(HERE / 'profile.json')}


def sample(phase, files=0, total=0, force=False):
    global LAST_SAMPLE
    if not force and time.monotonic() - LAST_SAMPLE < 30:
        return
    assert time.monotonic() - BEGIN < 12600, 'cooperative phase deadline'
    free = {p: shutil.disk_usage(p).free for p in ['/home/rehearsal', '/mnt/d', '/mnt/w']}
    for path, gib in [('/home/rehearsal', 20), ('/mnt/d', 50), ('/mnt/w', 100)]:
        assert free[path] > gib * GIB, ('reserve', path)
    if IMAGE_VIEW is not None:
        free['image'] = shutil.disk_usage(IMAGE_VIEW).free
        assert free['image'] > 20 * GIB, 'image reserve'
    with (HERE / 'progress.jsonl').open('a', encoding='utf-8') as output:
        output.write(json.dumps({'time': now(), 'phase': phase, 'files': files, 'bytes': total,
                                 'free_bytes': free, 'elapsed_seconds': time.monotonic() - BEGIN}) + '\n')
    LAST_SAMPLE = time.monotonic()


def closed_hashes(target, phase, expected=None):
    assert os.statvfs(target).f_flag & os.ST_RDONLY
    with (target / 'LOCK').open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
        before = copy.files(target)
        if expected is not None:
            assert set(before) == set(expected)
        total, hashes = 0, {}
        for count, (name, info) in enumerate(before.items(), 1):
            hashes[name] = digest(target / name)
            if expected is not None:
                assert hashes[name] == expected[name], name
            total += info['size']
            sample(phase, count, total)
        assert copy.files(target) == before
    save(phase + '-hashes.json', hashes)
    save(phase + '-metadata.json', before)
    sample(phase + '-complete', len(hashes), total, True)
    return before, hashes


def parse_cli(output, errors, expected):
    entries = [json.loads(line.split('RESTOREDCLI ', 1)[1]) for line in output.splitlines()
               if line.startswith('RESTOREDCLI ')]
    assert entries == [expected], entries
    assert 'panic:' not in errors and 'Blockchain manager stopped' in errors
    assert errors.index('readonly=true') < errors.index('Initialising Ethereum protocol')
    writes = [int(n.replace(',', '')) for n in re.findall(r'Writing cached state to disk[^\n]*block=([0-9,]+)', errors)]
    assert writes == [expected['head'], expected['head'] - 1, expected['head'] - 127], writes
    for bad in ['Failed to commit recent state trie', 'Dangling trie nodes', 'CRIT ', 'Fatal:']:
        assert bad not in errors, bad
    return {'observation': entries[0], 'shutdown_heights': writes}


def execute(name, args, env, target, cwd=None):
    record = {'started': now(), 'argv': args, 'cwd': str(cwd or RETAINED / 'node/tests/restart')}
    with (HERE / (name + '.stdout.txt')).open('xb') as output, (HERE / (name + '.stderr.txt')).open('xb') as errors:
        process = subprocess.Popen(args, cwd=record['cwd'], env=env, stdout=output, stderr=errors, start_new_session=True)
        try:
            while process.poll() is None:
                try:
                    process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    sample(name, force=True)
                    allocated = sum(p.stat().st_blocks * 512 for p in target.iterdir() if p.is_file())
                    assert allocated < 128 * GIB, '128 GiB database allocation ceiling'
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
            record.update(finished=now(), exit=process.returncode)
            save(name + '.json', record)
    assert process.returncode == 0, name
    sample(name + '-closed', force=True)
    return (HERE / (name + '.stdout.txt')).read_text(encoding='utf-8')


def cli(directory):
    assert not os.statvfs(directory / 'efsn/chaindata').f_flag & os.ST_RDONLY
    expected = read(HERE / 'expected-endpoint.json')
    want = {'head': expected['Number'], 'hash': expected['Hash'], 'root': expected['Root'],
            'tickets': expected['TicketCommitment'], 'mining': False, 'autoBuy': False}
    env = {k: v for k, v in os.environ.items() if not k.startswith(('GO', 'FUSION_', 'F12_'))}
    env.update(GOMAXPROCS='1', GOPROXY='off', GOSUMDB='off', GOTOOLCHAIN='local',
               FUSION_STARTUP_TEST_PROFILE=str(HERE / 'profile.json'))
    args = ['timeout', '--kill-after=20s', '600s', str(RETAINED / 'bin/efsn'),
            '--config', str(RETAINED / 'profile.toml'), '--datadir', str(directory),
            '--syncmode', 'full', '--gcmode', 'full', '--networkid', '32659', '--cache', '64',
            '--maxpeers', '0', '--port', '0', '--nat', 'none', '--nodiscover', '--v5disc=false',
            '--ipcdisable', '--authrpc.port', '0', '--mine=false', '--autobt=false', '--usb=false']
    query = 'var b=eth.getBlock("latest");console.log("RESTOREDCLI "+JSON.stringify({head:b.number,hash:b.hash,root:b.stateRoot,tickets:b.mixHash,mining:eth.mining,autoBuy:fsn.isAutoBuyTicket()}))'
    results = []
    for name in ['restored', 'restarted']:
        output = execute(name, args + ['--exec', query, 'console'], env, directory / 'efsn/chaindata')
        errors = (HERE / (name + '.stderr.txt')).read_text(encoding='utf-8')
        results.append({'phase': name, **parse_cli(output, errors, want)})
        assert not list((directory / 'keystore').glob('*')), 'unexpected keystore material'
    save('cli-result.json', {'pass': True, 'observations': results, 'normal_pruning': True,
                             'test_anchor_only': True, 'real_keys_present': False})


def cold(source, target):
    before, hashes = closed_hashes(target, 'post-startup')
    expected = copy.expected()
    env = {k: v for k, v in os.environ.items() if not k.startswith(('GO', 'FUSION_', 'F12_'))}
    env.update(GOMAXPROCS='1', GOPROXY='off', GOSUMDB='off', GOTOOLCHAIN='local',
               FUSION_RESTART_FULL_AUDIT='1', FUSION_RESTART_CHAINDATA=str(source),
               FUSION_RESTART_INSPECT_REPLAY_DIR=str(target), FUSION_RESTART_INSPECT_REPLAY_HEIGHT='15130080')
    for name, binary, test in [('cold-head', 'replay-tests', 'TestPreservedReplayHeadReadOnly'),
                                ('cold-details', 'observer', 'TestCandidateReplayColdDetails')]:
        args = ['timeout', '--kill-after=10s', '300s', str(REPLAY / 'bin' / binary),
                '-test.run=^' + test + '$', '-test.v', '-test.count=1', '-test.timeout=240s']
        output = execute(name, args, env, target, REPLAY / 'node/tests/restart')
        assert '--- SKIP:' not in output and '--- PASS: ' + test + ' (' in output
        if name == 'cold-head':
            assert 'closed replay matched: height=15130080 ' in output
        else:
            matches = re.findall(r'candidate endpoint observation: (\{.*\})', output)
            assert len(matches) == 1
            assert json.loads(matches[0]) == expected['endpoint_observations']['cold-details']
    assert copy.files(target) == before
    save('verification.json', {'pass': True, 'files_hashed': len(hashes),
                               'endpoint': expected['endpoint_observations']['cold-details'],
                               'closed_hash_inventory_sha256': digest(HERE / 'post-startup-hashes.json'),
                               'read_only_metadata_unchanged': True, 'cli_result': read(HERE / 'cli-result.json')})


def interrupted(signum, frame):
    raise TimeoutError('worker interrupted by signal ' + str(signum))


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, interrupted)
    assert os.getuid() == 1000 and len(sys.argv) == 5
    mode, source, target, view = sys.argv[1:]
    source, target, IMAGE_VIEW = Path(source), Path(target), Path(view)
    links = json.loads(subprocess.check_output(['ip', '-j', 'link', 'show'], text=True))
    assert len(links) == 1 and links[0]['ifname'] == 'lo' and 'UP' not in links[0]['flags']
    os.nice(10)
    sample(mode + '-start', force=True)
    before = identities()
    backup = read(COPY / 'source-metadata.json')
    assert os.statvfs(source).f_flag & os.ST_RDONLY and copy.files(source) == backup
    if mode == 'prehash':
        assert copy.files(target) == backup
        closed_hashes(target, 'before-startup', copy.expected()['target_before_cold_sha256'])
    elif mode == 'cli':
        cli(target)
    elif mode == 'cold':
        cold(source, target)
    else:
        raise ValueError(mode)
    assert copy.files(source) == backup and identities() == before
    save(mode + '-preservation.json', {'pass': True, 'identities': before, 'backup_metadata_unchanged': True})
