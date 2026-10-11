from pathlib import Path
import datetime
import importlib.util
import json
import os
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
here = Path(__file__).resolve().parent
repo = here.parents[2]
assert os.getuid() == 0 and not (here/'post-capacity.json').exists()
assert json.loads((here/'after/verification.json').read_text(encoding='utf-8'))['pass']
assert json.loads((here/'after-completion.json').read_text(encoding='utf-8'))['exit'] == 0
assert json.loads((here/'storage-health.json').read_text(encoding='utf-8'))['pass']
spec = importlib.util.spec_from_file_location('retained_monitor', repo/'tests/restart/replay_monitor.py')
monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)
prior = here.parent/'restart-ticket-encoder-job-6300000-v3-2026-10-10'
config = json.loads((prior/'inputs/config.json').read_text(encoding='utf-8'))
config.update(job='restart-ticket-encoder-job-6600000-2026-10-11', prior_bundle=prior.name, start_height=6300000, end_height=6600000)
config.pop('stopped_attempt')
config['limits']['max_bytes'] = 34*1024**3
monitor.validate_configuration(config)
monitor.require_verified_prior(config, json.loads((prior/'completion.json').read_text(encoding='utf-8')), json.loads((prior/'verification.json').read_text(encoding='utf-8')))
for folder in Path('/proc').iterdir():
    if folder.name.isdigit():
        try:
            assert (folder/'comm').read_text(encoding='utf-8').strip() not in ['efsn', 'replay-tests', 'restart-tests', 'observer']
        except (FileNotFoundError, ProcessLookupError):
            pass
target = Path('/home/rehearsal/replay')/config['target']
size = int(subprocess.check_output(['timeout', '15s', 'du', '-sB1', str(target)], text=True).split()[0])
free = {p: shutil.disk_usage(p).free for p in ['/home/rehearsal/results', '/mnt/d']}
record = {'checked': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'proposed_configuration': config, 'existing_allocated_bytes': size, 'capacity_bytes': free, 'prior_verified': True, 'job_prepared': False, 'launched': False}
try:
    record['required_capacity_bytes'] = monitor.require_starting_capacity(config, free, size)
    record['capacity_pass'] = True
except ValueError as error:
    record['capacity_pass'] = False
    record['reason'] = str(error)
(here/'post-capacity.json').write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
print(json.dumps(record), flush=True)
