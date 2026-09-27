#!/bin/bash
set -euo pipefail
results=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-manual-purchase-delivery-2026-09-27
[[ ! -e "$results/environment-final.txt" ]]
{
    date --iso-8601=seconds
    /opt/fusion-toolchain/go/bin/go version
    df -B1 /tmp /mnt/c /mnt/d
    if pgrep -ax 'restart-tests|protocol-tests|efsn'; then
        exit 1
    fi
    echo 'No rehearsal node or test process remains.'
} > "$results/environment-final.txt"
cat "$results/environment-final.txt"
