#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-operator-kit-2026-10-04"
baseline=/home/rehearsal/results/restart-automatic-sync-2026-10-04-attempt-2/source
work=/home/rehearsal/results/restart-operator-kit-2026-10-04-attempt-4
results="$evidence/attempt-4"
command=/home/rehearsal/results/restart-release-extraction-2026-10-04/bin/efsn-node
[[ ! -e "$work" && ! -e "$results" ]]
mkdir -p "$work/bin" "$results/inputs"
cp "$evidence/run-linux.sh" "$results/run-linux.sh"
cp "$evidence/README.md" "$results/declared-scope.md"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
export GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR=/tmp TMPDIR=/tmp
df -B1 "$work" /mnt/c /mnt/d > "$results/capacity-before.txt"
python3 - "$workspace" "$baseline" "$work" "$results" "$command" <<'PY'
import hashlib, json, shutil, sys
from pathlib import Path
workspace, baseline, work, results, command = map(Path, sys.argv[1:])
assert shutil.disk_usage(work).free > 5 * 1024**3
expected = json.loads((workspace / 'docs/evidence/restart-automatic-sync-2026-10-04/attempt-2/source-sha256.json').read_text(encoding='utf-8'))
actual = {p.relative_to(baseline).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in baseline.rglob('*') if p.is_file()}
assert actual == expected
pins = (workspace / 'docs/evidence/restart-release-extraction-2026-10-04/attempt-4/binaries.sha256').read_text(encoding='utf-8').splitlines()
pin = next(line.split()[0] for line in pins if line.endswith('/bin/efsn-node'))
assert hashlib.sha256(command.read_bytes()).hexdigest() == pin
shutil.copytree(baseline, work / 'source')
for name in ['node_rehearsal_linux_test.go', 'operator_kit_linux_test.go', 'snapshot_package.py']:
    data = (workspace / 'tests/restart' / name).read_bytes().replace(b'\r\n', b'\n')
    (results / 'inputs' / name).write_bytes(data)
    (work / 'source/tests/restart' / name).write_bytes(data)
inventory = {p.relative_to(work / 'source').as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((work / 'source').rglob('*')) if p.is_file()}
(results / 'source-sha256.json').write_text(json.dumps(inventory, indent=2) + '\n', encoding='utf-8')
(results / 'baseline-check.txt').write_text(f'PASS: {len(actual)} source files and extracted console executable verified\n', encoding='utf-8')
PY
ip link set lo up
ip -brief link > "$results/network.txt"
go version > "$results/toolchain.txt"
python3 --version >> "$results/toolchain.txt"
chown -R rehearsal:rehearsal "$work"
cd "$work/source"
[[ -z "$(gofmt -l tests/restart/operator_kit_linux_test.go tests/restart/node_rehearsal_linux_test.go)" ]]
set +e
runuser -u rehearsal -- timeout --kill-after=15s 5m go test -race -p=2 -mod=readonly -c -o "$work/bin/restart-tests" ./tests/restart > "$results/build.txt" 2>&1
code=$?
set -e
printf '%s\n' "$code" > "$results/build-exit.txt"
[[ "$code" == 0 ]]
sha256sum "$work/bin/restart-tests" "$command" > "$results/binaries.sha256"
cd tests/restart
set +e
runuser -u rehearsal -- env FUSION_RESTART_NODE_REHEARSAL=1 FUSION_RESTART_EFSN_COMMAND="$command" timeout --kill-after=15s 8m /usr/bin/time -v "$work/bin/restart-tests" '-test.run=^TestRestartNodeRehearsal$/^operator_kit$' -test.v -test.timeout=8m > "$results/test.txt" 2>&1
code=$?
set -e
printf '%s\n' "$code" > "$results/test-exit.txt"
df -B1 "$work" /mnt/c /mnt/d > "$results/capacity-after.txt"
sha256sum -c "$results/binaries.sha256" > "$results/binaries-after.txt"
printf '%s\n' "$code" > "$results/exit-code.txt"
tail -n 28 "$results/test.txt"
exit "$code"
