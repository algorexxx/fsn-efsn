from pathlib import Path
import datetime
import hashlib
import json

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text(encoding='utf-8-sig'))


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
assert not read('host-post-state.json')['dispatch_pid_present']
assert not state['busy_processes'] and not state['loopdevices'] and not state['matching_mounts']
copied, verified = read('copy-result.json'), read('verification.json')
assert copied['files'] == verified['files'] == 56107
assert copied['bytes'] == verified['bytes'] == 117170022674
assert copied['source_hashes_match_sealed_inventory'] and copied['source_metadata_unchanged']
assert verified['destination_hashes_match_sealed_inventory'] and verified['source_metadata_unchanged']
assert verified['destination_metadata_unchanged_after_cold_reads']
prior = json.loads((HERE.parent / 'restart-ticket-encoder-w-15130080-2026-10-19/verification.json').read_text(encoding='utf-8-sig'))
assert verified['endpoint'] == prior['endpoint']
assert verified['replay_binary_sha256'] == prior['replay_binary_sha256']
assert verified['observer_binary_sha256'] == prior['observer_binary_sha256']
assert (HERE / 'uuid.stdout.txt').read_bytes() == (HERE / 'uuid-reattached.stdout.txt').read_bytes()
for name, test in [('cold-head', 'TestPreservedReplayHeadReadOnly'), ('cold-details', 'TestCandidateReplayColdDetails')]:
    log = (HERE / (name + '.stdout.txt')).read_text(encoding='utf-8')
    assert '--- SKIP:' not in log and ('--- PASS: ' + test + ' (') in log, name
assert 'closed replay matched: height=15130080 ' in (HERE / 'cold-head.stdout.txt').read_text(encoding='utf-8')
assert hashlib.sha256((HERE / 'backup-SHA256SUMS').read_bytes()).hexdigest() == 'a41ebd5f4f250cbb22b7c0d9ac484b7b1a503d6bc6ff7ff57cec97915cbe88c6'
assert read('migration.json')['uuid'] == '0b18a87d-e8ee-413f-b37f-01eec39b0c48'
rows = [json.loads(line) for line in (HERE / 'progress.jsonl').read_text(encoding='utf-8').splitlines()]
minimum = {p: min(row['free_bytes'][p] for row in rows) for p in rows[0]['free_bytes']}
for path, gib in [('/home/rehearsal', 20), ('/mnt/d', 50), ('/mnt/w', 100)]:
    assert minimum[path] > gib * 1024**3
assert len(rows) == 463 and rows[-1]['phase'] == 'verified'
assert all(v > 20 * 1024**3 for p, v in minimum.items() if p.startswith('/tmp/'))
assert all(row['elapsed_seconds'] < 12600 for row in rows)
for name in ['copy', 'verify']:
    r=read(name + '.json')
    assert (datetime.datetime.fromisoformat(r['finished'])-datetime.datetime.fromisoformat(r['started'])).total_seconds() < 12720
assert read('migration.json')['elapsed_seconds'] < 28800
result = {'pass': True, 'reviewed': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'files': copied['files'], 'bytes': copied['bytes'], 'minimum_sampled_free_bytes': minimum,
          'source_retained': True, 'cold_endpoint_matches_prior': True,
          'input_and_start_manifests_unchanged': True, 'post_job_detached': True,
          'actual_cold_tests_passed': True, 'resource_samples': len(rows), 'limits_passed': True,
          'clock_note': 'Monotonic migration elapsed is 13924.078 seconds; wall duration is about 14873 seconds. Preserve both; clocks are not assumed synchronized.'}
with (HERE / 'review.json').open('x', encoding='utf-8') as output:
    output.write(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
