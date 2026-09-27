#!/bin/bash
set -euo pipefail
results=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-equal-weight-pause-2026-09-27
[[ ! -e "$results/final-environment.txt" ]]
{
    date -u
    if pgrep -ax 'restart-tests|protocol-tests|efsn'; then
        printf 'Unexpected remaining rehearsal process.\n'
        exit 1
    fi
    printf 'No restart-tests, protocol-tests or efsn processes remain.\n'
    df -B1 /tmp /mnt/c /mnt/d
} > "$results/final-environment.txt"
