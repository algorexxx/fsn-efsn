import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
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
    validate_prior_followup(config)
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


def require_observer_change(config, prior_inputs, inputs):
    original = (prior_inputs/'details_test.go').read_bytes()
    changed = (inputs/'details_test.go').read_bytes()
    old = ('const height = uint64('+str(config['start_height'])+')').encode()
    new = ('const height = uint64('+str(config['end_height'])+')').encode()
    if original.count(old) != 1 or changed != original.replace(old, new, 1):
        raise ValueError('observer must change exactly one height literal')
    expected = ''.join(difflib.unified_diff(original.decode('utf-8').splitlines(True), changed.decode('utf-8').splitlines(True), fromfile='a/details_test.go', tofile='b/details_test.go'))
    if (inputs/'observer-change.patch').read_bytes() != expected.encode('utf-8'):
        raise ValueError('observer patch must use the canonical filenames and exact source diff')


def validate_prior_followup(config):
    fields = {'prior_verification_bundle', 'prior_verification_sha256'}
    present = fields.intersection(config)
    if not present:
        return
    if present != fields or 'stopped_attempt' in config:
        raise ValueError('separate verification requires both pinned fields and no stopped attempt')
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]+', config['prior_verification_bundle']) or not re.fullmatch(r'[0-9a-f]{64}', config['prior_verification_sha256']):
        raise ValueError('invalid separate verification identity')
    if config['prior_verification_bundle'] == config['prior_bundle']:
        raise ValueError('verification follow-up must preserve a distinct original attempt')


def require_completed_prior(config, prior_directory):
    validate_prior_followup(config)
    if prior_directory.name != config['prior_bundle']:
        raise ValueError('prior directory identity differs')
    completion = json.loads((prior_directory/'completion.json').read_text(encoding='utf-8'))
    if 'prior_verification_bundle' not in config:
        require_verified_prior(config, completion, json.loads((prior_directory/'verification.json').read_text(encoding='utf-8')))
        return {}
    followup = prior_directory.parent/config['prior_verification_bundle']
    require_manifest_files(followup, config['prior_verification_sha256'])
    review = json.loads((followup/'review.json').read_text(encoding='utf-8'))
    verification = json.loads((followup/'verification.json').read_text(encoding='utf-8'))
    require_manifest_files(prior_directory, review['original_manifests_before_and_after']['SHA256SUMS']['sha256'])
    run = json.loads((prior_directory/'qualification/run.json').read_text(encoding='utf-8'))
    flags = ['pass', 'original_evidence_unchanged', 'source_change_exactly_one_height_literal', 'patch_difference_exactly_two_filename_headers', 'all_original_verifier_assertions_retained']
    if any(review.get(name) is not True for name in flags):
        raise ValueError('separate evidence review is incomplete')
    if review.get('original_completion') != completion or completion.get('exit') != 1 or completion.get('verified_pass') is not False:
        raise ValueError('original verifier failure must remain unchanged')
    if completion.get('job') != config['prior_bundle'] or completion.get('requested_end') != config['start_height'] or verification.get('end_height') != config['start_height'] or verification.get('pass') is not True:
        raise ValueError('separate verification endpoint or attempt differs')
    if not all(run.get(name) is True for name in ['completed', 'replay_passed', 'inspect_passed', 'cold_target_bytes_unchanged']) or run.get('failures') or run.get('stop_reason'):
        raise ValueError('separate verification requires completed replay and cold checks')
    if (prior_directory/'qualification/STOP').exists() or (prior_directory/'verification.json').exists():
        raise ValueError('separate verification cannot replace or reinterpret original evidence')
    if verification.get('endpoint') != run.get('endpoint_observations', {}).get('cold-details') or verification.get('replay_binary_sha256') != run.get('binary_sha256'):
        raise ValueError('separate verification result differs from recorded execution')
    if not run.get('target_before_cold_sha256') or not run.get('additional_preservation_checks') or not all(value is True for value in run['additional_preservation_checks'].values()):
        raise ValueError('separate verification requires preserved checkpoint and identities')
    return {followup.name: config['prior_verification_sha256']}


