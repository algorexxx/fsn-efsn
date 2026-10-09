from pathlib import Path
from contextlib import ExitStack
import datetime
import fcntl
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SOURCE = Path('/home/rehearsal/replay')
DEST = Path('/mnt/w/FusionRestart/checkpoint-archive-2026-10-09')
HEIGHTS = [100000, 300000, 600000, 900000, 1200000, 1400000, 1600000, 1800000]
KEEP = [2000000, 2200000]
BLOCK = 4 * 1024**2
spec = importlib.util.spec_from_file_location('snapshot_helpers', REPO/'tests/restart/snapshot_package.py')
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def save(name, data):
    helpers.write_json(HERE/name, data)


def capacity():
    return {str(p): shutil.disk_usage(p).free for p in [SOURCE, Path('/mnt/d'), Path('/mnt/w')]}


def require_source(path):
    assert SOURCE.resolve() == SOURCE and path.parent == SOURCE
    assert path.name in ['candidate-ticket-encoding-'+str(h) for h in HEIGHTS+KEEP]
    assert path.resolve() == path and path.is_dir() and not path.is_symlink()


def files(path):
    assert path.resolve() == path and path.is_dir() and not path.is_symlink()
    result = {}
    for item in sorted(path.iterdir()):
        info = item.lstat()
        assert stat.S_ISREG(info.st_mode) and not item.is_symlink(), str(item)
        assert helpers.FILE_NAME.fullmatch(item.name) or item.name == 'replay-identity.json'
        result[item.name] = {'size': info.st_size, 'mtime_ns': info.st_mtime_ns, 'mode': stat.S_IMODE(info.st_mode)}
    return result


def hashes(path):
    return {name: helpers.digest(path/name) for name in files(path)}


def expectations():
    result = {}
    for height in HEIGHTS+KEEP:
        day = '08' if height <= 1200000 else '09'
        bundle = HERE.parent/('restart-ticket-encoder-replay-'+str(height)+'-2026-10-'+day)
        manifest = (bundle/'SHA256SUMS').read_text(encoding='utf-8').splitlines()
        entries = {line.split(None, 1)[1]: line.split(None, 1)[0] for line in manifest}
        for name in ['qualification/run.json', 'verification.json']:
            assert helpers.digest(bundle/name) == entries[name]
        run = helpers.read_json(bundle/'qualification/run.json')
        assert run['completed'] and helpers.read_json(bundle/'verification.json')['pass']
        result[height] = {'hashes': run['target_before_cold_sha256'], 'bundle': str(bundle.relative_to(REPO)), 'run_sha256': entries['qualification/run.json']}
    return result


def copy_checkpoint(source, destination, expected):
    before = files(source)
    assert set(before) == set(expected)
    helpers.check_space(DEST, sum(i['size'] for i in before.values()), 100*1024**3)
    staging = destination.with_name(destination.name+'.incomplete')
    assert not staging.exists() and not destination.exists()
    staging.mkdir(mode=0o700)
    for name in before:
        digest = hashlib.sha256()
        with (source/name).open('rb') as reader, (staging/name).open('xb') as writer:
            while chunk := reader.read(BLOCK):
                writer.write(chunk)
                digest.update(chunk)
            writer.flush()
            os.fsync(writer.fileno())
        assert digest.hexdigest() == expected[name], name
    assert files(source) == before and hashes(source) == expected
    assert hashes(staging) == expected
    assert {n: i['size'] for n, i in files(staging).items()} == {n: i['size'] for n, i in before.items()}
    staging.rename(destination)
    return {'source': str(source), 'archive': str(destination), 'files': before, 'sha256': expected, 'verified': now()}


def require_archive(archived, expected):
    destination = Path(archived['archive'])
    assert destination.parent == DEST and destination.name == Path(archived['source']).name
    assert archived['sha256'] == expected and hashes(destination) == expected


