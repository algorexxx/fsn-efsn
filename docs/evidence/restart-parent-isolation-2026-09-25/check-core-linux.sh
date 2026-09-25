#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-parent-isolation-2026-09-25"
cd "$workspace"
unshare --net -- runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 TMPDIR=/tmp GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly ./core -run '^Test((ExtendCanonical|ShorterFork|LongerFork|EqualFork|ReorgLong|ReorgShort)(Headers|Blocks)|Broken(Header|Block)Chain|(Reorg)?Bad(Header|Block)Hashes|(Headers|Blocks)InsertNonceError|BlockchainHeaderchainReorgConsistency)$' -v -count=1 -timeout=4m > "$results/linux-core-race.txt" 2>&1
tail -n 4 "$results/linux-core-race.txt"
