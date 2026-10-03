import gzip
import hashlib
import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
linux = '/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/'
prefix = ['wsl', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--']
commands = {
    'resolved-packages': [linux + 'tmp/dashboard-runtime-review/v24.21.0/node', linux + bundle.relative_to(root).as_posix() + '/resolve.cjs'],
    'os-release': ['cat', '/etc/os-release'],
    'nginx-linked-libraries': ['ldd', linux + 'tmp/dashboard-proxy-runtime/extracted/usr/sbin/nginx'],
    'host-library-packages': ['dpkg-query', '-W', 'libc6', 'libssl3t64', 'libpcre2-8-0', 'zlib1g'],
}
results = []
for name, command in commands.items():
    suffix = '.json' if name == 'resolved-packages' else '.txt'
    path = bundle / (name + suffix)
    with path.open('wb') as stdout, (bundle / (name + '.stderr.txt')).open('wb') as stderr:
        result = subprocess.run(prefix + command, cwd=root, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
    results.append({'name': name, 'command': prefix + command, 'exit': result.returncode, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
changelog = root / 'tmp/dashboard-proxy-runtime/extracted/usr/share/doc/nginx/changelog.Debian.gz'
with gzip.open(changelog, 'rt', encoding='utf-8') as file:
    latest = file.read().split('\nnginx (', 1)[0]
(bundle / 'nginx-latest-changelog.txt').write_text(latest + '\n', encoding='utf-8', newline='\n')
(bundle / 'platform-capture.json').write_text(json.dumps({'commands': results, 'nginx_changelog_gzip_sha256': hashlib.sha256(changelog.read_bytes()).hexdigest()}, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(results), flush=True)
raise SystemExit(any(row['exit'] != 0 for row in results))
