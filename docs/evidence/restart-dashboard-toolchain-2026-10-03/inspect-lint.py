import json
import io
import tarfile
import urllib.request
from pathlib import Path

bundle = Path(__file__).resolve().parent
with urllib.request.urlopen('https://registry.npmjs.org/oxlint', timeout=45) as response:
    data = json.load(response)
selected = data['versions'][data['dist-tags']['latest']]
(bundle / 'oxlint-registry.json').write_text(json.dumps(selected, indent=2) + '\n', encoding='utf-8')
with urllib.request.urlopen(selected['dist']['tarball'], timeout=45) as response:
    archive = response.read()
with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as package:
    (bundle / 'oxlint-schema.json').write_bytes(package.extractfile('package/configuration_schema.json').read())
print(selected['version'])
