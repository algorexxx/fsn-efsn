from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ATTEMPT = HERE.parent / 'restart-ticket-encoder-job-6600000-2026-10-11'
verification = json.loads((HERE / 'verification.json').read_text(encoding='utf-8'))
run = json.loads((ATTEMPT / 'qualification/run.json').read_text(encoding='utf-8'))
assert verification['pass'] is True and run['completed'] and run['inspect_passed']
host = Path('tmp/replay-job-6600000-2026-10-11/dispatch-finished.json')
dispatch = json.loads(host.read_text(encoding='utf-8'))
assert dispatch['exit'] == 1 and dispatch['dispatcher_pid'] == 36588 and dispatch['wsl_pid'] == 7720
with (HERE / 'host-dispatch-finished.json').open('xb') as output:
    output.write(host.read_bytes())
probe = """from pathlib import Path
import datetime,json,os
matches=[]
for path in Path('/proc').iterdir():
    if not path.name.isdigit() or int(path.name)==os.getpid():
        continue
    try:
        executable=(path/'exe').resolve(strict=True)
        if executable.name in {'replay-tests','observer','efsn'}:
            matches.append({'pid':int(path.name),'executable':str(executable)})
    except (OSError,RuntimeError):
        pass
print(json.dumps({'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'matching_processes':matches,'free_bytes':{q:os.statvfs(q).f_bavail*os.statvfs(q).f_frsize for q in ('/home/rehearsal/results','/mnt/d')}}))
"""
argv = ['wsl.exe', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--', 'python3', '-c', probe]
capacity = json.loads(subprocess.check_output(argv, text=True, encoding='utf-8', timeout=45))
assert capacity['matching_processes'] == []
module_path = ATTEMPT / 'inputs/replay_monitor.py'
spec = importlib.util.spec_from_file_location('completion_monitor', module_path)
monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)
proposal = {'mode': 'resume', 'start_height': 6600000, 'end_height': 6900000, 'limits': dict(run['replay_limits'], max_bytes=39 * 1024**3)}
floors = monitor.require_starting_capacity(proposal, {name: 2**63 for name in capacity['free_bytes']}, verification['closed_allocated_bytes'])
try:
    monitor.require_starting_capacity(proposal, capacity['free_bytes'], verification['closed_allocated_bytes'])
    gate = {'passed': True}
except ValueError as error:
    gate = {'passed': False, 'reason': str(error)}
replay = next(item for item in run['commands'] if item['name'] == 'replay')
wall = (datetime.datetime.fromisoformat(replay['finished']) - datetime.datetime.fromisoformat(replay['started'])).total_seconds()
result = {
    'reviewed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'verification_followup_passed': True,
    'original_automatic_verification_still_failed': True,
    'new_blocks': 300000,
    'post_legacy_blocks': 3920000,
    'remaining_blocks_to_backup_tip': 8530080,
    'replay_wall_seconds': wall,
    'replay_monotonic_seconds': replay['monotonic_seconds'],
    'clock_difference_cause': 'not established',
    'closed_allocated_bytes': verification['closed_allocated_bytes'],
    'interval_growth_bytes': verification['closed_allocated_bytes'] - run['existing_allocated_bytes'],
    'additional_preservation_checks': run['additional_preservation_checks'],
    'fresh_capacity': capacity,
    'capacity_probe_argv': argv,
    'proposed_next_job_not_prepared_or_launched': proposal,
    'starting_floors_bytes': floors,
    'capacity_gate': gate,
    'controller_sha256': hashlib.sha256(module_path.read_bytes()).hexdigest(),
    'continuation_provenance_gate': 'Existing controller refuses original failed completion; explicit separately verified qualification support is required before any resumed writer',
    'database_files_opened_or_hashed_by_this_review': False,
}
with (HERE / 'capacity-review.json').open('x', encoding='utf-8', newline='\n') as output:
    output.write(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
