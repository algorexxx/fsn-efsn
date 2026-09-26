#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
cd "$workspace"
{
  date -u --iso-8601=seconds
  git rev-parse HEAD
  uname -a
  /opt/fusion-toolchain/go/bin/go version
  /usr/sbin/tc -V
  /usr/sbin/ip -V
  df -h /tmp
} > "$workspace/docs/evidence/restart-continuous-partitions-2026-09-26/environment.txt"
