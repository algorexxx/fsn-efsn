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
