import base64
import hashlib
import json
import re
import subprocess
import tarfile
import urllib.request
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
frontend = dashboard / 'react-frontend'
scratch = root / 'tmp/dashboard-frontend-resolution'
scratch.mkdir(exist_ok=False)
(bundle / 'inputs').mkdir()
names = subprocess.check_output(['git', '-C', str(dashboard), '-c', 'core.autocrlf=false', 'ls-files']).decode().splitlines()
baseline = {'commit': subprocess.check_output(['git', '-C', str(dashboard), 'rev-parse', 'HEAD']).decode().strip(), 'source_sha256': {name: hashlib.sha256((dashboard / name).read_bytes()).hexdigest() for name in names if not name.endswith('.md')}, 'build_sha256': {path.relative_to(frontend / 'build').as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in (frontend / 'build').rglob('*') if path.is_file()}}
(bundle / 'baseline.json').write_text(json.dumps(baseline, indent=2) + '\n', encoding='utf-8', newline='\n')
for name in ['package.json', 'package-lock.json']:
    (bundle / 'inputs' / name).write_bytes((frontend / name).read_bytes())
(bundle / 'inputs/deploy.yml').write_bytes((dashboard / '.github/workflows/deploy.yml').read_bytes())


def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'fusion-dashboard-local-review'})
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.read()


registry_bytes = fetch('https://registry.npmjs.org/axios')
registry = json.loads(registry_bytes)
versions = sorted([name for name in registry['versions'] if re.fullmatch(r'0\.\d+\.\d+', name)], key=lambda name: tuple(map(int, name.split('.'))))
assert versions[-1] == '0.34.0', versions[-1]
selected = registry['versions'][versions[-1]]
(bundle / 'axios-selected.json').write_text(json.dumps(selected, indent=2) + '\n', encoding='utf-8', newline='\n')
archive = fetch(selected['dist']['tarball'])
algorithm, expected = selected['dist']['integrity'].split('-', 1)
assert algorithm == 'sha512' and base64.b64encode(hashlib.sha512(archive).digest()).decode() == expected
archive_path = root / 'tmp/axios-0.34.0.tgz'
archive_path.write_bytes(archive)
files = {}
with tarfile.open(archive_path, 'r:gz') as source:
    for member in source.getmembers():
        if member.isfile():
            name = member.name.removeprefix('package/')
            data = source.extractfile(member).read()
            files[name] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
metadata = {'name': 'axios', 'version': selected['version'], 'published': registry['time'][selected['version']], 'latest_0x': versions[-1], 'latest': registry['dist-tags']['latest'], 'registry_sha256': hashlib.sha256(registry_bytes).hexdigest(), 'archive_sha256': hashlib.sha256(archive).hexdigest(), 'archive_bytes': len(archive), 'integrity': selected['dist']['integrity'], 'files': files}
(bundle / 'package-inspection.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8', newline='\n')
manifest = json.loads((frontend / 'package.json').read_text(encoding='utf-8'))
used = ['@material-ui/core', 'axios', 'prop-types', 'react', 'react-bootstrap', 'react-country-flag', 'react-datamaps', 'react-dom', 'react-number-format', 'react-scripts', 'react-timeago']
removed = sorted(set(manifest['dependencies']) - set(used))
source = subprocess.check_output(['git', '-C', str(dashboard), 'grep', '-n', '-E', '^(import |.*require\\()', '--', 'react-frontend/src', ':!react-frontend/src/fonts/*', ':!react-frontend/src/img/*']).decode()
(bundle / 'frontend-imports.txt').write_text(source, encoding='utf-8', newline='\n')
for name in removed:
    assert not re.search(r"['\"]" + re.escape(name) + r"(?:/|['\"])", source), name
compiled = set()
for path in (frontend / 'build').rglob('*.map'):
    for source_name in json.loads(path.read_text(encoding='utf-8')).get('sources', []):
        match = re.search(r'node_modules/((?:@[^/]+/)?[^/]+)', source_name)
        if match:
            compiled.add(match.group(1))
assert not set(removed) & compiled, sorted(set(removed) & compiled)
manifest['dependencies'] = {name: value for name, value in manifest['dependencies'].items() if name in used}
manifest['dependencies']['axios'] = '0.34.0'
manifest['engines'] = {'node': '>=24.0.0'}
(scratch / 'package.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8', newline='\n')
(scratch / 'package-lock.json').write_bytes((frontend / 'package-lock.json').read_bytes())
(bundle / 'unused-review.json').write_text(json.dumps({'removed_direct_dependencies': removed, 'baseline_compiled_packages': sorted(compiled), 'no_removed_direct_imports_or_compiled_modules': True}, indent=2) + '\n', encoding='utf-8', newline='\n')
actions = []
for repository in ['actions/checkout', 'actions/setup-node']:
    release = json.loads(fetch('https://api.github.com/repos/' + repository + '/releases/latest'))
    commit = json.loads(fetch('https://api.github.com/repos/' + repository + '/commits/' + release['tag_name']))
    actions.append({'repository': repository, 'tag': release['tag_name'], 'release_url': release['html_url'], 'published': release['published_at'], 'sha': commit['sha']})
(bundle / 'actions.json').write_text(json.dumps(actions, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'axios': selected['version'], 'removed': removed, 'actions': actions}, indent=2))
