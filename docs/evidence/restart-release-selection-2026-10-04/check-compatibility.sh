#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-release-selection-2026-10-04"
extraction="$workspace/docs/evidence/restart-release-extraction-2026-10-04"
inputs="$workspace/tmp/release-extraction-2026-10-04-exact"
work=/home/rehearsal/results/restart-release-selection-2026-10-04
test "$(cat "$evidence/build-node-exit.txt")" = 1
test ! -e "$evidence/compatibility-started.txt"
export PATH="$work/toolchain/go/bin:/usr/bin:/bin"
export GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off GOFLAGS=-mod=readonly CGO_ENABLED=1 GOMAXPROCS=2
export GOCACHE="$work/cache" GOTMPDIR="$work/tmp" TMPDIR="$work/tmp"
cd "$work/source"
python3 "$extraction/verify-tree.py" "$extraction" "$inputs" "$work/source" 1 > "$evidence/compatibility-before-tree.txt"
python3 - "$evidence" "$work/source" before <<'PY'
import hashlib, json, sys
from pathlib import Path
evidence, source = map(Path, sys.argv[1:3])
selection = json.loads((evidence / 'build-compatibility.json').read_text(encoding='utf-8'))
assert hashlib.sha256((evidence / selection['patch']).read_bytes()).hexdigest() == selection['sha256']
for item in selection['files']:
    assert hashlib.sha256((source / item['path']).read_bytes()).hexdigest() == item['before_sha256'], item['path']
inventory = {p.relative_to(source).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob('*') if p.is_file()}
for item in selection['files']:
    inventory[item['path']] = item['after_sha256']
(evidence / 'selected-node-inventory.json').write_text(json.dumps(inventory, indent=2, sort_keys=True) + '\n', encoding='utf-8')
PY
git apply --check "$evidence/05-build-compatibility.patch" > "$evidence/compatibility-apply.txt" 2>&1
git apply "$evidence/05-build-compatibility.patch" >> "$evidence/compatibility-apply.txt" 2>&1
date -u +%FT%TZ > "$evidence/compatibility-started.txt"
set +e
timeout --signal=TERM --kill-after=20s 12m go build -p=2 -trimpath -buildvcs=false -o "$work/bin/efsn" ./cmd/efsn > "$evidence/compatibility-build.txt" 2>&1
code=$?
set -e
printf '%s\n' "$code" > "$evidence/compatibility-build-exit.txt"
python3 - "$evidence" "$work/source" <<'PY'
import hashlib, json, sys
from pathlib import Path
evidence, source = map(Path, sys.argv[1:])
expected = json.loads((evidence / 'selected-node-inventory.json').read_text(encoding='utf-8'))
actual = {p.relative_to(source).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob('*') if p.is_file()}
assert expected == actual
print('PASS complete selected node inventory; only four declared B1 files changed')
PY
if [ "$code" != 0 ]; then tail -n 20 "$evidence/compatibility-build.txt"; exit "$code"; fi
timeout 20s "$work/bin/efsn" version > "$evidence/cli-version.txt" 2>&1
timeout 20s "$work/bin/efsn" --help > "$evidence/cli-help.txt" 2>&1
go list -deps ./cmd/efsn > "$evidence/node-dependencies.txt"
if grep -E '^github.com/fjl/memsize|/internal/recovery$|/internal/observer$' "$evidence/node-dependencies.txt"; then exit 1; fi
sha256sum "$work/bin/efsn" > "$evidence/selected-binary.sha256"
go version -m "$work/bin/efsn" > "$evidence/selected-build-info.txt"
date -u +%FT%TZ > "$evidence/compatibility-finished.txt"
printf '0\n' > "$evidence/compatibility-exit.txt"
cat "$evidence/cli-version.txt"
