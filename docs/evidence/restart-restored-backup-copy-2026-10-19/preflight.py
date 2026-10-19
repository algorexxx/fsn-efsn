from pathlib import Path
import datetime
import gzip
import json
import shutil
import subprocess
import worker

source = Path('/home/rehearsal/data/efsn/chaindata')
prior = worker.expected()
rows = worker.files(source)
assert set(rows) == set(prior['target_before_cold_sha256'])
metadata = [[name, row['size'], row['mtime_ns']] for name, row in rows.items()]
saved = json.loads(gzip.decompress((worker.PRIOR / 'qualification/backup-after.json.gz').read_bytes()))
assert metadata == saved
assert len(rows) == 56107 and sum(row['size'] for row in rows.values()) == 117170022674
runtime = Path('/home/rehearsal/results')
paths = {
    runtime / worker.PRIOR.name / 'bin/replay-tests': prior['binary_sha256'],
    runtime / worker.PRIOR.name / 'bin/observer': prior['observer_binary_sha256'],
    runtime / 'restart-restored-startup-candidate-2026-10-09/bin/efsn':
        '07aa74a3f58132e5ff1465152402d5ea3b01738c0017af5dfd5672a75a2550cd',
    runtime / worker.PRIOR.name / 'node/docs/evidence/restart-2026-09-23/responses.json':
        prior['responses_sha256'],
}
for path, digest in paths.items():
    assert worker.helper.digest(path) == digest, str(path)
processes = subprocess.check_output(['ps', '-eo', 'pid,comm'], text=True)
busy = [line for line in processes.splitlines() if line.split()[-1] in
        ['efsn', 'replay-tests', 'observer', 'storage-probe']]
loops = json.loads(subprocess.check_output(['losetup', '--list', '--json'], text=True))['loopdevices']
assert not busy and not loops
free = {p: shutil.disk_usage(p).free for p in ['/home/rehearsal', '/mnt/d']}
assert free['/home/rehearsal'] > 21 * 1024**3 and free['/mnt/d'] > 51 * 1024**3
worker.helper.write_json(worker.HERE / 'preflight.json', {
    'pass': True, 'checked': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'backup_files': len(rows), 'backup_bytes': sum(row['size'] for row in rows.values()),
    'backup_metadata_matches_final_replay': True,
    'executable_and_response_hashes': {str(path): digest for path, digest in paths.items()},
    'busy_processes': busy, 'loopdevices': loops, 'free_bytes': free,
    'database_bytes_opened_or_hashed': False,
})
print('provenance, metadata, identities and idle-state preflight passed')
