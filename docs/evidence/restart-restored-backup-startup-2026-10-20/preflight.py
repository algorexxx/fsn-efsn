from pathlib import Path
import json
import shutil
import subprocess
import worker

identities = worker.identities()
source = Path('/home/rehearsal/data/efsn/chaindata')
assert worker.copy.files(source) == worker.read(worker.COPY / 'source-metadata.json')
processes = subprocess.check_output(['ps', '-eo', 'pid,comm'], text=True)
busy = [line for line in processes.splitlines() if line.split()[-1] in
        ['efsn', 'replay-tests', 'observer', 'storage-probe']]
loops = json.loads(subprocess.check_output(['losetup', '--list', '--json'], text=True))['loopdevices']
assert not busy and not loops
free = {p: shutil.disk_usage(p).free for p in ['/home/rehearsal', '/mnt/d']}
assert free['/home/rehearsal'] > 21 * worker.GIB and free['/mnt/d'] > 51 * worker.GIB
worker.save('preflight.json', {'pass': True, 'checked': worker.now(), 'identities': identities,
                               'backup_metadata_unchanged': True, 'busy_processes': busy,
                               'loopdevices': loops, 'free_bytes': free, 'database_opened_or_hashed': False})
print('Identities, source inventory, original metadata and idle-state preflight passed')
