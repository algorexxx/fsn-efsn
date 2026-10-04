#!/bin/bash
set -euo pipefail
evidence=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-release-extraction-2026-10-04
results="$evidence/attempt-3"
source=/tmp/fsn-release-extraction-2026-10-04-exact/source
[[ -d "$source" && -f "$results/test-tree.txt" && ! -e "$results/params-compatibility.txt" ]]
cp "$evidence/check-params.sh" "$results/check-params.sh"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
export GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR=/tmp TMPDIR=/tmp
cd "$source"
set +e
runuser -u rehearsal -- go test -race -p=2 -mod=readonly ./params -run '^TestCheckCompatible$' -v -count=1 -timeout=1m > "$results/params-compatibility.txt" 2>&1
code=$?
set -e
printf '%s\n' "$code" > "$results/params-compatibility-exit.txt"
[[ "$code" == 0 ]]
grep -F -- '--- PASS: TestCheckCompatible' "$results/params-compatibility.txt"
