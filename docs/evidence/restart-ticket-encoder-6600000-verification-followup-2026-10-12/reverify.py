from pathlib import Path
import contextlib
import datetime
import difflib
import hashlib
import io
import json
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ATTEMPT = HERE.parent / 'restart-ticket-encoder-job-6600000-2026-10-11'
PRIOR = HERE.parent / 'restart-ticket-encoder-job-6300000-v3-2026-10-10'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_manifests():
    result = {}
    for name in ['inputs/SHA256SUMS', 'PREPARED_SHA256SUMS', 'LAUNCH_SHA256SUMS', 'STATUS_SHA256SUMS', 'OUTPUT_SHA256SUMS', 'SHA256SUMS']:
        manifest = ATTEMPT / name
        rows = manifest.read_text(encoding='utf-8').splitlines()
        for row in rows:
            digest, relative = row.split(None, 1)
            path = (manifest.parent / relative).resolve()
            assert path.is_relative_to(ATTEMPT.resolve()), relative
            assert sha(path) == digest, relative
        result[name] = {'entries': len(rows), 'sha256': sha(manifest)}
    return result


assert not (HERE / 'verification.json').exists()
assert not (HERE / 'review.json').exists()
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
before = verify_manifests()
completion = json.loads((ATTEMPT / 'completion.json').read_text(encoding='utf-8'))
assert completion['exit'] == 1 and completion['verified_pass'] is False
assert completion['requested_end'] == 6600000
assert not (ATTEMPT / 'verification.json').exists()
assert not (ATTEMPT / 'qualification/STOP').exists()
error = (ATTEMPT / 'verification.stderr.txt').read_text(encoding='utf-8')
assert error.endswith('AssertionError\n') and "assert (HERE/'observer-change.patch').read_text(encoding='utf-8') == patch" in error
old = (PRIOR / 'inputs/details_test.go').read_bytes()
assert old.count(b'const height = uint64(6300000)') == 1
new = old.replace(b'const height = uint64(6300000)', b'const height = uint64(6600000)', 1)
assert (ATTEMPT / 'inputs/details_test.go').read_bytes() == new
expected = ''.join(difflib.unified_diff(old.decode('utf-8').splitlines(keepends=True), new.decode('utf-8').splitlines(keepends=True), fromfile='a/details_test.go', tofile='b/details_test.go'))
recorded = (ATTEMPT / 'inputs/observer-change.patch').read_text(encoding='utf-8')
assert recorded.splitlines(keepends=True)[:2] == ['--- prior/details_test.go\n', '+++ inputs/details_test.go\n']
assert recorded.splitlines(keepends=True)[2:] == expected.splitlines(keepends=True)[2:]
assert recorded == expected.replace('--- a/details_test.go\n+++ b/details_test.go\n', '--- prior/details_test.go\n+++ inputs/details_test.go\n', 1)
original_path = ATTEMPT / 'inputs/replay_verify.py'
original = original_path.read_text(encoding='utf-8')
changes = {
    "fromfile='a/details_test.go',tofile='b/details_test.go'": "fromfile='prior/details_test.go',tofile='inputs/details_test.go'",
    "(BUNDLE/'verification.json').write_text": "(FOLLOWUP_DIR/'verification.json').write_text",
}
adapted = original
for old_text, new_text in changes.items():
    assert adapted.count(old_text) == 1
    adapted = adapted.replace(old_text, new_text, 1)
patch = ''.join(difflib.unified_diff(original.splitlines(keepends=True), adapted.splitlines(keepends=True), fromfile='a/replay_verify.py', tofile='b/replay_verify.py'))
with (HERE / 'verifier-change.patch').open('x', encoding='utf-8', newline='\n') as output:
    output.write(patch)
sys.path.insert(0, str(ATTEMPT / 'inputs'))
log = io.StringIO()
with contextlib.redirect_stdout(log):
    exec(compile(adapted, str(original_path), 'exec'), {'__file__': str(original_path), '__name__': '__main__', 'FOLLOWUP_DIR': HERE})
with (HERE / 'verification.stdout.txt').open('x', encoding='utf-8', newline='\n') as output:
    output.write(log.getvalue())
after = verify_manifests()
assert after == before
verification = json.loads((HERE / 'verification.json').read_text(encoding='utf-8'))
assert verification['pass'] is True and verification['end_height'] == 6600000
review = {
    'started': started,
    'finished': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'pass': True,
    'scope': 'Evidence-only verification of completed replay and existing cold checks; original automatic-verifier failure preserved',
    'original_completion': completion,
    'original_verifier_sha256': sha(original_path),
    'adapted_verifier_sha256': hashlib.sha256(adapted.encode('utf-8')).hexdigest(),
    'verifier_change_patch_sha256': sha(HERE / 'verifier-change.patch'),
    'source_change_exactly_one_height_literal': True,
    'patch_difference_exactly_two_filename_headers': True,
    'all_original_verifier_assertions_retained': True,
    'original_manifests_before_and_after': before,
    'original_evidence_unchanged': True,
    'database_files_opened_or_hashed': False,
    'replay_reexecuted': False,
    'automatic_continuation_authorized_by_this_result': False,
}
with (HERE / 'review.json').open('x', encoding='utf-8', newline='\n') as output:
    output.write(json.dumps(review, indent=2) + '\n')
print(log.getvalue())
print(json.dumps(review, indent=2))
