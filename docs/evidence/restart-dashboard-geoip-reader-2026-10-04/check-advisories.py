import datetime
import json
import urllib.request
from pathlib import Path

bundle = Path(__file__).resolve().parent
url = 'https://registry.npmjs.org/-/npm/v1/security/advisories/bulk'
payload = {'mmdb-lib': ['3.0.3']}
request = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'}, method='POST')
with urllib.request.urlopen(request, timeout=30) as response:
    result = json.loads(response.read(1000000))
value = {'checked_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'url': url, 'request': payload, 'response': result}
(bundle / 'advisories.json').write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
print(json.dumps(value, indent=2))
