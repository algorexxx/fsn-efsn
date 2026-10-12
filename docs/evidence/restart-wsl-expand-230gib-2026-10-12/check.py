from pathlib import Path
import fcntl
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent/'restart-ticket-encoder-job-6600000-2026-10-11'
ATTEMPT = PRIOR
FOLLOWUP = HERE.parent/'restart-ticket-encoder-6600000-verification-followup-2026-10-12'
HELPER = HERE.parent/'restart-ticket-encoder-replay-100000-2026-10-08/run.py'
spec = importlib.util.spec_from_file_location('sealed_helpers', HELPER)
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
phase = sys.argv[1]
assert os.getuid() == 0 and phase in ['before', 'after']
if len(sys.argv) == 2:
    os.execvp('unshare', ['unshare', '--mount', '--net', '--', 'python3', str(HERE/'check.py'), phase, os.readlink('/proc/self/ns/net'), os.readlink('/proc/self/ns/mnt')])
assert len(sys.argv) == 4
assert sys.argv[2] != os.readlink('/proc/self/ns/net') and sys.argv[3] != os.readlink('/proc/self/ns/mnt')
output = HERE/phase
output.mkdir(exist_ok=False)
r.RUN = output
record = {'started': r.now(), 'phase': phase, 'helper_sha256': r.sha(HELPER), 'commands': []}
try:
    links = subprocess.check_output(['ip', '-brief', 'link'], text=True)
    assert len(links.splitlines()) == 1 and links.startswith('lo ') and 'DOWN' in links
    record['links'] = links
    for folder in Path('/proc').iterdir():
        if folder.name.isdigit():
            try:
                assert (folder/'comm').read_text(encoding='utf-8').strip() not in ['efsn', 'replay-tests', 'observer']
            except (FileNotFoundError, ProcessLookupError):
                pass
    count = 0
    for bundle in [PRIOR, FOLLOWUP]:
        for line in (bundle/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
            digest, name = line.split(None, 1)
            assert r.sha(bundle/name) == digest, (bundle.name, name)
            count += 1
    record['evidence_files_verified'] = count
    prior = json.loads((PRIOR/'qualification/run.json').read_text(encoding='utf-8'))
    verification = json.loads((FOLLOWUP/'verification.json').read_text(encoding='utf-8'))
    review = json.loads((FOLLOWUP/'review.json').read_text(encoding='utf-8'))
    assert review['pass'] and review['original_evidence_unchanged']
    assert review['original_manifests_before_and_after']['SHA256SUMS']['sha256'] == r.sha(PRIOR/'SHA256SUMS')
    assert json.loads((PRIOR/'completion.json').read_text(encoding='utf-8')) == review['original_completion']
    assert verification['pass'] and verification['end_height'] == 6600000
    assert prior['completed'] and all(prior['additional_preservation_checks'].values())
    paths = {'backup': Path('/home/rehearsal/data/efsn/chaindata'), **{'baseline-'+h: p for h, p in r.BASELINES.items()}, 'working': Path('/home/rehearsal/replay/candidate-ticket-encoding-working'), 'recovery': Path('/home/rehearsal/replay/candidate-ticket-encoding-2400000-v2')}
    for path in paths.values():
        assert path.resolve() == path and path.is_dir() and not path.is_symlink()
    run_locks = [open(str(paths[name])+'.run.lock', 'a', encoding='utf-8') for name in ['working', 'recovery']]
    for lock in run_locks:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    database_locks = [(path/'LOCK').open('rb') for path in paths.values()]
    for lock in database_locks:
        fcntl.flock(lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
    record['locks_acquired'] = True
    capacity = {p: shutil.disk_usage(p).free for p in ['/home/rehearsal/results', '/mnt/d']}
    record['capacity_bytes'] = capacity
    assert capacity['/home/rehearsal/results'] > 20*1024**3 and capacity['/mnt/d'] > 50*1024**3
    source = subprocess.check_output(['findmnt', '-n', '-o', 'SOURCE', '/'], text=True).strip()
    size = int(subprocess.check_output(['blockdev', '--getsize64', source], text=True))
    record['root_device'] = source
    record['virtual_disk_bytes'] = size
    assert size == (220 if phase == 'before' else 230)*1024**3
    record['filesystem'] = subprocess.check_output(['df', '-B1', '/'], text=True)
    subprocess.run(['mount', '--make-rprivate', '/'], check=True)
    mounts = []
    try:
        for name, path in paths.items():
            directory = Path(tempfile.mkdtemp(prefix='fusion-resize-'+name+'-'))
            subprocess.run(['mount', '--bind', str(path), str(directory)], check=True)
            mounts.append(directory)
            subprocess.run(['mount', '-o', 'remount,bind,ro', str(directory)], check=True)
            if name == 'backup' or name.startswith('baseline-'):
                actual = r.metadata(directory, name)
                expected = prior['backup_after'] if name == 'backup' else prior['baseline_after'][name.split('-')[1]]
                assert actual == expected, name
                record[name] = actual
            else:
                expected = prior['target_before_cold_sha256'] if name == 'working' else prior['recovery_checkpoint_sha256']
                assert r.sha(directory/'replay-identity.json') == prior['checkpoint_identity_sha256']
                assert r.inventory(directory) == expected, name
                record[name+'_files_verified'] = len(expected)
                record[name+'_identity_sha256'] = prior['checkpoint_identity_sha256']
        node = Path('/home/rehearsal/results')/ATTEMPT.name
        assert r.inventory(r.SELECTED) == prior['selected_inventory']
        assert r.inventory(node/'node') == prior['candidate_inventory']
        assert r.sha(node/'bin/replay-tests') == prior['binary_sha256']
        assert not (node/'STOP').exists() and not (PRIOR/'qualification/STOP').exists()
        assert r.sha(r.TOOLCHAIN/'bin/go') == prior['toolchain']['go_binary_sha256']
        record['source_binary_toolchain_unchanged_and_no_stop'] = True
    finally:
        for directory in reversed(mounts):
            subprocess.run(['umount', str(directory)], check=True)
            directory.rmdir()
    record['pass'] = True
finally:
    record['finished'] = r.now()
    (output/'verification.json').write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(record), flush=True)
