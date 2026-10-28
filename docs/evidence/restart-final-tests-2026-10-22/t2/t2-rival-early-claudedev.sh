# T2 rival test on claudedev: a node holding the heavier rival pre-restart chain joins minutes after the restart,
# while its chain still outweighs the restarted one. The pinned producers must refuse it and stay on the
# recovery blocks; restarted on the pinned build, the rival node must rewind and follow the restarted chain.
# Run as root after the soak, e.g.: sudo systemd-run --unit=t2-rival-early bash /home/peter/t2/t2-rival-early-claudedev.sh
set -uo pipefail
T2=/home/peter/t2
BIN=${T2_BIN:-/home/peter/t2/bin}
SEEDS=$T2/work/seeds
IMGDIR=/var/lib/t2-rehearsal
IMG=$IMGDIR/t2.ext4
MNT=/mnt/t2
EXPECT_EFSN=${T2_EXPECT_EFSN:-e94ad0ec46108cbebd0c68939f98021b897ed3d9c77003c8227fd49c21d03211}
EXPECT_RIVAL=c276fab1d61f598de93e9b68760a035ea027e246f0f794f0da6dea25e2becee3
EXPECT_RECOVERY=bd101c836db182b876e716e6980a87bea11aa8a2711c1b6bc9588607facfa2dc
PHASE1=180
PHASE2=300
REFUSALS='check point failed|reorganization below check point refused|check point mismatch'

[ "$(id -u)" = 0 ] || { echo "run as root"; exit 1; }
systemctl is-active -q t2-soak && { echo "refusing: t2-soak still running"; exit 1; }
[ "$(sha256sum $BIN/efsn | cut -c1-64)" = $EXPECT_EFSN ] || { echo "efsn binary mismatch"; exit 1; }
[ "$(sha256sum $BIN/efsn-rival | cut -c1-64)" = $EXPECT_RIVAL ] || { echo "rival binary mismatch"; exit 1; }
[ "$(sha256sum $T2/work/recovery.rlp | cut -c1-64)" = $EXPECT_RECOVERY ] || { echo "recovery.rlp mismatch"; exit 1; }
for s in a b r; do [ -f $SEEDS/$s/efsn/handover.json ] || { echo "missing seed $s"; exit 1; }; done
ip netns list | grep -q '^t2' && { echo "refusing: t2 namespaces already exist"; exit 1; }
mountpoint -q $MNT && { echo "refusing: $MNT already mounted"; exit 1; }
[ -f $IMG ] || { echo "refusing: no image $IMG"; exit 1; }

LOOP=$(losetup --find --show $IMG)
mkdir -p $MNT
mount $LOOP $MNT || { losetup -d $LOOP; exit 1; }
RUN=$MNT/rival-early-$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p $RUN
chown peter:peter $RUN
RECOVERY=$RUN/recovery.rlp
cp $T2/work/recovery.rlp $RECOVERY
. $T2/lib2-claudedev.sh

cleanup() {
  set +e
  log "cleanup"
  for r in r b a; do stop_node $r TERM; done
  [ -f $RUN/bn.pid ] && kill $(cat $RUN/bn.pid) 2>/dev/null
  sleep 2
  net_down
  sync
  cp $RUN/events.log $T2/work/rival-early-events.log 2>/dev/null
  umount $MNT && losetup -d $LOOP && echo "$(stamp) image unmounted and detached"
}
trap cleanup EXIT
trap 'log "signal received"; exit 1' INT TERM

hash_at() { js $1 "eth.getBlock($2) ? eth.getBlock($2).hash : 'none'" | tr -d '"'; }
td_of() { js $1 "eth.getBlock('latest').totalDifficulty" | tr -d '"'; }
refusals() { grep -c -E "$REFUSALS" $RUN/$1/node.log; }

