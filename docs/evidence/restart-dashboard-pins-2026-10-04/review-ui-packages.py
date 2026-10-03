import concurrent.futures
import hashlib
import json
import urllib.request
from pathlib import Path

bundle = Path(__file__).resolve().parent
frontend = bundle.parents[2] / 'tmp/fsn-stats-auth/react-frontend'
manifest = json.loads((frontend / 'package.json').read_text(encoding='utf-8'))
lock = json.loads((frontend / 'package-lock.json').read_text(encoding='utf-8'))
names = list(manifest['dependencies']) + ['@mui/material', 'datamaps', 'd3', 'topojson']


def inspect(name):
    with urllib.request.urlopen('https://registry.npmjs.org/' + name, timeout=45) as response:
        raw = response.read()
    registry = json.loads(raw)
    latest = registry['dist-tags']['latest']
    installed = lock['packages'].get('node_modules/' + name, {}).get('version')
    selected = registry['versions'].get(installed, {})
    current = registry['versions'][latest]
    return name, {
        'installed': installed, 'installed_published': registry['time'].get(installed),
        'installed_peers': selected.get('peerDependencies', {}), 'deprecated': selected.get('deprecated'),
        'latest_tag': latest, 'latest_published': registry['time'].get(latest), 'latest_peers': current.get('peerDependencies', {}),
        'repository': current.get('repository'), 'homepage': current.get('homepage'), 'registry_sha256': hashlib.sha256(raw).hexdigest(),
    }


with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    records = dict(executor.map(inspect, names))
(bundle / 'ui-package-review.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8', newline='\n')
for name, value in records.items():
    print(name, value['installed'], '-> latest tag', value['latest_tag'], value['latest_peers'])
