import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
previous = evidence.parent / 'restart-release-selection-2026-10-04'
selected = Path('/home/rehearsal/results/restart-release-selection-2026-10-04')
work = Path('/home/rehearsal/results/restart-release-followup-2026-10-04')
result = {'inventories': {}, 'sha256': {}}
for source, manifest in [
    (selected / 'source', previous / 'selected-node-inventory.json'),
    (selected / 'repeat', previous / 'selected-recovery-inventory.json'),
    (work / 'network-source', evidence / 'network-source-inventory.json'),
]:
    expected = json.loads(manifest.read_text(encoding='utf-8'))
    if source.name == 'repeat':
        expected['p2p/rlpx_test.go'] = hashlib.sha256((workspace / 'p2p/rlpx_test.go').read_bytes().replace(b'\r\n', b'\n')).hexdigest()
    actual = {path.relative_to(source).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in source.rglob('*') if path.is_file()}
    assert actual == expected, str(source)
    result['inventories'][str(source)] = len(actual)
for binary, manifest in [
    (selected / 'bin/efsn', previous / 'selected-binary.sha256'),
    (selected / 'bin/fsn-recovery', previous / 'recovery-binary.sha256'),
    (work / 'bin/govulncheck', evidence / 'scanner-binary.sha256'),
]:
    actual = hashlib.sha256(binary.read_bytes()).hexdigest()
    assert actual == manifest.read_text(encoding='utf-8').split()[0]
    result['sha256'][str(binary)] = actual
snapshot = json.loads((evidence / 'database-snapshot.json').read_text(encoding='utf-8'))
assert hashlib.sha256((work / 'vulndb.zip').read_bytes()).hexdigest() == snapshot['archive_sha256']
with zipfile.ZipFile(work / 'vulndb.zip') as archive:
    for entry in archive.infolist():
        if not entry.is_dir():
            assert (work / 'vulndb' / entry.filename).read_bytes() == archive.read(entry)
for path in (work / 'vulndb').rglob('*'):
    if path.is_file():
        assert not path.is_symlink()
assert len([path for path in (work / 'vulndb').rglob('*') if path.is_file()]) == snapshot['files']
for path in ('p2p/discover/node_test.go', 'p2p/discover/udp_test.go'):
    data = (workspace / path).read_bytes().replace(b'\r\n', b'\n')
    assert subprocess.check_output([str(selected / 'toolchain/go/bin/gofmt')], input=data) == data
for runner in evidence.glob('*.sh'):
    subprocess.run(['bash', '-n', str(runner)], check=True)
subprocess.run(['python3', str(evidence / 'review-results.py'), '--check'], check=True)
result.update({'production_sources_unchanged': True, 'exact_selected_binaries': True,
               'project_modules_unchanged': True, 'launch_approved': False})
(evidence / 'verified-inputs.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
