# T2 48 h soak with fault schedule. Run as root, held by a wsl.exe session:
#   wsl -d FusionRehearsal -u root -- bash /mnt/c/Users/Peter/AppData/Local/Temp/claude/C--Users-Peter-Documents-CODING-fsn-efsn/a8ea1c11-81b9-474d-b4c3-dda6b28fadac/scratchpad/t2/t2-soak.sh
# Optional env: T2_SCALE (default 1; e.g. 0.05 = 2.4 h dry run with the same schedule), T2_ALLOW_T1=1 (skip T1 guard).
# Stop early: touch /mnt/t2/STOP (checked every poll); cleanup always stops nodes, removes namespaces, unmounts.
set -uo pipefail
T2=/mnt/c/Users/Peter/AppData/Local/Temp/claude/C--Users-Peter-Documents-CODING-fsn-efsn/a8ea1c11-81b9-474d-b4c3-dda6b28fadac/scratchpad/t2
BIN=/home/rehearsal/t2/bin
SEEDS=$T2/work/seeds
IMGDIR=/mnt/w/FusionRestart/t2-rehearsal-2026-10-22
IMG=$IMGDIR/t2.ext4
MNT=/mnt/t2
SCALE=${T2_SCALE:-1}
EXPECT_EFSN=e94ad0ec46108cbebd0c68939f98021b897ed3d9c77003c8227fd49c21d03211
EXPECT_RIVAL=c276fab1d61f598de93e9b68760a035ea027e246f0f794f0da6dea25e2becee3
EXPECT_RECOVERY=bd101c836db182b876e716e6980a87bea11aa8a2711c1b6bc9588607facfa2dc

# ---------- preflight (nothing changed yet) ----------
[ "$(id -u)" = 0 ] || { echo "run as root"; exit 1; }
if [ "${T2_ALLOW_T1:-0}" != 1 ] && { pgrep -f replay.test >/dev/null || mountpoint -q /mnt/t1-target; }; then
  echo "refusing: T1 still running or /mnt/t1-target mounted"; exit 1
fi
[ "$(sha256sum $BIN/efsn | cut -c1-64)" = $EXPECT_EFSN ] || { echo "efsn binary mismatch"; exit 1; }
[ "$(sha256sum $BIN/efsn-rival | cut -c1-64)" = $EXPECT_RIVAL ] || { echo "rival binary mismatch"; exit 1; }
[ "$(sha256sum $T2/work/recovery.rlp | cut -c1-64)" = $EXPECT_RECOVERY ] || { echo "recovery.rlp mismatch"; exit 1; }
for s in a b x j r; do [ -f $SEEDS/$s/efsn/handover.json ] || { echo "missing seed $s"; exit 1; }; done
[ -f $SEEDS/r/efsn/rival-blocks.rlp ] || { echo "rival seed lacks its rival chain"; exit 1; }
ip netns list | grep -q '^t2' && { echo "refusing: t2 namespaces already exist"; exit 1; }
[ $(df --output=avail -k / | tail -1) -gt $((15 * 1024 * 1024)) ] || { echo "Linux root below 15 GiB free"; exit 1; }
mountpoint -q /mnt/w || { echo "/mnt/w (W:) not mounted"; exit 1; }
for t in ip tc setpriv; do command -v $t >/dev/null || { echo "missing $t"; exit 1; }; done

# ---------- storage ----------
mkdir -p $IMGDIR
if [ ! -e $IMG ]; then truncate -s 64G $IMG && mkfs.ext4 -q -F -L t2rehearsal $IMG; fi
LOOP=$(losetup --find --show $IMG)
mkdir -p $MNT
mount $LOOP $MNT || { losetup -d $LOOP; exit 1; }
chown rehearsal:rehearsal $MNT
RUN=$MNT/soak-$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p $RUN
RECOVERY=$RUN/recovery.rlp
cp $T2/work/recovery.rlp $RECOVERY
. $T2/lib2.sh

cleanup() {
  set +e
  log "cleanup"
  for r in r k j x b a; do stop_node $r TERM; done
  [ -f $RUN/bn.pid ] && kill $(cat $RUN/bn.pid) 2>/dev/null
  sleep 2
  net_down
  sync
  cp $RUN/events.log $RUN/summary.txt $T2/work/ 2>/dev/null
  umount $MNT && losetup -d $LOOP && log "image unmounted and detached"
  echo "$(stamp) done; results under $IMG (soak dir $(basename $RUN)); events copied to $T2/work/"
}
trap cleanup EXIT
trap 'log "signal received"; exit 1' INT TERM

