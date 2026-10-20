"""Review closed records only. This does not open any database or image."""
from pathlib import Path
import datetime
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
COPY = HERE.parent / 'restart-restored-backup-copy-2026-10-19'
GIB = 1024**3


def read(name):
    return json.loads((HERE / name).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


counts = {}
for manifest, pin in [
    ('INPUT_SHA256SUMS', 'bc33b0a0378c8a414cd51e2c020dd255a0e87102ab80837d8e36ed33758e905d'),
    ('START_SHA256SUMS', '2a2fef6834a7d399597ecacfcda6aa81d541b4dfc45f0096d0d0f5d76f597bbc'),
]:
    assert sha(HERE / manifest) == pin
    lines = (HERE / manifest).read_text(encoding='utf-8').splitlines()
    for line in lines:
        digest, name = line.split(None, 1)
        assert sha(HERE / name) == digest, name
    counts[manifest] = len(lines)
commands = []
for path in sorted(HERE.glob('*.json')):
    record = read(path.name)
    if isinstance(record, dict) and 'exit' in record:
        assert record['exit'] == 0, path.name
        commands.append(path.name)
assert read('completion.json')['verified_pass']
assert not read('completion.json')['automatic_replay']
accepted, verified, env = read('acceptance.json'), read('verification.json'), read('environment.json')
assert accepted['pass'] and verified['pass']
assert accepted['original_backup_retained'] and not accepted['selected_release_changed']
assert accepted['protected_unchanged'] == env['protected_before']
assert env['netns'] != env['parent_netns']
assert len(env['interfaces']) == 1 and env['interfaces'][0]['ifname'] == 'lo'
assert env['interfaces'][0]['operstate'] == 'DOWN' and 'UP' not in env['interfaces'][0]['flags']
assert read('cleanup.json')['mounts_removed'] and read('cleanup.json')['loop_detached']
assert read('cleanup.json')['protected_metadata_unchanged']
assert not read('host-post-state.json')['dispatch_pid_present']
state = read('post-state.json')
assert not state['busy_processes'] and not state['matching_mounts']
assert not state['test_or_ext4_loopdevices']
for loop in state['loopdevices']:
    assert loop['ro'] and loop['autoclear']
    assert loop['back-file'].startswith('/mnt/docker-desktop-disk/isocache/entries/')
    assert '.iso/' in loop['back-file']
assert read('post-state-refusal.json')['supplemental_assertion_failed']
for mode in ['prehash', 'cli', 'cold']:
    record = read(mode + '-preservation.json')
    assert record['pass'] and record['backup_metadata_unchanged']
    assert record['identities'] == env['identities']
assert env['identities']['cli_sha256'] == '07aa74a3f58132e5ff1465152402d5ea3b01738c0017af5dfd5672a75a2550cd'
assert env['identities']['source_files'] == 1208
assert env['identities']['source_inventory_sha256'] == 'c751561c34e4a6546e3882880cbc64aafa221135772a6879cb0f799d7f992a4c'
assert env['identities']['profile_sha256'] == sha(HERE / 'profile.json')
assert read('controls.json')['pass'] and not read('controls.json')['database_opened']
assert sha(COPY / 'backup-SHA256SUMS') == 'a41ebd5f4f250cbb22b7c0d9ac484b7b1a503d6bc6ff7ff57cec97915cbe88c6'
backup_hashes = {}
for line in (COPY / 'backup-SHA256SUMS').read_text(encoding='utf-8').splitlines():
    digest, name = line.split(None, 1)
    assert name.startswith('./')
    backup_hashes[name[2:]] = digest
before_hashes, after_hashes = read('before-startup-hashes.json'), read('post-startup-hashes.json')
assert before_hashes == backup_hashes and len(before_hashes) == 56107
before_meta, after_meta = read('before-startup-metadata.json'), read('post-startup-metadata.json')
assert before_meta == json.loads((COPY / 'source-metadata.json').read_text(encoding='utf-8-sig'))
assert set(after_meta) == set(after_hashes) and len(after_hashes) == verified['files_hashed'] == 56168
assert sha(HERE / 'post-startup-hashes.json') == verified['closed_hash_inventory_sha256'] == '9af3c403a41e439eaf396a620a65f0d3621cc18c6944acc6d76dc0dec1eee7fc'
assert verified['read_only_metadata_unchanged']
expected = read('expected-endpoint.json')
prior = json.loads((HERE.parent / 'restart-ticket-encoder-w-15130080-2026-10-19/verification.json').read_text(encoding='utf-8-sig'))
assert verified['endpoint'] == expected == prior['endpoint']
assert expected['Number'] == 15130080
want = dict(head=expected['Number'], hash=expected['Hash'], root=expected['Root'],
            tickets=expected['TicketCommitment'], mining=False, autoBuy=False)
observations = []
for name in ['restored', 'restarted']:
    output = (HERE / (name + '.stdout.txt')).read_text(encoding='utf-8')
    errors = (HERE / (name + '.stderr.txt')).read_text(encoding='utf-8')
    entries = [json.loads(line[len('RESTOREDCLI '):]) for line in output.splitlines()
               if line.startswith('RESTOREDCLI ')]
    assert entries == [want], name
    assert errors.index('readonly=true') < errors.index('Initialising Ethereum protocol')
    assert 'Blockchain manager stopped' in errors
    writes = [int(n.replace(',', '')) for n in re.findall(r'Writing cached state to disk[^\n]*block=([0-9,]+)', errors)]
    assert writes == [15130080, 15130079, 15129953]
    assert all(bad not in errors for bad in ['panic:', 'Failed to commit recent state trie', 'Dangling trie nodes', 'CRIT ', 'Fatal:'])
    observations.append(dict(phase=name, observation=entries[0], shutdown_heights=writes))
cli = read('cli-result.json')
assert cli['pass'] and cli['normal_pruning'] and cli['test_anchor_only'] and not cli['real_keys_present']
assert cli['observations'] == observations and cli == verified['cli_result']
for name, test in [('cold-head', 'TestPreservedReplayHeadReadOnly'), ('cold-details', 'TestCandidateReplayColdDetails')]:
    log = (HERE / (name + '.stdout.txt')).read_text(encoding='utf-8')
    assert '--- SKIP:' not in log and ('--- PASS: ' + test + ' (') in log
assert 'closed replay matched: height=15130080 ' in (HERE / 'cold-head.stdout.txt').read_text(encoding='utf-8')
matches = re.findall(r'candidate endpoint observation: (\{.*\})', (HERE / 'cold-details.stdout.txt').read_text(encoding='utf-8'))
assert len(matches) == 1 and json.loads(matches[0]) == expected
for label, readonly in [('initial-readonly', True), ('writable', False), ('cold', True)]:
    prefix = 'reattach-' if label == 'cold' else 'attach-'
    loop = read(prefix + label + '-identity.stdout.txt')['loopdevices']
    assert len(loop) == 1 and loop[0]['back-file'] == env['image'] and loop[0]['ro'] is readonly
uuid = '0b18a87d-e8ee-413f-b37f-01eec39b0c48'
assert accepted['uuid'] == uuid
for name in ['initial', 'writable', 'cold']:
    assert (HERE / ('uuid-' + name + '.stdout.txt')).read_text(encoding='utf-8').strip() == uuid
rows = [json.loads(line) for line in (HERE / 'progress.jsonl').read_text(encoding='utf-8').splitlines()]
minimum = {path: min(row['free_bytes'][path] for row in rows) for path in rows[0]['free_bytes']}
for path, gib in [('/home/rehearsal', 20), ('/mnt/d', 50), ('/mnt/w', 100), ('image', 20)]:
    assert minimum[path] > gib * GIB
assert all(row['elapsed_seconds'] < 12600 for row in rows)
assert rows[-1]['phase'] == 'cold-details-closed'
durations = {}
for name, limit in [('prehash', 12720), ('cli', 1500), ('cold', 12720),
                    ('restored', 620), ('restarted', 620), ('cold-head', 310), ('cold-details', 310),
                    ('host-run', 28820)]:
    record = read(name + '.json')
    seconds = (datetime.datetime.fromisoformat(record['finished']) - datetime.datetime.fromisoformat(record['started'])).total_seconds()
    assert 0 <= seconds < limit, name
    durations[name] = seconds
assert accepted['elapsed_seconds'] < 28800
result = {
    'pass': True, 'reviewed': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'manifest_entries': counts, 'zero_exit_records': commands,
    'original_files': len(before_hashes), 'post_startup_files': len(after_hashes),
    'original_bytes': sum(item['size'] for item in before_meta.values()),
    'post_startup_bytes': sum(item['size'] for item in after_meta.values()),
    'new_files': len(set(after_hashes) - set(before_hashes)),
    'removed_files': len(set(before_hashes) - set(after_hashes)),
    'changed_retained_files': sum(before_hashes[name] != after_hashes[name] for name in before_hashes.keys() & after_hashes.keys()),
    'actual_cli_and_cold_tests_passed': True, 'protected_metadata_unchanged': True,
    'input_and_start_manifests_unchanged': True, 'post_job_detached': True,
    'unrelated_docker_iso_loops_recorded': True, 'supplemental_failed_assertion_preserved': True,
    'resource_samples': len(rows), 'minimum_sampled_free_bytes': minimum,
    'limits_passed': True, 'recorded_wall_seconds': durations,
    'monotonic_job_seconds': accepted['elapsed_seconds'],
    'clock_note': 'Host wall duration and Linux monotonic duration differ; host finish precedes Linux completion by about one second. Retain both without assuming synchronized clocks.',
}
with (HERE / 'review.json').open('x', encoding='utf-8') as output:
    output.write(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
