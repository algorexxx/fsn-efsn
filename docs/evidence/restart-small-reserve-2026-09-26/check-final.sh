#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-small-reserve-2026-09-26"
binary="$workspace/tmp/small-reserve-final-tests"
cd "$workspace"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
mode=${1:?build, rpc, small or rich}
if [[ "$mode" == build ]]; then
  {
    date -u --iso-8601=seconds
    git -c safe.directory="$workspace" rev-parse HEAD
    uname -a
    go version
    tc -V
    df -h /tmp
  } > "$results/final-environment.txt"
  runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -c -o "$binary" ./tests/restart > "$results/final-build.txt" 2>&1
  sha256sum "$binary" > "$results/final-binary.sha256"
  exit
fi
case "$mode" in
  rpc) pattern='^TestRestartNodeRehearsal$/(dense_miner_fixture|purchase_peer_nonce_rollback)$' ;;
  small) pattern='^TestRestartNodeRehearsal$/small_reserve_nonce_repair$' ;;
  rich) pattern='^TestRestartNodeRehearsal$/continuous_partition_nonce_repair$' ;;
  *) exit 2 ;;
esac
label=${2:?unique evidence label}
[[ "$label" =~ ^[a-z0-9-]+$ ]]
[[ ! -e "$results/$label-race.txt" ]]
set +e
unshare --net -- bash -c 'set -e; ip link set lo up; ip -brief link; cd "$1/tests/restart"; exec env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= FUSION_RESTART_NODE_REHEARSAL=1 FUSION_RESTART_NETWORK_PARTITION=1 "$2" "-test.run=$3" -test.v -test.timeout=12m' bash "$workspace" "$binary" "$pattern" > "$results/$label-race.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/$label-exit.txt"
tail -n 8 "$results/$label-race.txt"
exit "$status"