H() { awk -v h=$1 -v s=$SCALE 'BEGIN { printf "%d", h * 3600 * s }'; }  # scaled hours -> seconds
M() { local v=$(awk -v m=$1 -v s=$SCALE 'BEGIN { printf "%d", m * 60 * s }'); [ $v -lt ${2:-60} ] && v=${2:-60}; echo $v; }
log "T2 soak start scale=$SCALE run=$RUN efsn=${EXPECT_EFSN:0:16} recovery=${EXPECT_RECOVERY:0:16}"
log "free: $(df -h --output=avail / $MNT | tail -2 | tr -s ' \n' ' ')"

# ---------- setup ----------
net_up
setup_node a a 2; setup_node b b 1; setup_node x x 0; setup_node j j 0; setup_node r r 0
for r in a b x j; do import_recovery $r || { log "FAIL recovery import $r"; exit 1; }; done
log "rival seed head: $(cat $SEEDS/r/efsn/../../../seed-rival.log 2>/dev/null | grep -o 'T2-RIVAL.*' | head -1)"
$BIN/bootnode -genkey $RUN/bn.key
BOOTNODES="enode://$($BIN/bootnode -nodekey $RUN/bn.key -writeaddress)@$(ip_of bn):$BN_PORT"
write_static a b x
write_static b a x
write_static x a b
chown -R rehearsal:rehearsal $RUN

# ---------- schedule ----------
T0=$(date +%s)
at() { echo $((T0 + $1)); }
EV_JOIN_J=$(at $(H 1)); EV_KILL_A=$(at $(H 6)); EV_RESTART_B=$(at $(H 8)); EV_PART=$(at $(H 12))
EV_SNAP_K=$(at $(H 16)); EV_RIVAL=$(at $(H 20)); EV_END=$(at $(H 48))
A_DOWN=$(M 10); B_DOWN=$(M 2 30); PART_LEN=$(M 30 120); RIVAL_LEN=$(M 30 300); POLL=$(M 5 30); CHECK=$(H 1); [ $CHECK -lt 300 ] && CHECK=300
start_bootnode
start_producer a
start_producer b
start_node x $BIN/efsn
sleep 60
for r in a b x; do log "pins $r: $(js $r "[15130080,15130081,15130082,15130083].map(function(n){return eth.getBlock(n).hash.substr(0,12)}).join(' ')")"; done