def execute(mode):
    assert os.getuid() == 1000 and mode in ['archive', 'retire']
    mount = json.loads(subprocess.check_output(['findmnt', '-J', '-o', 'TARGET,SOURCE,FSTYPE,OPTIONS', '-T', '/mnt/w'], text=True))['filesystems'][0]
    assert mount['target'] == '/mnt/w' and mount['source'] == 'W:' and mount['fstype'] == '9p'
    assert DEST.parent.resolve() == DEST.parent and SOURCE.resolve() == SOURCE
    expected = expectations()
    record = {'mode': mode, 'started': now(), 'mount': mount, 'capacity_before': capacity(), 'script_sha256': helpers.digest(Path(__file__)), 'helper_sha256': helpers.digest(REPO/'tests/restart/snapshot_package.py'), 'checkpoints': [], 'preserved': {}}
    assert record['capacity_before'][str(SOURCE)] > 20*1024**3
    assert record['capacity_before']['/mnt/d'] > 50*1024**3
    assert record['capacity_before']['/mnt/w'] > 100*1024**3
    with ExitStack() as stack:
        for height in HEIGHTS+KEEP:
            path = SOURCE/('candidate-ticket-encoding-'+str(height))
            require_source(path)
            for lock_path in [Path(str(path)+'.run.lock'), path/'LOCK']:
                lock = stack.enter_context(lock_path.open('rb'))
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for height in KEEP:
            path = SOURCE/('candidate-ticket-encoding-'+str(height))
            assert hashes(path) == expected[height]['hashes']
            record['preserved'][str(height)] = expected[height]
        if mode == 'archive':
            assert not DEST.exists() and not (HERE/'archive.json').exists()
            DEST.mkdir(parents=True, mode=0o700)
            for height in HEIGHTS:
                source = SOURCE/('candidate-ticket-encoding-'+str(height))
                item = copy_checkpoint(source, DEST/source.name, expected[height]['hashes'])
                item.update(height=height, evidence=expected[height]['bundle'], evidence_sha256=expected[height]['run_sha256'])
                helpers.write_json(DEST/(str(height)+'.manifest.json'), item)
                record['checkpoints'].append(item)
                print(json.dumps({'archived': height, 'files': len(item['files']), 'bytes': sum(f['size'] for f in item['files'].values())}), flush=True)
        else:
            original = helpers.read_json(HERE/'archive.json')
            assert original['completed'] and original['script_sha256'] == record['script_sha256'] and original['helper_sha256'] == record['helper_sha256']
            assert [item['height'] for item in original['checkpoints']] == HEIGHTS
            assert helpers.digest(DEST/'archive.json') == helpers.digest(HERE/'archive.json')
            for item in original['checkpoints']:
                require_source(Path(item['source']))
                assert files(Path(item['source'])) == item['files']
                assert hashes(Path(item['source'])) == expected[item['height']]['hashes']
                require_archive(item, expected[item['height']]['hashes'])
                assert helpers.read_json(DEST/(str(item['height'])+'.manifest.json')) == item
            save('retire-ready.json', {'verified': now(), 'archive_sha256': helpers.digest(HERE/'archive.json'), 'sources': [item['source'] for item in original['checkpoints']]})
            for item in original['checkpoints']:
                path = Path(item['source'])
                require_source(path)
                assert files(path) == item['files']
                for name in item['files']:
                    child = path/name
                    assert child.parent == path and child.resolve() == child and stat.S_ISREG(child.lstat().st_mode)
                    child.unlink()
                path.rmdir()
                assert not path.exists()
                record['checkpoints'].append({'height': item['height'], 'source': str(path), 'archive': item['archive'], 'local_removed': now()})
                save(str(item['height'])+'-retired.json', record['checkpoints'][-1])
                print(json.dumps(record['checkpoints'][-1]), flush=True)
        for height in KEEP:
            assert hashes(SOURCE/('candidate-ticket-encoding-'+str(height))) == expected[height]['hashes']
        record.update(completed=True, finished=now(), capacity_after=capacity())
        save(mode+'.json', record)
        helpers.write_json(DEST/(mode+'.json'), record)
        assert helpers.digest(DEST/(mode+'.json')) == helpers.digest(HERE/(mode+'.json'))
        print(json.dumps({'completed': mode, 'capacity_after': record['capacity_after']}), flush=True)


if __name__ == '__main__':
    mode = sys.argv[1]
    try:
        execute(mode)
    except Exception as error:
        save(mode+'-failure.json', {'time': now(), 'error': repr(error)})
        raise
