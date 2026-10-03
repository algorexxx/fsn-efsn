import json
import re
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
frontend = root / 'tmp/fsn-stats-auth/react-frontend'
build = frontend / 'build'
modules = {}
for path in build.rglob('*.map'):
    for source in json.loads(path.read_text(encoding='utf-8')).get('sources', []):
        match = re.search(r'node_modules/((?:@[^/]+/)?[^/]+)', source)
        if match:
            modules.setdefault(match.group(1), []).append(source)
audit = json.loads((bundle / 'installed-audit.stdout.txt').read_text(encoding='utf-8'))
assert not set(modules) & set(audit['vulnerabilities'])
assert any('/axios/lib/adapters/xhr.js' in name for name in modules['axios'])
assert not any('/axios/lib/adapters/http.js' in name for name in modules['axios'])
before = json.loads((bundle / 'baseline.json').read_text(encoding='utf-8'))['build_sha256']
after = json.loads((bundle / 'frontend-4/result.json').read_text(encoding='utf-8'))['build_sha256']
unchanged = [name for name, value in before.items() if after.get(name) == value]
removed = sorted(set(before) - set(after))
added = sorted(set(after) - set(before))
changed = sorted(name for name in set(before) & set(after) if before[name] != after[name])
record = {'compiled_package_sources': modules, 'audited_names_in_compiled_sources': [], 'axios_xhr_present': True, 'axios_http_absent': True, 'old_build_files': len(before), 'new_build_files': len(after), 'unchanged_build_files': len(unchanged), 'removed_build_paths': removed, 'added_build_paths': added, 'changed_build_paths': changed}
(bundle / 'compiled-review.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({key: value for key, value in record.items() if key != 'compiled_package_sources'}, indent=2))
