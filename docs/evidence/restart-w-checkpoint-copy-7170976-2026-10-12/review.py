from pathlib import Path
import datetime
import hashlib
import json

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


for manifest in ['INPUT_SHA256SUMS', 'START_SHA256SUMS']:
    for line in (HERE / manifest).read_text(encoding='utf-8').splitlines():
        digest, name = line.split(None, 1)
        assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest, name
for name in ['completion.json', 'host-run.json', 'copy.json', 'verify.json',
             'filesystem-check.json', 'cold-head.json', 'cold-details.json',
             'cleanup-image-unmount.json', 'cleanup-image-detach.json', 'cleanup-source-unmount.json']:
    assert read(name)['exit'] == 0, name
assert read('completion.json')['verified_pass'] and not read('completion.json')['automatic_replay']
assert read('migration.json')['pass'] and read('verification.json')['pass']
assert read('cleanup.json')['mounts_removed'] and read('cleanup.json')['loop_detached']
state = read('post-state.json')
assert not state['busy_processes'] and not state['loopdevices'] and not state['matching_mounts']
copied, verified = read('copy-result.json'), read('verification.json')
assert copied['files'] == verified['files'] == 22501
assert copied['bytes'] == verified['bytes'] == 47231339260
assert copied['source_hashes_match_sealed_inventory'] and copied['source_metadata_unchanged']
assert verified['destination_hashes_match_sealed_inventory'] and verified['source_metadata_unchanged']
assert verified['destination_metadata_unchanged_after_cold_reads']
prior = json.loads((HERE.parent / 'restart-ticket-encoder-stopped-7170976-2026-10-12/qualification/run.json').read_text(encoding='utf-8'))
assert verified['endpoint'] == prior['endpoint_observations']['cold-details']
assert verified['replay_binary_sha256'] == prior['binary_sha256']
assert verified['observer_binary_sha256'] == prior['observer_binary_sha256']
assert (HERE / 'uuid.stdout.txt').read_bytes() == (HERE / 'uuid-reattached.stdout.txt').read_bytes()
rows = [json.loads(line) for line in (HERE / 'progress.jsonl').read_text(encoding='utf-8').splitlines()]
minimum = {p: min(row['free_bytes'][p] for row in rows) for p in rows[0]['free_bytes']}
for path, gib in [('/home/rehearsal', 20), ('/mnt/d', 50), ('/mnt/w', 100)]:
    assert minimum[path] > gib * 1024**3
result = {'pass': True, 'reviewed': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'files': copied['files'], 'bytes': copied['bytes'], 'minimum_sampled_free_bytes': minimum,
          'source_retained': True, 'cold_endpoint_matches_prior': True,
          'input_and_start_manifests_unchanged': True, 'post_job_detached': True,
          'clock_note': 'Windows host-finish timestamp precedes final Linux completion by about two seconds; clocks are not treated as synchronized.'}
with (HERE / 'review.json').open('x', encoding='utf-8') as output:
    output.write(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
