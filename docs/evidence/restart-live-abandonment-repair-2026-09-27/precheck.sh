#!/bin/bash
set -euo pipefail
if pgrep -ax 'restart-tests|protocol-tests|efsn'; then
    exit 1
fi
df -B1 /tmp /mnt/c /mnt/d
