set -euo pipefail
T2=/home/peter/t2
WORK=$T2/work
REPO=/home/peter/work/fsn-efsn
EXPORT=$REPO/tmp/preserved-head-state
MAN=$REPO/docs/evidence/restart-state-export-2026-09-24/artifact-SHA256SUMS
HIST=$REPO/tmp/partition-history-2026-09-26/history.rlp
HARNESS=$T2/bin/t2-harness.test
OPERATOR=/home/peter/final-bin/fsn-recovery
export PATH=/home/peter/toolchains/go1.27.3/bin:$PATH
stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }

copy_export() {
  local dst=$1
  [ "$(sha256sum $MAN | cut -c1-64)" = a6c86fc58a9f7b482a02b787a337d600e32a447551e45dbe40d210b498341bbf ]
  [ ! -e "$dst" ] || { echo "refusing: $dst exists"; exit 1; }
  mkdir -p "$dst"
  cp -r $EXPORT/. "$dst/"
  (cd "$dst" && sha256sum --quiet -c $MAN)
  [ "$(find "$dst" -type f | wc -l)" = 230 ]
  printf '{\n  "Source": "%s",\n  "ManifestSHA256": "a6c86fc58a9f7b482a02b787a337d600e32a447551e45dbe40d210b498341bbf",\n  "Files": 230\n}\n' "$EXPORT" > "$dst/copy-verified.json"
  echo "$(stamp) verified copy $dst"
}

[ "$(id -u)" != 0 ] || { echo "run as peter, not root"; exit 1; }
[ ! -e $WORK ] || { echo "refusing: $WORK exists"; exit 1; }
mkdir -p $WORK
cd $T2/src-tools/tests/restart

echo "$(stamp) operator: three recovery blocks with the real fsn-recovery"
for r in reference working verifier; do copy_export $WORK/operator/$r; done
env GOMAXPROCS=2 FUSION_RESTART_CHAINDATA= FUSION_RESTART_OPERATOR_FULL_STATE_ROOT=$WORK/operator FUSION_RECOVERY_OPERATOR=$OPERATOR \
  $HARNESS -test.run '^TestFullStateRecoveryOperator$' -test.v -test.timeout 40m > $WORK/operator.log 2>&1 \
  || { echo "$(stamp) operator FAIL"; tail -40 $WORK/operator.log; exit 1; }
grep -E "reference stage=|stage=.: actual|^(--- |PASS|ok)" $WORK/operator.log
cat $WORK/operator/operator-1-block.rlp $WORK/operator/operator-2-block.rlp $WORK/operator/operator-3-block.rlp > $WORK/recovery.rlp

echo "$(stamp) seeds"
for r in a b x j r; do
  copy_export $WORK/seeds/$r/efsn
  env GOMAXPROCS=2 FUSION_RESTART_CHAINDATA= T2_NODE_FIXTURE=$WORK/seeds/$r/efsn T2_HISTORY_INPUT=$HIST \
    $HARNESS -test.run '^TestT2PrepareNode$' -test.v -test.timeout 20m > $WORK/seed-$r.log 2>&1 \
    || { echo "$(stamp) seed $r FAIL"; tail -20 $WORK/seed-$r.log; exit 1; }
  grep -o "T2-SEED.*\|genuine ancestry installed blocks=[0-9]*" $WORK/seed-$r.log
done
env GOMAXPROCS=2 FUSION_RESTART_CHAINDATA= T2_RIVAL_FIXTURE=$WORK/seeds/r/efsn T2_RIVAL_BLOCKS=60 \
  $HARNESS -test.run '^TestT2RivalChain$' -test.v -test.timeout 20m > $WORK/seed-rival.log 2>&1 \
  || { echo "$(stamp) rival FAIL"; tail -20 $WORK/seed-rival.log; exit 1; }
grep -o "T2-RIVAL.*" $WORK/seed-rival.log

sha256sum $WORK/recovery.rlp $T2/bin/*
du -sh $WORK/seeds/* $WORK/operator
echo "$(stamp) prep done"
