import hashlib
import json
import shutil
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
segment = workspace / 'tmp/partition-history-2026-09-26/history.rlp'
working = workspace / 'tmp/full-state-history-partition-2026-09-26'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def git(*args):
    return subprocess.check_output(['git', '-c', 'core.safecrlf=false', *args], cwd=workspace).decode().strip()


def retain(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert digest(source) == digest(target), target
    else:
        shutil.copyfile(source, target)


def read(name):
    return (evidence / name).read_text(encoding='utf-8')


measured = json.loads(Path(str(segment) + '.measure.json').read_text(encoding='utf-8'))
exported = json.loads(Path(str(segment) + '.export.json').read_text(encoding='utf-8'))
assert measured == exported
assert exported == {'First': 15040080, 'Last': 15130080, 'Blocks': 90001, 'Transactions': 90020, 'Bytes': 70098887, 'SHA256': '99185867e8dd894c27bf8bf304193d3247c8ef76bbc86cd4387d48342265c73d'}
assert segment.stat().st_size == exported['Bytes'] and digest(segment) == exported['SHA256']
assert int(read('measure-initial-exit.txt')) == 1 and 'historical block body commitment mismatch at 15040080' in read('measure-initial.txt')
assert '--- PASS: TestExportFullStateHistory (49.23s)' in read('measure.txt')
assert not (evidence / 'measure-exit.txt').exists()
assert int(read('export-exit.txt')) == 0 and '--- PASS: TestExportFullStateHistory (89.93s)' in read('export.txt')
assert 'ro,relatime' in read('export.txt') and 'readonly=true' in read('export.txt') and 'lo               DOWN' in read('export.txt')
assert read('body-validation-verified-race.txt').count('--- PASS:') == 7
for log in ['measure.txt', 'export.txt', 'body-validation-verified-race.txt']:
    assert read(log).endswith('PASS\n') and 'WARNING: DATA RACE' not in read(log)
assert read('build.txt') == '' and read('initial-build.txt') == ''
assert read('binary.sha256').split()[0] == digest(workspace / 'tmp/partition-history-2026-09-26/tests')
assert read('initial-binary.sha256').split()[0] == digest(workspace / 'tmp/partition-history-2026-09-26/tests-initial')
for role in ['producer', 'verifier']:
    report = working / role / 'history-installed.json'
    assert json.loads(report.read_text(encoding='utf-8')) == exported
    retain(report, evidence / (role + '-history-installed.json'))
for mode in ['measure', 'export']:
    retain(Path(str(segment) + '.' + mode + '.json'), evidence / ('history-' + mode + '.json'))
manifest = workspace / 'docs/evidence/restart-state-export-2026-09-24/artifact-SHA256SUMS'
assert digest(manifest) == 'a6c86fc58a9f7b482a02b787a337d600e32a447551e45dbe40d210b498341bbf'
entries = [line.split('  ./', 1) for line in manifest.read_text(encoding='utf-8').splitlines()]
assert len(entries) == 230
for expected, relative in entries:
    assert digest(workspace / 'tmp/preserved-head-state' / relative) == expected, relative
print('Verified 90,001 genuine blocks, both history installations, 70,098,887 identical measured/exported bytes, retained failures, final binary identity, six focused cases and all 230 unchanged source-export files')
