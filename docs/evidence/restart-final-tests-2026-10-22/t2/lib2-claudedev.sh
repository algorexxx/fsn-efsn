# Shared helpers for the T2 soak (per-node network namespaces). Source with RUN, BIN, T2, RECOVERY set.
# Roles: a = producer A (public key 2), b = producer B (public key 1), x = explorer-like full node,
# j = joiner from the launch snapshot, k = joiner from a live snapshot of x, r = rival pre-restart chain.
A_ADDR=0x2B5AD5c4795c026514f8317c7a215E218DcCD6cF
B_ADDR=0x7E5F4552091A69125d5DfCb7b8C2659029395Bdf
PIN81=0xd2cfe5bb26551cda5c04ced4598a72944daa12da6962f256c376ca5bfa6b9586
PIN83=0x1d68db766979da529fcaf9a8f8f217bcf08f6e3705eb348febd2d28ca83a78db
PORT=30411
BN_PORT=30400
NET=10.77.0
declare -A HOST=([bn]=10 [a]=11 [b]=12 [x]=13 [j]=14 [r]=15 [k]=16)
UIDGID=$(id -u peter)
stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }
log() { echo "$(stamp) $*" | tee -a $RUN/events.log; }
ip_of() { echo $NET.${HOST[$1]}; }
in_ns() { local r=$1; shift; ip netns exec t2-$r setpriv --reuid=$UIDGID --regid=$UIDGID --init-groups env HOME=/home/peter "$@"; }
bg_in_ns() { local r=$1; shift; exec ip netns exec t2-$r setpriv --reuid=$UIDGID --regid=$UIDGID --init-groups env HOME=/home/peter "$@"; }

net_up() {
  ip netns add t2hub
  ip -n t2hub link add br0 type bridge
  ip -n t2hub link set br0 up
  for r in bn a b x j k r; do
    ip netns add t2-$r
    ip -n t2-$r link set lo up
    ip link add v-$r netns t2hub type veth peer name eth0 netns t2-$r
    ip -n t2hub link set v-$r master br0
    ip -n t2hub link set v-$r up
    ip -n t2-$r addr add $(ip_of $r)/24 dev eth0
    ip -n t2-$r link set eth0 up
  done
  log "network up: $(ip netns list | tr '\n' ' ')"
}

net_down() {
  for r in bn a b x j k r; do ip netns del t2-$r 2>/dev/null; done
  ip netns del t2hub 2>/dev/null
  log "network removed"
}

link() { ip -n t2hub link set v-$1 $2; log "link $1 $2"; }

js() { $BIN/efsn attach --exec "$2" $RUN/$1/efsn.ipc 2>/dev/null; }

# setup_node ROLE SEEDROLE KEYSCALAR(0=none)
setup_node() {
  local r=$1 seed=$2 key=$3 d=$RUN/$1
  mkdir -p $d
  cp -r $SEEDS/$seed/efsn $d/efsn
  $BIN/bootnode -genkey $d/nodekey.key
  if [ "$key" != 0 ]; then
    printf '%064x\n' $key > $d/key.hex
    echo "public-t2-password" > $d/password.txt
    $BIN/efsn --datadir $d --lightkdf --password $d/password.txt account import $d/key.hex > $d/account-import.log 2>&1
    rm $d/key.hex
  fi
  chown -R peter:peter $d
}

# 'efsn import' cannot be used: importChain builds a full node (which opens chaindata) and then opens
# chaindata again (LevelDB lock). Import through admin.importChain on an offline, non-mining node.
import_recovery() {
  local r=$1 d=$RUN/$1
  bg_in_ns $r $BIN/efsn --datadir $d --nodiscover --maxpeers 0 --nat none --port $PORT --cache 128 \
    --ipcpath $d/efsn.ipc --verbosity 3 > $d/import.log 2>&1 &
  local p=$!
  for i in $(seq 60); do [ -S $d/efsn.ipc ] && break; sleep 1; done
  local res=$(js $r "admin.importChain('$RECOVERY')")
  local head=$(js $r "eth.blockNumber + ' ' + eth.getBlock('latest').hash" | tr -d '"')
  kill -TERM $p; wait $p 2>/dev/null
  log "recovery import $r: importChain=$res head=$head"
  [ "$head" = "15130083 $PIN83" ]
}

