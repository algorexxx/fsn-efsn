#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-release-followup-2026-10-04"
work=/home/rehearsal/results/restart-release-followup-2026-10-04
test ! -e "$work/vulndb.zip"
test ! -e "$work/vulndb"
date -u +%FT%TZ > "$evidence/database-download-started.txt"
curl --fail --location --proto '=https' --proto-redir '=https' --connect-timeout 20 --max-time 180 --max-filesize 134217728 'https://vuln.go.dev/vulndb.zip' -o "$work/vulndb.zip" 2> "$evidence/database-download.txt"
python3 - "$evidence" "$work" <<'PY'
from datetime import datetime, timezone
import hashlib, json, shutil, sys, zipfile
from pathlib import Path, PurePosixPath
evidence, work = map(Path, sys.argv[1:])
assert shutil.disk_usage(work).free > 30 * 1024**3
assert shutil.disk_usage('/mnt/d').free > 60 * 1024**3
with zipfile.ZipFile(work / 'vulndb.zip') as archive:
    files = archive.infolist()
    assert sum(item.file_size for item in files) < 512 * 1024**2
    names = [item.filename for item in files]
    assert len(names) == len(set(names))
    assert 'index/db.json' in names and 'index/modules.json' in names
    for item in files:
        path = PurePosixPath(item.filename)
        assert not path.is_absolute() and '..' not in path.parts and '\\' not in item.filename
        assert not (item.external_attr >> 16) & 0o170000 == 0o120000
        assert path.parts[0] in ['index', 'ID']
    archive.extractall(work / 'vulndb')
snapshot = {
    'url': 'https://vuln.go.dev/vulndb.zip',
    'download_scope': 'complete public database, independent of repository or binary metadata',
    'captured_at': datetime.now(timezone.utc).isoformat(),
    'archive_sha256': hashlib.sha256((work / 'vulndb.zip').read_bytes()).hexdigest(),
    'archive_bytes': (work / 'vulndb.zip').stat().st_size,
    'files': len(files),
    'database_metadata': json.loads((work / 'vulndb/index/db.json').read_text(encoding='utf-8')),
}
(evidence / 'database-snapshot.json').write_text(json.dumps(snapshot, indent=2) + '\n', encoding='utf-8')
print(json.dumps(snapshot, indent=2))
PY
