#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-release-selection-2026-10-04"
extraction="$workspace/docs/evidence/restart-release-extraction-2026-10-04"
inputs="$workspace/tmp/release-extraction-2026-10-04-exact"
work=/home/rehearsal/results/restart-release-selection-2026-10-04
test "$(cat "$evidence/repeat-build-exit.txt")" = 0
test ! -e "$evidence/recovery-apply.txt"
export PATH="$work/toolchain/go/bin:/usr/bin:/bin"
export GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off GOFLAGS=-mod=readonly CGO_ENABLED=1 GOMAXPROCS=2
export GOCACHE="$work/repeat-cache" GOTMPDIR="$work/tmp" TMPDIR="$work/tmp"
cd "$work/repeat"
cmp "$work/bin/efsn" "$work/bin/efsn-repeat"
set +e
go list -m all > "$evidence/module-graph-recheck.txt" 2> "$evidence/module-graph-recheck.stderr.txt"
code=$?
set -e
printf '%s\n' "$code" > "$evidence/module-graph-recheck-exit.txt"
test "$code" = 1
grep -q 'module lookup disabled by GOPROXY=off' "$evidence/module-graph-recheck.stderr.txt"
git apply --check "$extraction/03-recovery-tool.patch" > "$evidence/recovery-apply.txt" 2>&1
git apply "$extraction/03-recovery-tool.patch" >> "$evidence/recovery-apply.txt" 2>&1
python3 - "$evidence" "$extraction" "$work/repeat" <<'PY'
import hashlib, json, sys
from pathlib import Path
evidence, extraction, source = map(Path, sys.argv[1:])
expected = json.loads((evidence / 'selected-node-inventory.json').read_text(encoding='utf-8'))
selection = json.loads((extraction / 'selection.json').read_text(encoding='utf-8'))
patch = next(p for p in selection['patches'] if p['patch'] == '03-recovery-tool.patch')
assert hashlib.sha256((extraction / patch['patch']).read_bytes()).hexdigest() == patch['sha256']
for item in patch['files']:
    assert expected.get(item['path']) == item['before_sha256']
    expected[item['path']] = item['after_sha256']
actual = {p.relative_to(source).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob('*') if p.is_file()}
assert expected == actual
(evidence / 'selected-recovery-inventory.json').write_text(json.dumps(expected, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print('PASS separate recovery selection without O1 or observer additions')
PY
set +e
timeout --signal=TERM --kill-after=20s 5m go build -p=2 -trimpath -buildvcs=false -o "$work/bin/fsn-recovery" ./cmd/fsn-recovery > "$evidence/recovery-build.txt" 2>&1
code=$?
set -e
printf '%s\n' "$code" > "$evidence/recovery-build-exit.txt"
test "$code" = 0
sha256sum "$work/bin/fsn-recovery" > "$evidence/recovery-binary.sha256"
go version -m "$work/bin/fsn-recovery" > "$evidence/recovery-build-info.txt"
for item in parse forward handshake; do
    case "$item" in
        parse) package=./p2p/discover; selection='^TestParseNode$' ;;
        forward) package=./p2p/discover; selection='^TestForwardCompatibility$' ;;
        handshake) package=./p2p; selection='^TestProtocolHandshake$' ;;
    esac
    set +e
    timeout --signal=TERM --kill-after=20s 5m go test -p=2 -count=1 -run "$selection" -timeout=90s -v "$package" > "$evidence/finding-$item.txt" 2>&1
    code=$?
    set -e
    printf '%s\n' "$code" > "$evidence/finding-$item-exit.txt"
done
date -u +%FT%TZ > "$evidence/repeat-finished.txt"
df -B1 --output=source,size,used,avail / /mnt/d > "$evidence/repeat-capacity-after.txt"
du -sB1 "$work" > "$evidence/repeat-work-size.txt"
printf '0\n' > "$evidence/continuation-exit.txt"
