# User-level T2 smoke (no root): A+B producers, bootnode, joiner, ~25 min, on C: scratch.
# Isolation: host network namespace of the WSL VM (NAT mode), every node --netrestrict 127.0.0.0/8 --nat none,
# explicit loopback bootnode, IPC only. (The named netns + W: image path needs root; see t2-soak.sh.)
set -uo pipefail
. "$(dirname "$0")/../env.sh"
T2=$SP/t2
BIN=/home/rehearsal/t2/bin
RUN=$T2/work/smoke-$(date -u +%Y%m%dT%H%M%SZ)
NETEXEC=""
RECOVERY=$T2/work/recovery.rlp
IPCDIR=/home/rehearsal/t2/ipc; mkdir -p $IPCDIR
SMOKE_MIN=${SMOKE_MIN:-25}
mkdir -p $RUN
. $T2/lib.sh
cleanup() { for r in j b a; do stop_node $r TERM; done; [ -f $RUN/bn.pid ] && kill $(cat $RUN/bn.pid) 2>/dev/null; log "smoke cleanup done"; }
trap cleanup EXIT
log "smoke start RUN=$RUN efsn=$(sha256sum $BIN/efsn | cut -c1-16) recovery=$(sha256sum $T2/work/recovery.rlp | cut -c1-16)"
setup_node a $T2/work/seeds/a 2 1 || exit 1
setup_node b $T2/work/seeds/b 1 1 || exit 1
setup_node j $T2/work/seeds/j 0 1 || exit 1

$BIN/bootnode -genkey $RUN/bn.key
BOOTNODES="enode://$($BIN/bootnode -nodekey $RUN/bn.key -writeaddress)@127.0.0.1:$BN_PORT"
$BIN/bootnode -nodekey $RUN/bn.key -addr 127.0.0.1:$BN_PORT -nat none -netrestrict 127.0.0.0/8 -verbosity 4 > $RUN/bootnode.log 2>&1 &
echo $! > $RUN/bn.pid
log "bootnode $BOOTNODES"
write_static a b
write_static b a
start_node a $BIN/efsn --unlock $A_ADDR --password $RUN/a/password.txt --mine --miner.etherbase $A_ADDR --autobt
start_node b $BIN/efsn --unlock $B_ADDR --password $RUN/b/password.txt --mine --miner.etherbase $B_ADDR --autobt
sleep 45
for r in a b; do log "pins $r: $(js $r "[15130080,15130081,15130082,15130083].map(function(n){return n+'='+eth.getBlock(n).hash.substr(0,12)}).join(' ')")"; done
START=$(date +%s)
JOINED=0
while [ $(( $(date +%s) - START )) -lt $(( SMOKE_MIN * 60 )) ]; do
  if [ $JOINED = 0 ] && [ $(( $(date +%s) - START )) -ge 360 ]; then
    start_node j $BIN/efsn
    JOINED=1
  fi
  line=""
  for r in a b j; do [ -f $RUN/$r/pid ] && line="$line | $r: $(status $r)"; done
  log "status$line"
  sleep 60
done
HEAD=$(js a "eth.blockNumber")
TO=$((HEAD - 3))
log "final A check: $(js a "var FROM=15130084, TO=$TO; loadScript('$T2/check-blocks.js')" | head -1)"
for r in a b j; do log "hash@$TO $r: $(js $r "eth.getBlock($TO).hash") peers=$(js $r "net.peerCount")"; done
for r in a b; do log "funds $r: $(js $r "var x=(\"$r\"==\"a\")?\"$A_ADDR\":\"$B_ADDR\"; [web3.fromWei(fsn.getBalance('0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff', x, 'latest')), fsn.totalNumberOfTicketsByAddress(x,'latest'), eth.getTransactionCount(x), txpool.status.pending].join(' ')")"; done
grep -h -c "multiple block mined" $RUN/*/node.log | paste -sd' ' | sed 's/^/multiple-mined counts: /' | while read l; do log "$l"; done
grep -h -iE "check point failed|Fatal|panic|BAD BLOCK" $RUN/*/node.log | head -5 | while read l; do log "WARN: $l"; done
log "smoke done"
