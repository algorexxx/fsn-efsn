import base64
import hashlib
import json
import subprocess
import tarfile
import urllib.request
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
scratch = root / 'tmp/dashboard-geoip-reader'
scratch.mkdir(exist_ok=True)


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def fetch(url, path, limit=5000000):
    request = urllib.request.Request(url, headers={'User-Agent': 'fusion-dashboard-compatibility-review'})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError('Download exceeds review budget: ' + url)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return data


def capture_baseline():
    dashboard = root / 'tmp/fsn-stats-auth'
    paths = subprocess.check_output(['git', '-C', str(dashboard), 'ls-files', '-z']).decode().split('\0')
    hashes = {name: hashlib.sha256((dashboard / name).read_bytes()).hexdigest() for name in paths if name}
    value = {'dashboard_commit': subprocess.check_output(['git', '-C', str(dashboard), 'rev-parse', 'HEAD']).decode().strip(), 'dashboard_sha256': hashes}
    value['efsn_sha256'] = json.loads((bundle.parent / 'restart-dashboard-geoip-validation-2026-10-04/source-baseline.json').read_text(encoding='utf-8'))['efsn_sha256']
    save_json(bundle / 'source-baseline.json', value)


def fetch_package(name, version, install):
    label = name.replace('/', '_').replace('@', '')
    url = 'https://registry.npmjs.org/' + name.replace('/', '%2f') + '/' + version
    metadata = json.loads(fetch(url, bundle / (label + '-metadata.json')))
    if not install:
        return metadata
    archive = scratch / (label + '-' + metadata['version'] + '.tgz')
    data = fetch(metadata['dist']['tarball'], archive)
    actual = 'sha512-' + base64.b64encode(hashlib.sha512(data).digest()).decode()
    if actual != metadata['dist']['integrity']:
        raise ValueError('Package integrity mismatch: ' + name)
    destination = scratch / 'candidate/node_modules' / name
    destination.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive, 'r:gz') as package:
        total = 0
        for member in package.getmembers():
            relative = Path(member.name).parts
            if not relative or relative[0] != 'package' or '..' in relative:
                raise ValueError('Unexpected archive path')
            target = destination.joinpath(*relative[1:]).resolve()
            if not target.is_relative_to(destination.resolve()):
                raise ValueError('Archive path escaped destination')
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile():
                raise ValueError('Unexpected archive member')
            total += member.size
            if total > 10000000:
                raise ValueError('Expanded package exceeds review budget')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(package.extractfile(member).read())
    return metadata


capture_baseline()
versions = {'maxmind': '5.0.7', 'mmdb-lib': '3.0.3', '@maxmind/geoip2-node': '7.1.0'}
packages = {name: fetch_package(name, version, name == 'mmdb-lib') for name, version in versions.items()}
commit = json.loads(fetch('https://api.github.com/repos/maxmind/MaxMind-DB/commits/276926d23b4109ca5452709bfb5931c338afb34c', bundle / 'fixture-commit.json'))['sha']
tree = json.loads(fetch('https://api.github.com/repos/maxmind/MaxMind-DB/git/trees/' + commit + '?recursive=1', bundle / 'fixture-tree.json'))
save_json(bundle / 'acquisition.json', {'fixture_commit': commit, 'packages': {name: {'version': value['version'], 'dependencies': value.get('dependencies', {}), 'integrity': value['dist']['integrity']} for name, value in packages.items()}})
print(json.dumps({'fixture_commit': commit, 'packages': {name: {'version': value['version'], 'dependencies': value.get('dependencies', {})} for name, value in packages.items()}, 'fixtures': [entry['path'] for entry in tree['tree'] if entry['path'].startswith(('source-data/', 'test-data/')) and ('City' in entry['path'] or 'ipv6' in entry['path'])]}, indent=2))
