# User: build the three recovery blocks with the real fsn-recovery (union build) on fresh complete-state copies.
set -euo pipefail
. "$(dirname "$0")/../env.sh"
T2=$SP/t2
ROOT=$T2/work/operator
[ ! -e $ROOT ] || { echo "refusing: $ROOT exists"; exit 1; }
for r in reference working verifier; do bash $T2/copy-export.sh $ROOT/$r; done
cd ~/t2/src-tools/tests/restart
date -u
env GOMAXPROCS=2 FUSION_RESTART_CHAINDATA= FUSION_RESTART_OPERATOR_FULL_STATE_ROOT=$ROOT FUSION_RECOVERY_OPERATOR=/home/rehearsal/final-bin/fsn-recovery \
  ~/t2/bin/t2-harness.test -test.run '^TestFullStateRecoveryOperator$' -test.v -test.timeout 40m > $T2/work/operator.log 2>&1 && echo PASS || { echo FAIL; tail -40 $T2/work/operator.log; exit 1; }
date -u
grep -E "reference stage=|stage=.: actual|^(--- |PASS|ok)" $T2/work/operator.log
ls -la $ROOT/operator-*-block.rlp
sha256sum $ROOT/operator-*-block.rlp
