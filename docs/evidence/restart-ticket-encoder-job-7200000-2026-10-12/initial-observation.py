import datetime
import hashlib
import json
from pathlib import Path

runtime = Path('/home/rehearsal/results/restart-ticket-encoder-job-7200000-2026-10-12')
bundle = Path('/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-ticket-encoder-job-7200000-2026-10-12')
raw = (runtime / 'run.json').read_bytes()
run = json.loads(raw)
status_raw = (runtime / 'status.json').read_bytes()
status = json.loads(status_raw)
assert run.get('resume_verified') and run.get('replay_started'), status
assert run.get('size_measurements') and not run.get('failures') and not run.get('stop_reason'), status
pid = run['replay_pid']
process = Path('/proc') / str(pid)
assert process.exists() and not (bundle / 'completion.json').exists()
observed = {
    'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'runtime': str(runtime),
    'source_commit': run['investigation_commit'],
    'run_record_sha256': hashlib.sha256(raw).hexdigest(),
    'status_record_sha256': hashlib.sha256(status_raw).hexdigest(),
    'status': status,
    'replay_started': run['replay_started'],
    'replay_pid': pid,
    'process_stat': (process / 'stat').read_text(),
    'process_command': (process / 'cmdline').read_bytes().replace(b'\0', b' ').decode(),
    'startup_commands': [{k: command[k] for k in ('name', 'started', 'finished', 'exit')} for command in run['commands']],
    'resume_verified': run['resume_verified'],
    'working_files_verified': len(run['checkpoint_before_sha256']),
    'recovery_files_verified': len(run['recovery_checkpoint_sha256']),
    'previous_files_verified': run['previous_files_verified'],
    'binary_sha256': run['binary_sha256'],
    'checkpoint_identity_sha256': run['checkpoint_identity_sha256'],
    'startup_capacity_bytes': run['capacity_bytes'],
    'latest_size_measurement': run['size_measurements'][-1],
    'isolation': {k: run[k] for k in ('namespace', 'mount_namespace', 'parent_namespace', 'parent_mount_namespace', 'links', 'backup_mount', 'checkpoint_mount', 'recovery_mount')},
    'replay_stdout_tail': (runtime / 'replay.stdout.txt').read_text(encoding='utf-8').splitlines()[-8:],
    'replay_stderr_tail': (runtime / 'replay.stderr.txt').read_text(encoding='utf-8').splitlines()[-8:],
    'coverage_remains_cold_verified_height': 6900000,
    'database_files_read_or_hashed_by_this_observation': False,
}
with (bundle / 'initial-observation.json').open('x', encoding='utf-8', newline='\n') as output:
    output.write(json.dumps(observed, indent=2) + '\n')
print(json.dumps(observed, indent=2))
