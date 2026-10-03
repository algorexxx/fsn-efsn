#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-observer-preserved-inventory-2026-10-03"
attempt="${1:?explicit attempt name required}"
[[ "$attempt" =~ ^attempt-[1-9][0-9]*$ ]]
shift
if [[ "$#" == 0 ]]; then
    set -- 15130080 15130079 15129953 15129952 15129056 15120080 15030080 14000000 1000000
fi
[[ "$#" -le 16 ]]
for height in "$@"; do
    [[ "$height" =~ ^[1-9][0-9]{0,7}$ && "$height" -le 15130080 ]]
done
results="$evidence/$attempt"
[[ ! -e "$results" ]]
test -f /home/rehearsal/results/backup-copy-2026-09-23/verified.txt
source=/home/rehearsal/data/efsn/chaindata
readonly=/mnt/fusion-preserved-inventory
mkdir -p "$results" "$readonly"
cp "$evidence/run-linux.sh" "$results/run-linux.sh"
printf '%s\n' "$@" > "$results/heights.txt"
mount --bind "$source" "$readonly"
mount -o remount,bind,ro "$readonly"
findmnt -no TARGET,FSTYPE,OPTIONS -T "$readonly" > "$results/mount.txt"
findmnt -no OPTIONS -T "$readonly" | grep -Eq '(^|,)ro(,|$)'
ip -brief link > "$results/network.txt"
df -B1 /tmp /mnt/c /mnt/d > "$results/capacity-before.txt"
python3 "$evidence/capture-source.py" "$source" "$results/source-before.json"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
cd "$workspace"
go version > "$results/toolchain.txt"
git -c safe.directory="$workspace" rev-parse HEAD > "$results/baseline.txt"
sha256sum tests/restart/*_test.go internal/ethapi/api_fsn.go eth/api_backend.go core/state/statedb.go common/ticket.go docs/evidence/restart-2026-09-23/responses.json tests/restart/snapshot_package.py > "$results/sources.sha256"
binary="/tmp/fusion-preserved-inventory-$attempt-tests"
test ! -e "$binary"
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR=/tmp go test -p=2 -mod=readonly -c -o "$binary" ./tests/restart > "$results/build.txt" 2>&1
sha256sum "$binary" > "$results/binary.sha256"
cd tests/restart
date -u +%FT%TZ > "$results/started.txt"
for height in "$@"; do
    set +e
    /usr/bin/time -v -o "$results/$height-resources.txt" runuser -u rehearsal -- env GOMAXPROCS=2 FUSION_RESTART_CHAINDATA="$readonly" FUSION_RESTART_FULL_AUDIT=1 FUSION_RESTART_INVENTORY_HEIGHT="$height" FUSION_RESTART_INVENTORY_OUTPUT="$results/$height.json" "$binary" -test.run='^TestPreservedHistoricalInventory$' -test.v -test.timeout=2m > "$results/$height.txt" 2>&1
    result=$?
    set -e
    printf '%s\n' "$result" > "$results/$height-exit.txt"
    tail -n 4 "$results/$height.txt"
    [[ "$result" == 0 ]]
done
date -u +%FT%TZ > "$results/finished.txt"
python3 "$evidence/capture-source.py" "$source" "$results/source-after.json"
cmp "$results/source-before.json" "$results/source-after.json"
df -B1 /tmp /mnt/c /mnt/d > "$results/capacity-after.txt"