RIVAL_FIRST=$(grep -o 'T2-RIVAL first=0x[0-9a-f]*' $T2/work/seed-rival.log | cut -d= -f2)
log "T2 rival-early start run=$RUN efsn=${EXPECT_EFSN:0:16} rival=${EXPECT_RIVAL:0:16} rival@15130081=$RIVAL_FIRST"
net_up
setup_node a a 2; setup_node b b 1; setup_node r r 0
for r in a b; do import_recovery $r || { log "FAIL recovery import $r"; exit 1; }; done
$BIN/bootnode -genkey $RUN/bn.key
BOOTNODES="enode://$($BIN/bootnode -nodekey $RUN/bn.key -writeaddress)@$(ip_of bn):$BN_PORT"
write_static a b
write_static b a
chown -R peter:peter $RUN
start_bootnode
start_producer a
start_producer b
sleep 30

write_static r a b
REAL_TD=$(td_of a)
start_node r $BIN/efsn-rival
sleep 15
RIVAL_TD=$(td_of r)
log "rival joins: a=$(status a) td=$REAL_TD | r=$(status r) td=$RIVAL_TD"
HEAVIER=0
[[ $REAL_TD =~ ^[0-9]+$ && $RIVAL_TD =~ ^[0-9]+$ ]] && [ $RIVAL_TD -gt $REAL_TD ] && HEAVIER=1
END1=$(( $(date +%s) + PHASE1 ))
while [ $(date +%s) -lt $END1 ]; do
  log "phase 1 | a: $(status a) @81=$(hash_at a 15130081 | cut -c1-12) | b: $(status b) @81=$(hash_at b 15130081 | cut -c1-12) | r: $(status r) @81=$(hash_at r 15130081 | cut -c1-12) td=$(td_of r)"
  sleep 30
done
A81=$(hash_at a 15130081); B81=$(hash_at b 15130081); R81=$(hash_at r 15130081)
A_REF=$(refusals a); B_REF=$(refusals b)
log "phase 1 end: a@81=$A81 b@81=$B81 r@81=$R81 refusals a=$A_REF b=$B_REF rival-heavier-at-join=$HEAVIER"
grep -h -E "$REFUSALS" $RUN/a/node.log $RUN/b/node.log | head -5 | tee -a $RUN/events.log

stop_node r TERM
start_node r $BIN/efsn
END2=$(( $(date +%s) + PHASE2 ))
R81B=none
while [ $(date +%s) -lt $END2 ]; do
  sleep 20
  R81B=$(hash_at r 15130081)
  log "phase 2 | a: $(status a) | r: $(status r) @81=$(echo $R81B | cut -c1-12)"
  [ "$R81B" = $PIN81 ] && [ "$(js r eth.blockNumber)" -ge "$(( $(js a eth.blockNumber) - 2 ))" ] 2>/dev/null && break
done
R_REWIND=$(grep -c "check point mismatch" $RUN/r/node.log)
log "phase 2 end: r@81=$R81B a=$(status a) r=$(status r) rewind lines on r=$R_REWIND"
grep -h -E "$REFUSALS" $RUN/r/node.log | head -3 | tee -a $RUN/events.log

result() { if [ "$2" = 1 ]; then log "PASS $1"; else log "FAIL $1"; fi; }
result "rival chain heavier than the restarted chain when it joined ($RIVAL_TD > $REAL_TD)" $HEAVIER
result "producers kept the pinned recovery block 15130081" $([ "$A81" = $PIN81 ] && [ "$B81" = $PIN81 ] && echo 1 || echo 0)
result "producers logged refusals of the rival chain (a=$A_REF b=$B_REF)" $([ $((A_REF + B_REF)) -gt 0 ] && echo 1 || echo 0)
result "rival node stayed on its own chain while on the rival build" $([ "$R81" = "$RIVAL_FIRST" ] && echo 1 || echo 0)
result "rival node on the pinned build follows the restarted chain" $([ "$R81B" = $PIN81 ] && echo 1 || echo 0)
result "rival node on the pinned build rewound at startup (check point mismatch lines=$R_REWIND)" $([ $R_REWIND -gt 0 ] && echo 1 || echo 0)
