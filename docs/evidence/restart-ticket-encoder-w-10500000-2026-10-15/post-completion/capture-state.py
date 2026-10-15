from pathlib import Path
import datetime
import json
import shutil
import subprocess

post = Path(__file__).resolve().parent
config = json.loads((post.parent / 'inputs/config.json').read_text(encoding='utf-8'))
processes = subprocess.check_output(['ps', '-eo', 'pid,comm'], text=True)
loops = json.loads(subprocess.check_output(['losetup', '--list', '--json'], text=True))['loopdevices']
mounts = Path('/proc/self/mountinfo').read_text(encoding='utf-8').splitlines()
target = '/home/rehearsal/replay/' + config['target']
state = {
    'checked': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'busy_processes': [line for line in processes.splitlines() if line.split()[-1] in
                       ['efsn', 'replay-tests', 'observer', 'storage-probe']],
    'loopdevices': loops,
    'replay_image_attachments': [row for row in loops if row.get('back-file') == config['storage']['image']],
    'matching_mounts': [line for line in mounts if any(value in line for value in
                        [target, config['job'], config['storage']['image']])],
    'target_directory_exists': Path(target).exists(),
    'free_bytes': {p: shutil.disk_usage(p).free for p in ['/home/rehearsal/results', '/mnt/d']},
}
with (post / 'post-state.json').open('x', encoding='utf-8', newline='\n') as output:
    output.write(json.dumps(state, indent=2) + '\n')
print(json.dumps(state, indent=2))
