import os
from pathlib import Path
import re
import subprocess
import time


def validate_limits(limits):
    if not 0 < limits['clean_seconds'] < limits['go_seconds'] < limits['outer_seconds']:
        raise ValueError('require clean-stop < Go timeout < outer timeout')
    if limits['max_bytes'] <= 0 or limits['sample_seconds'] <= 0:
        raise ValueError('storage allowance and sample interval must be positive')


def validate_configuration(config):
    validate_limits(config['limits'])
    for name in ['job', 'prior_bundle', 'recovery_bundle', 'checkpoint', 'target', 'recovery_checkpoint']:
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]+', config[name]):
            raise ValueError('invalid path component: '+name)
    if 'stopped_attempt' in config and not re.fullmatch(r'[a-z0-9][a-z0-9-]+', config['stopped_attempt']):
        raise ValueError('invalid stopped attempt path component')
    if not 0 < config['start_height'] < config['end_height'] <= 15130080:
        raise ValueError('invalid historical interval')
    if config['mode'] not in ['copy', 'resume']:
        raise ValueError('unknown checkpoint mode')
    same = config['checkpoint'] == config['target']
    if same != (config['mode'] == 'resume') or config['target'] == config['recovery_checkpoint']:
        raise ValueError('working target must preserve the recovery checkpoint')


def request_stop(helper, reason):
    if not helper.STOP.exists():
        with helper.STOP.open('x', encoding='utf-8') as output:
            output.write(reason+'\n')
    helper.record.setdefault('stop_reason', reason)
    helper.save()


def require_starting_capacity(config, capacity, existing_bytes):
    if existing_bytes < 0 or existing_bytes >= config['limits']['max_bytes']:
        raise ValueError('existing target leaves no declared growth allowance')
    if config['mode'] == 'copy' and existing_bytes:
        raise ValueError('copy mode requires an absent target')
    growth = config['limits']['max_bytes']-existing_bytes
    gib = 1024**3
    required = {'/home/rehearsal/results':max(30*gib if config['mode'] == 'copy' else 0, 21*gib+growth),
                '/mnt/d':max(60*gib, 51*gib+growth)}
    for path, floor in required.items():
        if capacity[path] <= floor:
            raise ValueError('insufficient starting capacity: '+path)
    return required


def require_verified_prior(config, completion, verification):
    if not completion.get('verified_pass') or completion.get('exit') != 0 or not verification.get('pass'):
        raise ValueError('prior job must have passed its evidence verifier')
    if completion.get('requested_end') != config['start_height'] or verification.get('end_height') != config['start_height']:
        raise ValueError('prior verified endpoint must equal requested start')


def require_verified_stopped(config, run, verification, attempt_completion):
    checks = {'backup_metadata_unchanged', 'baseline_metadata_unchanged',
              'checkpoint_bytes_unchanged', 'target_bytes_unchanged',
              'selected_unchanged', 'candidate_unchanged', 'replay_binary_unchanged',
              'stop_unchanged', 'inputs_unchanged', 'imported_runner_unchanged',
              'observer_unchanged', 'overlay_unchanged'}
    preserved = run.get('preservation_checks', {})
    if not run.get('completed') or not run.get('inspect_passed') or run.get('failures'):
        raise ValueError('stopped checkpoint inspection must be complete')
    if set(preserved) != checks or not all(value is True for value in preserved.values()):
        raise ValueError('stopped checkpoint preservation checks must all pass')
    if verification.get('pass') is not True or verification.get('attempt_completed') is not False:
        raise ValueError('inspection must pass without reclassifying the stopped attempt')
    if run.get('inspection_height') != config['start_height'] or verification.get('cold_verified_height') != config['start_height']:
        raise ValueError('cold verified endpoint must equal requested start')
    if attempt_completion.get('verified_pass') is not False or attempt_completion.get('exit') in [None, 0]:
        raise ValueError('stopped attempt must retain its unsuccessful completion')
    if attempt_completion.get('job') != config['stopped_attempt'] or attempt_completion.get('requested_end') != verification.get('requested_height') or run.get('requested_attempt_height') != verification.get('requested_height'):
        raise ValueError('stopped attempt identity or requested height differs')
    if verification.get('endpoint') != run.get('endpoint_observations', {}).get('cold-details'):
        raise ValueError('stopped checkpoint endpoint differs from verified observation')
    if not run.get('target_before_cold_sha256') or not re.fullmatch(r'[0-9a-f]{64}', run.get('stop_sha256', '')):
        raise ValueError('stopped checkpoint inventory and STOP identity are required')


def run_monitored(helper, command, cwd, env, limits):
    validate_limits(limits)
    if helper.STOP.exists():
        raise FileExistsError('preserve existing stop marker; use a new result directory')
    entry = {'name':'replay', 'argv':command, 'cwd':str(cwd), 'started':helper.now()}
    start = time.monotonic()
    next_measurement = start
    with (helper.RUN/'replay.stdout.txt').open('xb') as output, (helper.RUN/'replay.stderr.txt').open('xb') as errors:
        process = subprocess.Popen(command, cwd=cwd, env=env, stdout=output, stderr=errors)
        helper.record['replay_pid'] = process.pid
        helper.record['replay_started'] = entry['started']
        helper.save()
        try:
            while process.poll() is None:
                if helper.STOP.exists():
                    helper.record.setdefault('stop_reason', 'external stop marker observed')
                if time.monotonic()-start >= limits['clean_seconds']:
                    request_stop(helper, 'declared clean-stop allowance reached')
                if time.monotonic() >= next_measurement:
                    size = helper.allocated_size()
                    if size is None:
                        request_stop(helper, 'size monitor failed all three bounded attempts')
                    elif size >= limits['max_bytes']:
                        request_stop(helper, 'declared target allocation allowance reached')
                    next_measurement = time.monotonic()+limits['sample_seconds']
                try:
                    process.wait(timeout=min(1, limits['sample_seconds']))
                except subprocess.TimeoutExpired:
                    pass
        finally:
            if process.poll() is None:
                request_stop(helper, 'runner interrupted; retain partial target')
                process.wait()
        entry['exit'] = process.returncode
    entry['finished'] = helper.now()
    entry['monotonic_seconds'] = time.monotonic()-start
    helper.record['commands'].append(entry)
    helper.save()
    if entry['exit'] or helper.STOP.exists():
        raise RuntimeError('replay stopped or failed; no automatic retry')


def run_replay(helper, env, limits):
    command = ['timeout', '--kill-after=20s', str(limits['outer_seconds'])+'s',
               str(helper.RUN/'bin/replay-tests'), '-test.run=^TestPreservedHistoryReplay$',
               '-test.v', '-test.count=1', '-test.timeout='+str(limits['go_seconds'])+'s']
    env = dict(env, FUSION_RESTART_REPLAY_DIR=str(helper.TARGET), FUSION_RESTART_REPLAY_STOP_FILE=str(helper.STOP))
    run_monitored(helper, command, helper.RUN/'node/tests/restart', env, limits)
    helper.record['replay_passed'] = True
    helper.record['closed_allocated_bytes'] = helper.allocated_size()
    if helper.record['closed_allocated_bytes'] is None:
        raise RuntimeError('closed allocation measurement failed')
    (helper.RUN/'replay-identity.json').write_bytes((helper.TARGET/'replay-identity.json').read_bytes())


def write_atomic(path, data):
    temporary = Path(str(path)+'.tmp')
    temporary.write_text(data, encoding='utf-8')
    os.replace(temporary, path)