enode_of() { echo "enode://$($BIN/bootnode -nodekey $RUN/$1/nodekey.key -writeaddress)@$(ip_of $1):$PORT"; }

write_static() { # ROLE PEER...
  local r=$1; shift
  local list=""
  for p in "$@"; do list="$list\"$(enode_of $p)\","; done
  echo "[${list%,}]" > $RUN/$r/efsn/static-nodes.json
  chown peter:peter $RUN/$r/efsn/static-nodes.json
}

start_bootnode() {
  bg_in_ns bn $BIN/bootnode -nodekey $RUN/bn.key -addr $(ip_of bn):$BN_PORT -nat extip:$(ip_of bn) -netrestrict $NET.0/24 -verbosity 4 >> $RUN/bootnode.log 2>&1 &
  echo $! > $RUN/bn.pid
  log "bootnode pid $(cat $RUN/bn.pid) $BOOTNODES"
}

# start_node ROLE BINARY EXTRA-FLAGS...
start_node() {
  local r=$1 bin=$2; shift 2
  local d=$RUN/$r
  bg_in_ns $r $bin --datadir $d --identity t2-$r --port $PORT --nat extip:$(ip_of $r) --netrestrict $NET.0/24 \
    --nodekey $d/nodekey.key --bootnodes "$BOOTNODES" --maxpeers 10 --syncmode full --cache 128 \
    --ipcpath $d/efsn.ipc --verbosity 3 "$@" >> $d/node.log 2>&1 &
  echo $! > $d/pid
  log "started $r pid $(cat $d/pid) $(basename $bin) $*"
}

start_producer() { # a|b
  local r=$1 addr=$A_ADDR
  [ $r = b ] && addr=$B_ADDR
  start_node $r $BIN/efsn --unlock $addr --password $RUN/$r/password.txt --mine --miner.etherbase $addr --autobt
}

stop_node() { # ROLE [SIGNAL]
  local r=$1 sig=${2:-TERM} d=$RUN/$1
  [ -f $d/pid ] || return 0
  local p=$(cat $d/pid)
  kill -$sig $p 2>/dev/null
  for i in $(seq 90); do kill -0 $p 2>/dev/null || break; sleep 1; done
  kill -0 $p 2>/dev/null && { kill -KILL $p; log "$r did not stop in 90s, killed"; }
  rm -f $d/pid $d/efsn.ipc
  log "stopped $r ($sig)"
}

running() { [ -f $RUN/$1/pid ] && kill -0 $(cat $RUN/$1/pid) 2>/dev/null; }

status() { # ROLE -> "number hash peers ticketsA ticketsB miner"
  js $1 "var b=eth.getBlock('latest'); [b.number, b.hash.substr(0,18), net.peerCount, fsn.totalNumberOfTicketsByAddress('$A_ADDR','latest'), fsn.totalNumberOfTicketsByAddress('$B_ADDR','latest'), b.miner.substr(0,10)].join(' ')"
}

status_all() {
  local line=""
  for r in a b x j k r; do running $r && line="$line | $r: $(status $r)"; done
  log "status$line"
}

check_blocks() { # ROLE FROM TO
  js $1 "var FROM=$2, TO=$3; loadScript('$T2/check-blocks.js')" | head -1
}

# miner_since ROLE ADDR UNIXTIME -> number of canonical blocks by ADDR with timestamp >= UNIXTIME
miner_since() {
  js $1 "var c=0; for (var n=eth.blockNumber; n>15130083; n--) { var b=eth.getBlock(n); if (b.timestamp < $3) break; if (b.miner.toLowerCase()=='$2'.toLowerCase()) c++; } c"
}
