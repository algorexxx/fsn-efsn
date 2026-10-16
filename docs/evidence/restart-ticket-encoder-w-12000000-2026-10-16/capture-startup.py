from pathlib import Path
import datetime
import json

bundle = Path(__file__).resolve().parent
config = json.loads((bundle / 'inputs/config.json').read_text(encoding='utf-8'))
runtime = Path('/home/rehearsal/results') / config['job']
record = json.loads((runtime / 'run.json').read_text(encoding='utf-8'))
assert record['uid'] == 1000
assert record['namespace'] != record['parent_namespace']
assert record['mount_namespace'] != record['parent_mount_namespace']
assert len(record['links'].splitlines()) == 1 and 'lo ' in record['links'] and 'DOWN' in record['links']
assert record['storage_mount']['image'] == config['storage']['image']
assert record['storage_mount']['uuid'] == config['storage']['uuid']
assert all(record['capacity_bytes'][p] > value for p, value in record['required_capacity_bytes'].items())
prior = json.loads((bundle.parent / config['prior_bundle'] / 'verification.json').read_text(encoding='utf-8'))
assert prior['pass'] and prior['end_height'] == config['start_height']
allocation = {'prior_closed_allocated_bytes': prior['closed_allocated_bytes'],
              'startup_allocated_bytes': record['existing_allocated_bytes'],
              'difference_bytes': record['existing_allocated_bytes'] - prior['closed_allocated_bytes'],
              'cause_established': False,
              'exact_file_inventory_verification_required_before_replay': True}
assert not record.get('failures')
keys = ['started', 'uid', 'namespace', 'mount_namespace', 'parent_namespace',
        'parent_mount_namespace', 'links', 'target', 'capacity_bytes', 'existing_allocated_bytes',
        'required_capacity_bytes', 'storage_mount', 'phase', 'replay_pid', 'commands', 'failures']
observation = {'observed': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'allocation_observation': allocation,
               **{key: record.get(key) for key in keys}}
with (bundle / 'startup-observation.json').open('x', encoding='utf-8', newline='\n') as output:
    output.write(json.dumps(observation, indent=2) + '\n')
print(json.dumps(observation, indent=2))
