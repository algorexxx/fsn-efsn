# T2 crash test on claudedev: producer A is killed with kill -9 after it has sealed blocks whose state is
# still only in memory, and restarted a minute later. In the soak this brought A back on a stale head, where
# it sealed a second block on a parent it had already sealed on and was reported for it. Pass: A refuses to
# seal until it has synced, nobody logs "multiple block mined", and A follows the network head again.
# Run as root when no other T2 test is running, e.g.:
#   sudo systemd-run --unit=t2-crash-restart --setenv=T2_BIN=/home/peter/t2/bin-fixed bash /home/peter/t2/t2-crash-restart-claudedev.sh
set -uo pipefail
T2=/home/peter/t2
BIN=${T2_BIN:-/home/peter/t2/bin}
SEEDS=$T2/work/seeds
IMG=/var/lib/t2-rehearsal/t2.ext4
MNT=/mnt/t2
RUN_FOR=${T2_RUN_FOR:-900}
DOWN=60
WATCH=300

[ "$(id -u)" = 0 ] || { echo "run as root"; exit 1; }
for u in t2-soak t2-rival-early; do systemctl is-active -q $u && { echo "refusing: $u running"; exit 1; }; done
for s in a b x; do [ -f $SEEDS/$s/efsn/handover.json ] || { echo "missing seed $s"; exit 1; }; done
ip netns list | grep -q '^t2' && { echo "refusing: t2 namespaces already exist"; exit 1; }
mountpoint -q $MNT && { echo "refusing: $MNT already mounted"; exit 1; }

LOOP=$(losetup --find --show $IMG)
mkdir -p $MNT
mount $LOOP $MNT || { losetup -d $LOOP; exit 1; }
RUN=$MNT/crash-restart-$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p $RUN
chown peter:peter $RUN
RECOVERY=$RUN/recovery.rlp
cp $T2/work/recovery.rlp $RECOVERY
. $T2/lib2-claudedev.sh

cleanup() {
  set +e
  log "cleanup"
  for r in x b a; do stop_node $r TERM; done
  [ -f $RUN/bn.pid ] && kill $(cat $RUN/bn.pid) 2>/dev/null
  sleep 2
  net_down
  sync
  cp $RUN/events.log $T2/work/crash-restart-events.log 2>/dev/null
  umount $MNT && losetup -d $LOOP && echo "$(stamp) image unmounted and detached"
}
trap cleanup EXIT
trap 'log "signal received"; exit 1' INT TERM

head_of() { js $1 eth.blockNumber | tr -d '"'; }
result() { if [ "$2" = 1 ]; then log "PASS $1"; else log "FAIL $1"; fi; }

log "T2 crash-restart start run=$RUN efsn=$(sha256sum $BIN/efsn | cut -c1-16) run_for=${RUN_FOR}s"
net_up
setup_node a a 2; setup_node b b 1; setup_node x x 0
for r in a b x; do import_recovery $r || { log "FAIL recovery import $r"; exit 1; }; done
$BIN/bootnode -genkey $RUN/bn.key
BOOTNODES="enode://$($BIN/bootnode -nodekey $RUN/bn.key -writeaddress)@$(ip_of bn):$BN_PORT"
write_static a b x
write_static b a x
write_static x a b
chown -R peter:peter $RUN
start_bootnode
start_producer a
start_producer b
start_node x $BIN/efsn
END=$(( $(date +%s) + RUN_FOR ))
while [ $(date +%s) -lt $END ]; do status_all; sleep 60; done

A_SEALED=$(miner_since x $A_ADDR 0)
KILLED_AT=$(head_of a)
log "EVENT kill -9 producer A at head $KILLED_AT after sealing $A_SEALED blocks: $(status a)"
stop_node a KILL
sleep $DOWN
start_producer a
sleep 20
RESTART_HEAD=$(grep 'Loaded most recent local full block' $RUN/a/node.log | tail -1 | grep -o 'number=[0-9,]*' | tr -d 'number=,')
log "A restarted on head ${RESTART_HEAD:-unknown} (it was at $KILLED_AT)"
END=$(( $(date +%s) + WATCH ))
while [ $(date +%s) -lt $END ]; do status_all; sleep 30; done

NET_HEAD=$(head_of x); A_HEAD=$(head_of a)
REFUSED=$(grep -c 'refusing to seal' $RUN/a/node.log)
DOUBLE=$(grep -c 'multiple block mined' $RUN/a/node.log $RUN/b/node.log $RUN/x/node.log | awk -F: '{s+=$2} END {print s}')
BUY_WARN=$(grep -c 'Automatic ticket purchase failed' $RUN/a/node.log)
log "end: x=$(status x) a=$(status a) refused seals on a=$REFUSED multiple-block lines=$DOUBLE purchase-failure warnings on a=$BUY_WARN"
grep -h -E 'refusing to seal|multiple block mined|Automatic ticket purchase failed' $RUN/a/node.log | head -5 | tee -a $RUN/events.log
result "A restarted on an older head than it had reached (${RESTART_HEAD:-unknown} < $KILLED_AT)" $([[ ${RESTART_HEAD:-x} =~ ^[0-9]+$ ]] && [ $RESTART_HEAD -lt $KILLED_AT ] && echo 1 || echo 0)
result "no node logged a second block by the same miner on one parent ($DOUBLE)" $([ "$DOUBLE" = 0 ] && echo 1 || echo 0)
result "A refused to seal below its own last block before syncing ($REFUSED)" $([ $REFUSED -gt 0 ] && echo 1 || echo 0)
result "A follows the network head again (a=$A_HEAD x=$NET_HEAD)" $([[ $A_HEAD =~ ^[0-9]+$ && $NET_HEAD =~ ^[0-9]+$ ]] && [ $A_HEAD -ge $((NET_HEAD - 2)) ] && echo 1 || echo 0)
