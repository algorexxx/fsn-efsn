#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
root=/mnt/d/FusionRehearsal/expired-nonce-neutralization-2026-09-27
results="$workspace/docs/evidence/restart-expired-nonce-neutralization-2026-09-27"
binary="$root/restart-tests"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
cd "$workspace"
[[ ! -e "$binary" && ! -e "$results/live-race.txt" ]]
df -B1 /tmp /mnt/c /mnt/d > "$results/capacity-before.txt"
sha256sum tests/restart/{full_state_nonce_neutralization_linux,full_state_participant_ledger,node_rehearsal_linux,full_state_retry_partition_linux,partition_funds_ledger_linux,full_state_paused_purchase_linux,purchase_peer_linux}_test.go > "$results/test-sources.sha256"
sha256sum core/{blockchain,tx_pool}.go common/fsnparams.go internal/ethapi/{api,api_fsn,autobuy}.go > "$results/production-sources.sha256"
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR=/tmp go test -race -p=2 -mod=readonly -c -o "$binary" ./tests/restart > "$results/build.txt" 2>&1
sha256sum "$binary" > "$results/binary.sha256"
set +e
unshare --net -- bash -c 'set -e; ip link set lo up; ip -brief link; cd "$1/tests/restart"; exec env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= FUSION_RESTART_NODE_REHEARSAL=1 FUSION_RESTART_NETWORK_PARTITION=1 FUSION_RESTART_NODE_DEBUG=1 FUSION_RESTART_HOST_STORAGE=/mnt/d FUSION_RESTART_RETRY_PARTITION="$2" "$3" -test.run="^TestFullStateExplicitNonceNeutralization$" -test.v -test.timeout=8m' bash "$workspace" "$root" "$binary" > "$results/live-race.txt" 2>&1
live=$?
printf '%s\n' "$live" > "$results/live-exit.txt"
tail -n 12 "$results/live-race.txt"
unshare --net -- bash -c 'set -e; ip link set lo up; cd "$1/tests/restart"; exec env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= FUSION_RESTART_NODE_REHEARSAL=1 FUSION_RESTART_NETWORK_PARTITION=1 FUSION_RESTART_HOST_STORAGE=/mnt/d FUSION_RESTART_RETRY_PARTITION="$2" "$3" -test.run="^TestFullStateNonceNeutralizationColdAudit$" -test.v -test.timeout=4m' bash "$workspace" "$root" "$binary" > "$results/cold-race.txt" 2>&1
cold=$?
printf '%s\n' "$cold" > "$results/cold-exit.txt"
tail -n 12 "$results/cold-race.txt"
[[ "$live" == 0 && "$cold" == 0 ]]
