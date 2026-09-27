#!/bin/bash
set -euo pipefail
results=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-live-abandonment-repair-2026-09-27
set -o noclobber
{
    date -u
    if pgrep -ax 'restart-tests|protocol-tests|efsn'; then
        exit 1
    fi
    df -B1 /tmp /mnt/c /mnt/d
} > "$results/final-environment.txt"
cat "$results/final-environment.txt"
