import datetime
import hashlib
import json
import urllib.request
from pathlib import Path

bundle = Path(__file__).resolve().parent
output = bundle / 'metadata'
output.mkdir(exist_ok=True)
urls = {
    'node-index.json': 'https://nodejs.org/dist/index.json',
    'node-schedule.json': 'https://raw.githubusercontent.com/nodejs/Release/main/schedule.json',
}
for name in ['ws', 'primus', 'lodash', 'express', 'geoip-lite', 'axios', 'react-scripts']:
    urls[name + '-latest.json'] = 'https://registry.npmjs.org/' + name + '/latest'
record = []
for name, url in urls.items():
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Fusion-dashboard-dependency-review'}), timeout=30) as response:
        raw = response.read(4 * 1024 * 1024)
        assert not response.read(1)
        (output / name).write_bytes(raw)
        record.append({'file': name, 'url': url, 'final_url': response.url, 'retrieved_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'sha256': hashlib.sha256(raw).hexdigest()})
    value = json.loads(raw)
    if name == 'node-index.json':
        print({major: next(row['version'] for row in value if row['version'].startswith('v' + major + '.')) for major in ['22', '24']}, flush=True)
    elif 'version' in value:
        print({'name': value['name'], 'version': value['version'], 'engines': value.get('engines')}, flush=True)
(output / 'sources.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
