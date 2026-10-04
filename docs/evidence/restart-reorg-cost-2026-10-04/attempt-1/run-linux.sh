#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-reorg-cost-2026-10-04"
attempt="${1:?explicit attempt name required}"
[[ "$attempt" =~ ^attempt-[1-9][0-9]*$ ]]
results="$evidence/$attempt"
[[ ! -e "$results" ]]
mkdir "$results"
cp "$evidence/run-linux.sh" "$results/run-linux.sh"
cp "$evidence/README.md" "$results/declared-scope.md"
for name in reorg_cost_test.go reorg_cost_fixture_test.go; do
    cp "$workspace/tests/restart/$name" "$results/$name.txt"
done
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
export GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR=/tmp TMPDIR=/tmp
export FUSION_RESTART_REORG_COST=1
cd "$workspace"
df -B1 /tmp /mnt/c /mnt/d > "$results/capacity-before.txt"
ip -brief link > "$results/network.txt"
go version > "$results/toolchain.txt"
git -c safe.directory="$workspace" rev-parse HEAD > "$results/baseline.txt"
git -c safe.directory="$workspace" ls-files -z '*.go' go.mod go.sum | sort -z | xargs -0 sha256sum > "$results/tracked-sources.sha256"
sha256sum tests/restart/reorg_cost*.go > "$results/added-tests.sha256"
sha256sum docs/evidence/restart-2026-09-23/responses.json > "$results/fixture-source.sha256"
set +e
runuser -u rehearsal -- env PATH="$PATH" go test -p=2 -mod=readonly -c -o /tmp/fsn-reorg-cost-tests ./tests/restart > "$results/build.txt" 2>&1
code=$?
set -e
printf '%s\n' "$code" > "$results/build-exit.txt"
[[ "$code" == 0 ]]
sha256sum /tmp/fsn-reorg-cost-tests > "$results/binary.sha256"
cd tests/restart
set +e
runuser -u rehearsal -- /usr/bin/time -v /tmp/fsn-reorg-cost-tests '-test.run=^TestRestartReorganizationCost$' -test.v -test.timeout=20m > "$results/reorg.txt" 2> "$results/resources.txt"
code=$?
set -e
printf '%s\n' "$code" > "$results/test-exit.txt"
df -B1 /tmp /mnt/c /mnt/d > "$results/capacity-after.txt"
tail -n 14 "$results/reorg.txt"
[[ "$code" == 0 ]]
