from pathlib import Path
import datetime
import hashlib
import json

BUNDLE = Path(__file__).resolve().parent.parent
POST = BUNDLE / 'post-completion'


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def check_manifest(path):
    lines = path.read_text(encoding='utf-8').splitlines()
    for line in lines:
        digest, relative = line.split(None, 1)
        assert hashlib.sha256((path.parent / relative).read_bytes()).hexdigest() == digest, relative
    return {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'files_verified': len(lines)}


checks = {name: check_manifest(BUNDLE / name) for name in
          ['SHA256SUMS', 'OUTPUT_SHA256SUMS', 'PREPARED_SHA256SUMS', 'START_SHA256SUMS', 'inputs/SHA256SUMS']}
assert checks['inputs/SHA256SUMS']['sha256'] == '8db5f5bea414f6b9394234ddd5e5c12b9e7887d5f51dfcd39e738f117b9f34b4'
assert checks['PREPARED_SHA256SUMS']['sha256'] == 'b8b3a957af4b58eb46150f9b2aa22a7eac12a5290a3e51ee01938e73da2ed7f5'
assert checks['START_SHA256SUMS']['sha256'] == '42dad21c3b4d2e8814c460aaf798fcccf2f4ff4a9453568e53ae62a4f514063a'
r = read_json(BUNDLE / 'qualification/run.json')
v = read_json(BUNDLE / 'verification.json')
inner = read_json(BUNDLE / 'completion.json')
outer = read_json(BUNDLE / 'storage-completion.json')
host = read_json(POST / 'host-host-run.json')
state = read_json(POST / 'post-state.json')
assert inner['exit'] == outer['exit'] == host['exit'] == 0
assert inner['verified_pass'] and v['pass'] and r['completed']
assert outer['detached'] and outer['mounts_removed']
assert not inner['automatic_continuation'] and not outer['automatic_continuation']
assert not state['busy_processes'] and not state['replay_image_attachments'] and not state['matching_mounts'] and not state['target_directory_exists']
assert len(r['commands']) == 7 and all(c['exit'] == 0 for c in r['commands'])
assert all(r['additional_preservation_checks'].values()) and not r.get('failures') and not r.get('stop_reason')
assert all(r[k] for k in ['replay_passed', 'inspect_passed', 'cold_target_bytes_unchanged', 'backup_unchanged',
                          'baselines_unchanged', 'selected_unchanged', 'candidate_unchanged', 'inputs_unchanged'])
assert v['start_height'] == 7800000 and v['end_height'] == inner['requested_end'] == 8100000
assert r['binary_sha256'] == v['replay_binary_sha256'] == 'b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245'
assert r['observer_binary_sha256'] == v['observer_binary_sha256'] == '04f8099835d18fe4061c70add4f82ddad36f3e6c04b6d80a2e64921f1550dee3'
replay = next(c for c in r['commands'] if c['name'] == 'replay')
wall = (datetime.datetime.fromisoformat(replay['finished']) - datetime.datetime.fromisoformat(replay['started'])).total_seconds()
samples = r['storage_samples'] + [{'free_bytes': r['remaining_bytes']}]
minimum = {p: min(s['free_bytes'][p] for s in samples) for p in r['remaining_bytes']}
for p, gib in [('/home/rehearsal/results', 20), ('/mnt/d', 50), ('/mnt/w', 100), (r['target'], 20)]:
    assert minimum[p] > gib * 1024**3
assert v['closed_allocated_bytes'] == r['closed_allocated_bytes'] < r['replay_limits']['max_bytes']
assert v['target_files_hashed'] == len(r['target_before_cold_sha256'])
result = {'pass': True, 'reviewed': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'manifest_checks': checks, 'commands': len(r['commands']),
          'preservation_checks': len(r['additional_preservation_checks']),
          'target_files': len(r['target_before_cold_sha256']),
          'independent_recovery_files': len(r['recovery_checkpoint_sha256']), 'height': v['end_height'],
          'additional_blocks': v['end_height'] - v['start_height'],
          'post_legacy_blocks': v['end_height'] - v['legacy_checkpoint_end'],
          'remaining_to_backup_tip': 15130080 - v['end_height'],
          'replay_seconds_wall': wall, 'replay_seconds_monotonic': replay['monotonic_seconds'],
          'host_seconds_wall': (datetime.datetime.fromisoformat(host['finished']) - datetime.datetime.fromisoformat(host['started'])).total_seconds(),
          'closed_allocated_bytes': r['closed_allocated_bytes'],
          'allocation_growth_bytes': r['closed_allocated_bytes'] - r['existing_allocated_bytes'],
          'minimum_sampled_free_bytes': minimum, 'inner_verification_and_outer_cleanup_pass': True,
          'database_files_opened_or_hashed_by_this_review': False}
with (POST / 'review.json').open('x', encoding='utf-8', newline='\n') as output:
    output.write(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
