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
assert checks['inputs/SHA256SUMS']['sha256'] == 'a8618aef240176cef0d5687c220ad186341d6031758ae9d59a51a9f88263e974'
assert checks['PREPARED_SHA256SUMS']['sha256'] == 'c9816a79dbe1cbb6e64e502be1ce096ecff461cd4bf4b1a773e10eb2393030fd'
assert checks['START_SHA256SUMS']['sha256'] == '67457f050e547f02efd658e47772ec3943432b3c502470daa5fbe86b4dd7b6dd'
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
assert v['start_height'] == 9900000 and v['end_height'] == inner['requested_end'] == 10200000
assert r['binary_sha256'] == v['replay_binary_sha256'] == 'b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245'
assert r['observer_binary_sha256'] == v['observer_binary_sha256'] == '7901fdc27e68fb4039368a55396a26ad72a71f38ef801cc3ccfb459774f0e8ab'
replay = next(c for c in r['commands'] if c['name'] == 'replay')
wall = (datetime.datetime.fromisoformat(replay['finished']) - datetime.datetime.fromisoformat(replay['started'])).total_seconds()
samples = r['storage_samples'] + [{'free_bytes': r['remaining_bytes']}]
minimum = {p: min(s['free_bytes'][p] for s in samples) for p in r['remaining_bytes']}
for p, gib in [('/home/rehearsal/results', 20), ('/mnt/d', 50), ('/mnt/w', 100), (r['target'], 20)]:
    assert minimum[p] > gib * 1024**3
assert v['closed_allocated_bytes'] == r['closed_allocated_bytes'] < r['replay_limits']['max_bytes']
assert v['target_files_hashed'] == len(r['target_before_cold_sha256'])
prior = read_json(BUNDLE.parent / r['configuration']['prior_bundle'] / 'qualification/run.json')
assert r['checkpoint_before_sha256'] == prior['target_before_cold_sha256']
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
          'database_files_opened_or_hashed_by_this_review': False,
          'starting_checkpoint_files_match_prior': True,
          'startup_allocation_delta_bytes': r['existing_allocated_bytes'] - prior['closed_allocated_bytes']}
with (POST / 'review.json').open('x', encoding='utf-8', newline='\n') as output:
    output.write(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
