#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-automatic-sync-2026-10-04"
previous="$workspace/docs/evidence/restart-release-extraction-2026-10-04"
baseline=/home/rehearsal/results/restart-release-extraction-2026-10-04/source
work=/home/rehearsal/results/restart-automatic-sync-2026-10-04
results="$evidence/attempt-1"
[[ ! -e "$work" && ! -e "$results" ]]
mkdir -p "$work/bin" "$results/inputs"
cp "$evidence/run-linux.sh" "$results/run-linux.sh"
cp "$evidence/README.md" "$results/declared-scope.md"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
export GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR=/tmp TMPDIR=/tmp
df -B1 "$work" /mnt/c /mnt/d > "$results/capacity-before.txt"
python3 "$previous/verify-tree.py" "$previous" "$workspace/tmp/release-extraction-2026-10-04-exact" "$baseline" 5 > "$results/baseline-check.txt"
python3 - "$workspace" "$baseline" "$work" "$results" <<'PY'
import hashlib, json, shutil, sys
from pathlib import Path
workspace, baseline, work, results = map(Path, sys.argv[1:])
assert shutil.disk_usage(work).free > 5 * 1024**3
shutil.copytree(baseline, work / 'source')
for name in ['node_rehearsal_linux_test.go', 'automatic_sync_linux_test.go']:
    data = (workspace / 'tests/restart' / name).read_bytes().replace(b'\r\n', b'\n')
    (results / 'inputs' / name).write_bytes(data)
    (work / 'source/tests/restart' / name).write_bytes(data)
inventory = {p.relative_to(work / 'source').as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted((work / 'source').rglob('*')) if p.is_file()}
(results / 'source-sha256.json').write_text(json.dumps(inventory, indent=2) + '\n', encoding='utf-8')
PY
ip link set lo up
ip -brief link > "$results/network.txt"
go version > "$results/toolchain.txt"
gcc --version >> "$results/toolchain.txt"
chown -R rehearsal:rehearsal "$work"
cd "$work/source"
[[ -z "$(gofmt -l tests/restart/automatic_sync_linux_test.go tests/restart/node_rehearsal_linux_test.go)" ]]
set +e
runuser -u rehearsal -- timeout --kill-after=15s 5m go test -race -p=2 -mod=readonly -c -o "$work/bin/restart-tests" ./tests/restart > "$results/build.txt" 2>&1
code=$?
set -e
printf '%s\n' "$code" > "$results/build-exit.txt"
[[ "$code" == 0 ]]
sha256sum "$work/bin/restart-tests" > "$results/binary.sha256"
go version -m "$work/bin/restart-tests" > "$results/build-info.txt"
cd tests/restart
set +e
runuser -u rehearsal -- env FUSION_RESTART_NODE_REHEARSAL=1 timeout --kill-after=15s 6m /usr/bin/time -v "$work/bin/restart-tests" '-test.run=^TestRestartNodeRehearsal$/^unknown_heavier_automatic_sync$' -test.v -test.timeout=6m > "$results/test.txt" 2>&1
code=$?
set -e
printf '%s\n' "$code" > "$results/test-exit.txt"
df -B1 "$work" /mnt/c /mnt/d > "$results/capacity-after.txt"
sha256sum -c "$results/binary.sha256" > "$results/binary-after.txt"
printf '%s\n' "$code" > "$results/exit-code.txt"
tail -n 28 "$results/test.txt"
exit "$code"
