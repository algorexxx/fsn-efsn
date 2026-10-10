from pathlib import Path
import datetime, hashlib, importlib.util, json, subprocess, sys

sys.dont_write_bytecode = True
bundle = Path('docs/evidence/restart-ticket-encoder-job-6300000-v3-2026-10-10')
counts = {}
for name in ['inputs/SHA256SUMS', 'PREPARED_SHA256SUMS', 'LAUNCH_SHA256SUMS', 'STATUS_SHA256SUMS', 'OUTPUT_SHA256SUMS', 'SHA256SUMS']:
    path = bundle / name
    lines = path.read_text(encoding='utf-8').splitlines()
    for line in lines:
        digest, relative = line.split(None, 1)
        assert hashlib.sha256((path.parent / relative).read_bytes()).hexdigest() == digest, relative
    counts[name] = {'entries': len(lines), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
run = json.loads((bundle / 'qualification/run.json').read_text(encoding='utf-8'))
verification = json.loads((bundle / 'verification.json').read_text(encoding='utf-8'))
completion = json.loads((bundle / 'completion.json').read_text(encoding='utf-8'))
assert completion['exit'] == 0 and completion['verified_pass'] and verification['pass'] and run['completed']
assert len(run['commands']) == 7 and all(item['exit'] == 0 for item in run['commands'])
assert all(run['additional_preservation_checks'].values()) and not run.get('failures') and not run.get('stop_reason')
probe = "import json,os,datetime; print(json.dumps({'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'free_bytes':{q:os.statvfs(q).f_bavail*os.statvfs(q).f_frsize for q in ('/home/rehearsal/results','/mnt/d')}}))"
capacity = json.loads(subprocess.check_output(['wsl.exe', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--', 'python3', '-c', probe], text=True))
module_path = bundle / 'inputs/replay_monitor.py'
spec = importlib.util.spec_from_file_location('completion_monitor', module_path)
monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)
proposal = {'mode': 'resume', 'start_height': 6300000, 'end_height': 6600000, 'limits': dict(run['replay_limits'], max_bytes=34 * 1024**3)}
floors = monitor.require_starting_capacity(proposal, {name: 2**63 for name in capacity['free_bytes']}, verification['closed_allocated_bytes'])
try:
    monitor.require_starting_capacity(proposal, capacity['free_bytes'], verification['closed_allocated_bytes'])
    gate = {'passed': True}
except ValueError as error:
    gate = {'passed': False, 'reason': str(error)}
root = Path('D:/FusionRehearsal')
disk = root / 'Ubuntu/ext4.vhdx'
swap = root / 'swap/swap.vhdx'
replay = next(item for item in run['commands'] if item['name'] == 'replay')
wall = (datetime.datetime.fromisoformat(replay['finished']) - datetime.datetime.fromisoformat(replay['started'])).total_seconds()
result = {'reviewed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'completed_evidence_passed': True, 'manifests': counts, 'completion': completion, 'new_blocks': 323136, 'post_legacy_blocks': 3620000, 'replay_wall_seconds': wall, 'replay_monotonic_seconds': replay['monotonic_seconds'], 'clock_difference_cause': 'not established', 'additional_preservation_checks': run['additional_preservation_checks'], 'fresh_capacity': capacity, 'd_root_names': sorted(path.name for path in root.iterdir()), 'vhd': {'path': str(disk), 'length': disk.stat().st_size}, 'swap': {'path': str(swap), 'length': swap.stat().st_size}, 'proposed_next_job_not_prepared_or_launched': proposal, 'starting_floors_bytes': floors, 'capacity_gate': gate, 'controller_sha256': hashlib.sha256(module_path.read_bytes()).hexdigest(), 'database_files_opened_or_hashed_by_this_review': False}
with (bundle / 'post-completion-review.json').open('x', encoding='utf-8', newline='\n') as output:
    output.write(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
