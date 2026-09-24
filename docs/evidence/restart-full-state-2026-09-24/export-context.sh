#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
source=/home/rehearsal/fsn-efsn-full-state-context-v2
results="$workspace/docs/evidence/restart-full-state-2026-09-24"
binary="$workspace/tmp/full-state-context-v2-linux-tests"
test ! -e "$source"
test ! -e "$binary"
mkdir "$source"
tar -xf "$workspace/tmp/full-state-base.tar" -C "$source"
cp "$workspace"/tests/restart/full_state*test.go "$source/tests/restart/"
chown -R rehearsal:rehearsal "$source"
cd "$source"
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 go test -race -p=2 -mod=readonly -c -o "$binary" ./tests/restart > "$results/context-build.txt" 2>&1
sha256sum "$binary" tests/restart/full_state*test.go > "$results/context-build-identity.txt"
test -f /home/rehearsal/results/backup-copy-2026-09-23/verified.txt
mountpoint=/mnt/fusion-full-state-context
mkdir -p "$mountpoint"
mount --bind /home/rehearsal/data/efsn/chaindata "$mountpoint"
mount -o remount,bind,ro "$mountpoint"
findmnt -no TARGET,OPTIONS -T "$mountpoint" > "$results/context-isolation.txt"
ip -brief link >> "$results/context-isolation.txt"
cd tests/restart
runuser -u rehearsal -- env GOMAXPROCS=2 FUSION_RESTART_FULL_AUDIT=1 FUSION_RESTART_CHAINDATA="$mountpoint" FUSION_RESTART_CONTEXT_OUTPUT="$results/context.rlp" "$binary" '-test.run=^TestExportFullStateContext$' -test.v -test.timeout=5m > "$results/context-export.txt" 2>&1
umount "$mountpoint"
cat "$results/context-export.txt"
