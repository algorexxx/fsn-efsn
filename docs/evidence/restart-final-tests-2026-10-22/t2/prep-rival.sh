# User: (re)build the harness and the rival seed only.
set -euo pipefail
. "$(dirname "$0")/../env.sh"
T2=$SP/t2
cd ~/t2/src-tools
cp $T2/harness/t2_harness_test.go tests/restart/
git add tests/restart/t2_harness_test.go
git -c user.name=t2 -c user.email=t2@local commit -q -m "T2 harness: rival purchases keep the one-month minimum after the jump"
git log --oneline -1
go test -c -o ~/t2/bin/t2-harness.test ./tests/restart
SEEDS=$T2/work/seeds
HIST=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/tmp/partition-history-2026-09-26/history.rlp
mkdir -p $T2/work/seeds-attempt2
[ ! -e $SEEDS/r ] || mv $SEEDS/r $T2/work/seeds-attempt2/r
cd ~/t2/src-tools/tests/restart
bash $T2/copy-export.sh $SEEDS/r/efsn
env GOMAXPROCS=2 FUSION_RESTART_CHAINDATA= T2_NODE_FIXTURE=$SEEDS/r/efsn T2_HISTORY_INPUT=$HIST \
  ~/t2/bin/t2-harness.test -test.run '^TestT2PrepareNode$' -test.v -test.timeout 20m > $T2/work/seed-r.log 2>&1 || { tail -20 $T2/work/seed-r.log; exit 1; }
grep -o "T2-SEED.*" $T2/work/seed-r.log
env GOMAXPROCS=2 FUSION_RESTART_CHAINDATA= T2_RIVAL_FIXTURE=$SEEDS/r/efsn T2_RIVAL_BLOCKS=60 \
  ~/t2/bin/t2-harness.test -test.run '^TestT2RivalChain$' -test.v -test.timeout 20m > $T2/work/seed-rival.log 2>&1 || { tail -20 $T2/work/seed-rival.log; exit 1; }
grep -o "T2-RIVAL.*" $T2/work/seed-rival.log
cat $T2/work/operator/operator-1-block.rlp $T2/work/operator/operator-2-block.rlp $T2/work/operator/operator-3-block.rlp > $T2/work/recovery.rlp
sha256sum $T2/work/recovery.rlp ~/t2/bin/* | sed "s#$HOME/##; s#$SP/##"
du -sh $SEEDS/*
df -h / | tail -1
