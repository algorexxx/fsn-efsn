from pathlib import Path
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
if len(sys.argv) == 1:
    assert os.getuid() == 0
    os.execvp('unshare', ['unshare', '--mount', '--net', '--', 'python3', '-B', str(__file__), 'mount'])
if sys.argv[1] == 'mount':
    subprocess.run(['mount', '--make-rprivate', '/'], check=True)
    fixture = Path(tempfile.mkdtemp(prefix='w-copy-controls-'))
    os.chown(fixture, 1000, 1000)
    source = fixture / 'source'
    source.mkdir()
    for name, content in [('CURRENT', b'MANIFEST-000001\n'), ('MANIFEST-000001', b'manifest-fixture\n'),
                          ('000001.ldb', bytes(range(256)) * 256), ('LOCK', b''), ('replay-identity.json', b'{}\n')]:
        (source / name).write_bytes(content)
    view = fixture / 'read-only'
    view.mkdir()
    subprocess.run(['mount', '--bind', str(source), str(view)], check=True)
    subprocess.run(['mount', '-o', 'remount,bind,ro', str(view)], check=True)
    try:
        result = subprocess.run(['runuser', '-u', 'rehearsal', '--', 'python3', '-B', str(__file__), 'checks', str(fixture)])
    finally:
        subprocess.run(['umount', str(view)], check=True)
    sys.exit(result.returncode)
assert sys.argv[1] == 'checks' and os.getuid() == 1000
spec = importlib.util.spec_from_file_location('migration_worker', HERE / 'worker.py')
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)
fixture = Path(sys.argv[2])
source = fixture / 'read-only'
hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in source.iterdir()}
worker.status = lambda *args, **kwargs: None
real_check_space = worker.helper.check_space
def check_fixture_space(directory, needed, reserve):
    if directory != Path('/mnt/w'):
        real_check_space(directory, needed, reserve)
worker.helper.check_space = check_fixture_space
passed = []
for name, expected_failure in [('valid', False), ('wrong-hash', True), ('existing-target', True)]:
    case = fixture / name
    case.mkdir()
    worker.HERE = case
    expected = dict(hashes)
    destination = case / 'copied'
    if name == 'wrong-hash':
        expected['000001.ldb'] = '0' * 64
    if name == 'existing-target':
        destination.mkdir()
    try:
        worker.copy(source, destination, {'target_before_cold_sha256': expected})
    except AssertionError:
        assert expected_failure, name
    else:
        assert not expected_failure, name
        assert {p.name: worker.helper.digest(p) for p in destination.iterdir()} == hashes
        assert worker.files(source) == worker.files(destination)
    passed.append(name)
assert {p.name: worker.helper.digest(p) for p in source.iterdir()} == hashes
assert worker.expected()['inspection_height'] == 7170976
worker.helper.write_json(HERE / 'copy-controls.json', {'pass': True, 'cases': passed,
    'fixture': str(fixture), 'source_unchanged': True, 'sealed_prior_verified': True,
    'scope': 'synthetic source-copy fidelity/hash mismatch/existing-target guards; capacity status not exercised'})