def require_manifest_files(directory, expected_digest):
    manifest = directory/'SHA256SUMS'
    if hashlib.sha256(manifest.read_bytes()).hexdigest() != expected_digest:
        raise ValueError('evidence manifest identity differs')
    for line in manifest.read_text(encoding='utf-8').splitlines():
        digest, relative = line.split(None, 1)
        path = (directory/relative).resolve()
        if not path.is_relative_to(directory.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('evidence file identity differs: '+relative)


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
    if not run.get('target_before_cold_sha256'):
        raise ValueError('stopped checkpoint inventory is required')
    if run.get('stop_kind') == 'host-reserve':
        evidence = run.get('stop_evidence_sha256', {})
        if set(evidence) != {'completion.json', 'qualification/replay.stdout.txt', 'qualification/run.json'} or not all(isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) for value in evidence.values()):
            raise ValueError('native reserve stop requires exact failure evidence identities')
        if run.get('stop_sha256') or verification.get('stop_kind') != 'host-reserve' or run.get('discovery_expected_refusal') is not True or verification.get('discovery_expected_refusal') is not True:
            raise ValueError('native reserve stop must preserve its distinct discovery provenance')
        return
    if run.get('stop_kind') is not None or not re.fullmatch(r'[0-9a-f]{64}', run.get('stop_sha256', '')):
        raise ValueError('stopped checkpoint STOP identity is required')


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
    closed_measurement = helper.allocated_size
    helper.allocated_size = lambda: measure_live_allocation(helper)
    try:
        run_monitored(helper, command, helper.RUN/'node/tests/restart', env, limits)
    finally:
        helper.allocated_size = closed_measurement
    helper.record['replay_passed'] = True
    helper.record['closed_allocated_bytes'] = helper.allocated_size()
    if helper.record['closed_allocated_bytes'] is None:
        raise RuntimeError('closed allocation measurement failed')
    (helper.RUN/'replay-identity.json').write_bytes((helper.TARGET/'replay-identity.json').read_bytes())


def write_atomic(path, data):
    temporary = Path(str(path)+'.tmp')
    temporary.write_text(data, encoding='utf-8')
    os.replace(temporary, path)


def allocated_blocks(directory):
    descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        root = os.fstat(descriptor)
        allocated = root.st_blocks * 512
        seen = {(root.st_dev, root.st_ino)}
        vanished = []
        with os.scandir(descriptor) as entries:
            for entry in entries:
                try:
                    info = entry.stat(follow_symlinks=False)
                except FileNotFoundError:
                    if not re.fullmatch(r'(?:[0-9]+\.(?:ldb|sst|log|tmp)|MANIFEST-[0-9]+)', entry.name):
                        raise
                    vanished.append(entry.name)
                    continue
                if not stat.S_ISREG(info.st_mode) or info.st_dev != root.st_dev:
                    raise ValueError('allocation scan requires regular files on the target filesystem')
                identity = (info.st_dev, info.st_ino)
                if identity not in seen:
                    allocated += info.st_blocks * 512
                    seen.add(identity)
        final = os.stat(directory, follow_symlinks=False)
        if (final.st_dev, final.st_ino) != (root.st_dev, root.st_ino):
            raise ValueError('allocation target directory changed')
        allocated += max(0, final.st_blocks - root.st_blocks) * 512
        return {'path':str(directory), 'allocated_bytes':allocated, 'vanished_entries':vanished}
    finally:
        os.close(descriptor)


def measure_live_allocation(helper):
    command = ['timeout','--kill-after=2s','15s',sys.executable,'-B',str(Path(__file__).resolve()),'--allocated-size',str(helper.TARGET)]
    for attempt in range(1,4):
        measured = subprocess.run(command,capture_output=True,text=True)
        entry = {'time':helper.now(),'attempt':attempt,'exit':measured.returncode,
                 'stdout':'','stderr':measured.stderr,'method':'stat-blocks-v1',
                 'scanner_stdout':measured.stdout,'argv':command}
        value = None
        if measured.returncode == 0:
            try:
                result = json.loads(measured.stdout)
                if result['path'] == str(helper.TARGET) and type(result['allocated_bytes']) is int and result['allocated_bytes'] >= 0 and isinstance(result['vanished_entries'],list):
                    value = result['allocated_bytes']
                    entry['stdout'] = str(value)+'\t'+str(helper.TARGET)+'\n'
            except (ValueError,KeyError,TypeError):
                pass
        helper.record['size_measurements'].append(entry)
        helper.save()
        if value is not None:
            return value
        time.sleep(1)
    return None


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] != '--allocated-size':
        raise ValueError('expected --allocated-size and one target directory')
    print(json.dumps(allocated_blocks(Path(sys.argv[2]))))
