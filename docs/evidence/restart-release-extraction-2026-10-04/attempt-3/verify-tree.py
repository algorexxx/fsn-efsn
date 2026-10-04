import hashlib
import json
from pathlib import Path
import sys
import tarfile

evidence, inputs, source = (Path(value) for value in sys.argv[1:4])
stage = int(sys.argv[4])
assert stage in [1, 2, 3, 4]
manifest = json.loads((evidence / 'selection.json').read_text(encoding='utf-8'))
archives = json.loads((evidence / 'input-archives.json').read_text(encoding='utf-8'))
expected = {}
with tarfile.open(inputs / 'baseline.tar') as archive:
    for member in archive.getmembers():
        if member.isfile() and member.name.endswith('.go'):
            expected[member.name] = hashlib.sha256(archive.extractfile(member).read()).hexdigest()
for name in ['baseline.tar', 'tests.tar']:
    assert hashlib.sha256((inputs / name).read_bytes()).hexdigest() == archives[name], name
for patch in manifest['patches'][:min(stage, 3)]:
    assert hashlib.sha256((evidence / patch['patch']).read_bytes()).hexdigest() == patch['sha256']
    for entry in patch['files']:
        expected[entry['path']] = entry['after_sha256']
if stage == 4:
    expected.update({p: digest for p, digest in archives['test_overlay'].items() if p.endswith('.go')})
actual = {p.relative_to(source).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob('*.go')}
assert expected == actual, {'missing': sorted(expected.keys() - actual.keys()), 'extra': sorted(actual.keys() - expected.keys()), 'different': sorted(p for p in expected.keys() & actual.keys() if expected[p] != actual[p])}
for excluded in manifest['excluded_runtime']:
    assert not (source / excluded).exists(), excluded
if stage < 3:
    assert not (source / 'internal/recovery').exists()
    assert not (source / 'cmd/fsn-recovery').exists()
if stage == 4:
    for path, digest in archives['test_overlay'].items():
        assert hashlib.sha256((source / path).read_bytes()).hexdigest() == digest, path
print(f'PASS stage={stage}: {len(actual)} exact Go files; observer absent; archive/patch/test inputs match their recorded hashes')
