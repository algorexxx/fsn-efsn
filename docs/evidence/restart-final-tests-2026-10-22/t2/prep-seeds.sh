# User: rebuild harness, build the rival efsn (pins only the synthetic parent), prepare five node seeds.
set -euo pipefail
. "$(dirname "$0")/../env.sh"
T2=$SP/t2
cd ~/t2/src-tools
cp $T2/harness/t2_harness_test.go tests/restart/
git add tests/restart/t2_harness_test.go
git -c user.name=t2 -c user.email=t2@local commit -q -m "T2 harness: open the seed once (history install held a second LevelDB handle)"
git log --oneline -1
go vet ./tests/restart
go test -c -o ~/t2/bin/t2-harness.test ./tests/restart
# rival build: efsn-final with only 15130080 moved to the synthetic parent
if [ ! -e ~/t2/src-rival ]; then
  git clone -q ~/efsn-final ~/t2/src-rival
  cd ~/t2/src-rival
  sed -i 's/15130080: common.HexToHash("0xe93ffded087a79097d4309c7831690161db6ed136f4b1a22c4c83a99db80f99f")/15130080: common.HexToHash("0xe463e592a96c93420fbf155824b4ee95ba418ee29312637e8dd08eea43951458")/' consensus/datong/checkpoints.go
  git diff --stat
  git -c user.name=t2 -c user.email=t2@local commit -qam "REHEARSAL ONLY (T2 rival): pin only the synthetic parent"
  go build -o ~/t2/bin/efsn-rival ./cmd/efsn
fi
git -C ~/t2/src-rival log --oneline -1
SEEDS=$T2/work/seeds
HIST=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/tmp/partition-history-2026-09-26/history.rlp
cd ~/t2/src-tools/tests/restart
for r in a b x j r; do
  bash $T2/copy-export.sh $SEEDS/$r/efsn
  env GOMAXPROCS=2 FUSION_RESTART_CHAINDATA= T2_NODE_FIXTURE=$SEEDS/$r/efsn T2_HISTORY_INPUT=$HIST \
    ~/t2/bin/t2-harness.test -test.run '^TestT2PrepareNode$' -test.v -test.timeout 20m > $T2/work/seed-$r.log 2>&1 || { tail -20 $T2/work/seed-$r.log; exit 1; }
  grep -o "T2-SEED.*\|genuine ancestry installed blocks=[0-9]*" $T2/work/seed-$r.log
done
env GOMAXPROCS=2 FUSION_RESTART_CHAINDATA= T2_RIVAL_FIXTURE=$SEEDS/r/efsn T2_RIVAL_BLOCKS=60 \
  ~/t2/bin/t2-harness.test -test.run '^TestT2RivalChain$' -test.v -test.timeout 20m > $T2/work/seed-rival.log 2>&1 || { tail -20 $T2/work/seed-rival.log; exit 1; }
grep -o "T2-RIVAL.*" $T2/work/seed-rival.log
cat $T2/work/operator/operator-1-block.rlp $T2/work/operator/operator-2-block.rlp $T2/work/operator/operator-3-block.rlp > $T2/work/recovery.rlp
sha256sum $T2/work/recovery.rlp ~/t2/bin/* | sed "s#$HOME/##; s#$SP/##"
du -sh $SEEDS/*
df -h / | tail -1
