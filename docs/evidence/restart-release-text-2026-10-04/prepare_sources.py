import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import urllib.request


evidence = Path(__file__).resolve().parent
work = Path('/home/rehearsal/results/restart-release-text-2026-10-04')
previous = evidence.parent / 'restart-release-jwt-2026-10-04'
base = Path('/home/rehearsal/results/restart-release-jwt-2026-10-04')
toolchain = Path('/home/rehearsal/results/restart-release-selection-2026-10-04/toolchain/go/bin/go')
assert not (work / 'node').exists()
assert shutil.disk_usage(work).free > 30 * 1024**3
assert shutil.disk_usage('/mnt/d').free > 60 * 1024**3
for name in ('node', 'recovery'):
    source = base / name
    actual = {p.relative_to(source).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in source.rglob('*') if p.is_file()}
    assert actual == json.loads((previous / (name + '-inventory.json')).read_text(encoding='utf-8'))
    shutil.copytree(source, work / name)

inventories = {}
for version in ('v0.12.0', 'v0.39.0'):
    source = Path('/home/rehearsal/go/pkg/mod/golang.org/x/text@' + version)
    inventories[version] = {p.relative_to(source).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in source.rglob('*') if p.is_file()}
    (evidence / (version + '-go.mod')).write_bytes((source / 'go.mod').read_bytes())
(evidence / 'upstream-inventories.json').write_text(json.dumps(inventories, indent=2, sort_keys=True) + '\n', encoding='utf-8')
changed = sorted(p for p in inventories['v0.12.0'].keys() | inventories['v0.39.0'].keys()
                 if inventories['v0.12.0'].get(p) != inventories['v0.39.0'].get(p))
(evidence / 'upstream-changed-paths.json').write_text(json.dumps(changed, indent=2) + '\n', encoding='utf-8')
url = 'https://go-review.googlesource.com/changes/794100/detail?o=CURRENT_REVISION&o=CURRENT_FILES&o=CURRENT_COMMIT'
with urllib.request.urlopen(url, timeout=30) as response:
    raw = response.read(2000000)
(evidence / 'upstream-change-response.txt').write_bytes(raw)
change = json.loads(raw.decode('utf-8').removeprefix(")]}'\n"))
revision = change['current_revision']
print(json.dumps({'change_status': change['status'], 'revision': revision,
                  'files': list(change['revisions'][revision]['files']),
                  'changed_module_paths': len(changed)}, indent=2))
subprocess.run([str(toolchain), 'mod', 'edit', '-go=1.25.0', '-require=golang.org/x/text@v0.39.0'], cwd=work / 'node', check=True)
