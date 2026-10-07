#!/bin/bash
# Bounded re-run of the self-destruct parent-rollback fixture against both
# established source selections, with full provenance capture. Runtime source
# trees are never edited; the fixture is injected via `go test -overlay`.
# Run from inside the FusionRehearsal WSL distro as:
#   bash <this-dir>/run.sh
set -uo pipefail

evid=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-state-rollback-followup-2026-10-07
qualified=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-state-tests-2026-10-07/qualified
prior=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-state-tests-2026-10-07/corrected/suicide_evm_test.go
fixture="$evid/suicide_evm_test.go"
toolchain=/home/rehearsal/results/restart-release-selection-2026-10-04/toolchain/go
gocache=/home/rehearsal/results/restart-release-selection-2026-10-04/repeat-cache

export PATH="$toolchain/bin:/usr/bin:/bin"
export GOTOOLCHAIN=local GOWORK=off GOPROXY=off GOSUMDB=off GOFLAGS=-mod=readonly
export CGO_ENABLED=1 GOAMD64=v1 GOMAXPROCS=2 GOCACHE="$gocache"

env_file="$evid/environment.txt"
{
  echo "run-date-utc: $(date -u +%FT%TZ)"
  echo "user: $(whoami)"
  echo "distro: FusionRehearsal (WSL2)"
  echo "go: $(go version)"
  echo "gcc: $(gcc --version | head -1)"
  echo "go-env: GOTOOLCHAIN=local GOWORK=off GOPROXY=off GOSUMDB=off GOFLAGS=-mod=readonly CGO_ENABLED=1 GOAMD64=v1 GOMAXPROCS=2"
  echo "GOCACHE: $gocache"
  echo "GOTMPDIR: (default /tmp)"
  echo "test-flags: -race -p=2 -count=1 -timeout=5m -run TestSelfdestructParentRollback -v ./core/state"
  echo "inner-timeout: 5m (go test)   outer-limit: 7m (timeout --kill-after=20s)"
  echo "network-namespace: unshare -n NOT PERMITTED for user rehearsal; ran in the distro default namespace."
  echo "network-use: none possible — GOPROXY=off GOSUMDB=off GOFLAGS=-mod=readonly, cached modules only."
  echo "net-ns-inode: $(readlink /proc/self/ns/net)"
  echo "ip-links:"
  ip -brief link | sed 's/^/  /'
  echo "disk:"
  df -BG /home/rehearsal/results /mnt/d | sed 's/^/  /'
} > "$env_file"

# Capacity gate (30 GiB Linux, 60 GiB D:). Record, do not silently proceed.
python3 - "$env_file" <<'PY'
import shutil, sys
lin = shutil.disk_usage('/home/rehearsal/results').free / 1024**3
dfree = shutil.disk_usage('/mnt/d').free / 1024**3
ok = lin > 30 and dfree > 60
with open(sys.argv[1], 'a') as f:
    f.write(f"capacity-check: linux={lin:.1f}GiB (>30) d={dfree:.1f}GiB (>60) ok={ok}\n")
sys.exit(0 if ok else 2)
PY
if [ $? -ne 0 ]; then echo "capacity check failed; aborting" | tee -a "$env_file"; exit 2; fi

# Preserve the exact delta from the preceding fixture.
diff -u "$prior" "$fixture" > "$evid/fixture-from-corrected.patch"
echo "fixture-patch-vs-corrected: $(wc -l < "$evid/fixture-from-corrected.patch") lines" >> "$env_file"

run_selection() {
  local label="$1" node="$2" out="$evid/$3"
  mkdir -p "$out"

  {
    echo "selection: $label"
    echo "node-tree: $node"
    echo "runtime-source-hashes:"
    sha256sum "$node/core/state/statedb.go" "$node/core/state/journal.go" "$node/core/state/state_object.go" | sed 's/^/  /'
  } > "$out/source-selection.txt"

  # Overlay: ported five-file suite + the new fixture, injected over this tree.
  local ov="$out/overlay.json"
  {
    printf '{\n  "Replace": {\n'
    printf '    "%s/core/state/state_test.go": "%s/state_test.go",\n' "$node" "$qualified"
    printf '    "%s/core/state/statedb_test.go": "%s/statedb_test.go",\n' "$node" "$qualified"
    printf '    "%s/core/state/iterator_test.go": "%s/iterator_test.go",\n' "$node" "$qualified"
    printf '    "%s/core/state/sync_test.go": "%s/sync_test.go",\n' "$node" "$qualified"
    printf '    "%s/core/state/suicide_test.go": "%s/suicide_test.go",\n' "$node" "$qualified"
    printf '    "%s/core/state/suicide_evm_test.go": "%s"\n' "$node" "$fixture"
    printf '  }\n}\n'
  } > "$ov"

  date -u +%FT%TZ > "$out/started.txt"
  ( cd "$node" && timeout --signal=TERM --kill-after=20s 7m \
      go test -overlay="$ov" -race -p=2 -count=1 -timeout=5m \
      -run TestSelfdestructParentRollback -v ./core/state ) > "$out/test.txt" 2>&1
  echo "$?" > "$out/exit.txt"
  date -u +%FT%TZ > "$out/finished.txt"
  echo "$label exit=$(cat "$out/exit.txt")"
}

run_selection "Selected D1 baseline (jwt)" /home/rehearsal/results/restart-release-jwt-2026-10-04/node d1
run_selection "Unselected text experiment" /home/rehearsal/results/restart-release-text-2026-10-04/node text

# Inventory/checksum manifest covering the new evidence files.
( cd "$evid" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum ) > "$evid/SHA256SUMS"
echo "manifest entries: $(wc -l < "$evid/SHA256SUMS")"
echo "done"