done_ev() { [ -e $RUN/.ev-$1 ]; }
mark() { touch $RUN/.ev-$1; }
LAST_CHECKED=15130083
NEXT_CHECK=$((T0 + CHECK))
while [ $(date +%s) -lt $EV_END ] && [ ! -e $MNT/STOP ]; do
  now=$(date +%s)
  if ! done_ev join_j && [ $now -ge $EV_JOIN_J ]; then
    log "EVENT joiner j (launch snapshot, bootnode only)"; start_node j $BIN/efsn; mark join_j
  fi
  if ! done_ev kill_a && [ $now -ge $EV_KILL_A ]; then
    log "EVENT kill -9 producer A at $(status a)"; stop_node a KILL; mark kill_a; KILL_A_UP=$((now + A_DOWN))
  fi
  if done_ev kill_a && ! done_ev up_a && [ $now -ge ${KILL_A_UP:-0} ]; then
    start_producer a; A_BACK=$(date +%s); mark up_a
  fi
  if ! done_ev restart_b && [ $now -ge $EV_RESTART_B ]; then
    log "EVENT clean restart producer B"; stop_node b TERM; sleep $B_DOWN; start_producer b; B_BACK=$(date +%s); mark restart_b
  fi
  if ! done_ev part && [ $now -ge $EV_PART ]; then
    log "EVENT partition: producer A isolated for ${PART_LEN}s"; link a down; mark part; PART_HEAL=$((now + PART_LEN))
  fi
  if done_ev part && ! done_ev heal && [ $now -ge ${PART_HEAL:-0} ]; then
    log "partition end: a=$(status a) b=$(status b)"; link a up; HEALED=$(date +%s); mark heal
  fi
  if ! done_ev snap_k && [ $now -ge $EV_SNAP_K ]; then
    log "EVENT live snapshot of x -> joiner k"; stop_node x TERM
    mkdir -p $RUN/k && cp -r $RUN/x/efsn $RUN/k/efsn && rm -f $RUN/k/efsn/static-nodes.json $RUN/k/efsn/nodekey
    $BIN/bootnode -genkey $RUN/k/nodekey.key; chown -R rehearsal:rehearsal $RUN/k
    start_node x $BIN/efsn; start_node k $BIN/efsn; mark snap_k
  fi
  if ! done_ev rival && [ $now -ge $EV_RIVAL ]; then
    if [ $(js a "eth.blockNumber") -gt 15130200 ]; then
      log "EVENT rival node (pins only 15130080) joins: $(status a)"
      write_static r a b
      start_node r $BIN/efsn-rival; RIVAL_UP=$(date +%s); mark rival
    fi
  fi
  if done_ev rival && ! done_ev rival_pinned && [ $now -ge $((${RIVAL_UP:-0} + RIVAL_LEN)) ]; then
    log "rival phase 1 end: r=$(status r) a=$(status a) a@15130081=$(js a "eth.getBlock(15130081).hash")"
    log "check point refusals logged by a/b/x: $(grep -c 'check point failed' $RUN/a/node.log $RUN/b/node.log $RUN/x/node.log | tr '\n' ' ')"
    stop_node r TERM; start_node r $BIN/efsn; mark rival_pinned
    sleep 30; log "rival restarted on pinned build: r@15130081=$(js r "eth.getBlock(15130081) ? eth.getBlock(15130081).hash : 'none'") $(status r)"
  fi
  if [ $now -ge $NEXT_CHECK ]; then
    head=$(js a "eth.blockNumber"); to=$((head - 5))
    [ $to -gt $LAST_CHECKED ] && { log "hourly a: $(check_blocks a $((LAST_CHECKED + 1)) $to)"; LAST_CHECKED=$to; }
    log "free: $(df -h --output=avail / $MNT | tail -2 | tr -s ' \n' ' ') mem: $(free -m | awk '/Mem/ {print $7"MiB avail"}')"
    NEXT_CHECK=$((now + CHECK))
  fi
  status_all
  sleep $POLL
done

# ---------- final checks ----------
head=$(js a "eth.blockNumber"); to=$((head - 5))
{
  echo "T2 soak summary $(stamp) scale=$SCALE duration=$(( $(date +%s) - T0 ))s head(a)=$head"
  echo "pins@15130081 / 15130083 per node (expect $PIN81 / $PIN83):"
  for r in a b x j k r; do running $r && echo "  $r: $(js $r "eth.getBlock(15130081).hash + ' ' + eth.getBlock(15130083).hash")"; done
  echo "agreement hash@$to:"
  for r in a b x j k r; do running $r && echo "  $r: $(js $r "eth.getBlock($to) ? eth.getBlock($to).hash : 'missing'") head=$(js $r eth.blockNumber) peers=$(js $r net.peerCount)"; done
  echo "whole-run block check (a): $(check_blocks a 15130084 $to)"
  echo "A blocks since restart: $(miner_since a $A_ADDR ${A_BACK:-0})  B blocks since restart: $(miner_since a $B_ADDR ${B_BACK:-0})  both since heal: A=$(miner_since a $A_ADDR ${HEALED:-0}) B=$(miner_since a $B_ADDR ${HEALED:-0})"
  for r in a b; do addr=$A_ADDR; [ $r = b ] && addr=$B_ADDR
    echo "funds $r: liquid=$(js a "web3.fromWei(fsn.getBalance('0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff','$addr','latest'))") tickets=$(js a "fsn.totalNumberOfTicketsByAddress('$addr','latest')") nonce=$(js a "eth.getTransactionCount('$addr')")"
  done
  echo "log markers (multiple block mined / check point failed / check point mismatch / Fatal|panic / BAD BLOCK):"
  for r in a b x j k r; do [ -f $RUN/$r/node.log ] && echo "  $r: $(grep -c 'multiple block mined' $RUN/$r/node.log) / $(grep -c 'check point failed' $RUN/$r/node.log) / $(grep -c 'check point mismatch' $RUN/$r/node.log) / $(grep -cE 'Fatal|panic' $RUN/$r/node.log) / $(grep -c 'BAD BLOCK' $RUN/$r/node.log)"; done
} > $RUN/summary.txt
cat $RUN/summary.txt | tee -a $RUN/events.log
