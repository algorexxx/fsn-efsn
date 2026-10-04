import base64
import hashlib
import json
from pathlib import Path
import urllib.request


evidence = Path(__file__).resolve().parent
change = json.loads((evidence / 'upstream-change-response.txt').read_text(encoding='utf-8').removeprefix(")]}'\n"))
revision = change['current_revision']
results = {}
for name in change['revisions'][revision]['files']:
    url = 'https://go-review.googlesource.com/changes/794100/revisions/' + revision + '/files/' + urllib.parse.quote(name, safe='') + '/content'
    with urllib.request.urlopen(url, timeout=30) as response:
        content = base64.b64decode(response.read(1000000))
    target = evidence / 'upstream-fix' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    release = Path('/home/rehearsal/go/pkg/mod/golang.org/x/text@v0.39.0') / name
    assert release.read_bytes() == content, name
    results[name] = hashlib.sha256(content).hexdigest()
result = {'merged_revision': revision, 'all_four_fixed_files_identical_in_release': True, 'sha256': results}
(evidence / 'upstream-fix-verification.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
