#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
source="$workspace/tmp/full-state-handover-linux-src"
results="$workspace/docs/evidence/restart-full-state-handover-2026-09-24"
binary="$workspace/tmp/full-state-handover-linux-tests"
export HANDOVER_WORKSPACE="$workspace"
test ! -e "$source"
test ! -e "$binary"
mkdir "$source"
tar -xf "$workspace/tmp/full-state-handover-base.tar" -C "$source"
cp "$workspace"/tests/restart/full_state_handover*_test.go "$workspace/tests/restart/full_state_rehearsal_test.go" "$source/tests/restart/"
mkdir "$workspace/tmp/full-state-handover-linux-gotmp"
cd "$source"
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/full-state-handover-linux-gotmp" go test -race -p=2 -mod=readonly -c -o "$binary" ./tests/restart > "$results/linux-build.txt" 2>&1
sha256sum "$binary" tests/restart/full_state_handover*_test.go tests/restart/full_state_rehearsal_test.go > "$results/linux-identity.txt"
python3 - <<'PY'
import hashlib, json, os, pathlib, shutil
workspace = pathlib.Path(os.environ['HANDOVER_WORKSPACE'])
source = workspace/'tmp/preserved-head-state'
manifest = workspace/'docs/evidence/restart-state-export-2026-09-24/artifact-SHA256SUMS'
expected = 'a6c86fc58a9f7b482a02b787a337d600e32a447551e45dbe40d210b498341bbf'
assert hashlib.sha256(manifest.read_bytes()).hexdigest() == expected
entries = [line.split('  ', 1) for line in manifest.read_text().splitlines()]
assert len(entries) == 230
assert shutil.disk_usage(workspace).free > 55 * 1024**3
for role in ['producer','verifier']:
    target = workspace/f'tmp/full-state-handover-linux-{role}'
    assert not target.exists()
    target.mkdir()
    for checksum, name in entries:
        relative = pathlib.PurePosixPath(name)
        assert not relative.is_absolute() and '..' not in relative.parts
        destination = target/relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source/relative, destination)
        assert hashlib.sha256(destination.read_bytes()).hexdigest() == checksum
    proof = {'Source': str(source), 'ManifestSHA256': expected, 'Files': len(entries)}
    (target/'copy-verified.json').write_text(json.dumps(proof, indent=2)+'\n')
    (workspace/f'docs/evidence/restart-full-state-handover-2026-09-24/linux-{role}-copy-verified.json').write_text(json.dumps(proof, indent=2)+'\n')
PY
cd tests/restart
for phase in producer:prepare verifier:prepare producer:produce producer:runtime-first producer:runtime-restart verifier:import; do
    role="${phase%%:*}"
    label="${phase#*:}"
    mode="${label%%-*}"
    unshare --net -- runuser -u rehearsal -- env GOMAXPROCS=2 FUSION_RESTART_HANDOVER_DIR="$workspace/tmp/full-state-handover-linux-$role" FUSION_RESTART_HANDOVER_MODE="$mode" FUSION_RESTART_HANDOVER_BLOCKS="$workspace/tmp/full-state-handover-linux-blocks" "$binary" '-test.run=^TestFullStateHandover$' -test.v -test.timeout=10m > "$results/linux-$role-$label.txt" 2>&1
    tail -n 3 "$results/linux-$role-$label.txt"
done
unshare --net -- runuser -u rehearsal -- env GOMAXPROCS=2 FUSION_RESTART_HANDOVER_AUDIT="$workspace/tmp/full-state-handover-linux-producer" FUSION_RESTART_HANDOVER_BLOCKS="$workspace/tmp/full-state-handover-linux-blocks" "$binary" '-test.run=^Test(HandoverFundingGuard|HandoverTemporalAccounting|FullStateHandoverAccounting|FullStateDifferenceAccounting|FullStateContextIntegrity|SingleBackupBlockHandover|SingleBackupBlockRejectsShortSuccessorTicket)$' -test.v -test.count=2 -test.timeout=3m > "$results/linux-accounting-race.txt" 2>&1
tail -n 4 "$results/linux-accounting-race.txt"
