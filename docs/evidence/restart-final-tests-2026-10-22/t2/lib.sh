# Shared helpers for the T2 smoke and soak. Source with RUN, BIN, T2 set.
A_ADDR=0x2B5AD5c4795c026514f8317c7a215E218DcCD6cF   # public test key 2 (producer A, donation funding)
B_ADDR=0x7E5F4552091A69125d5DfCb7b8C2659029395Bdf   # public test key 1 (producer B, backup funding)
declare -A PORT=([a]=30411 [b]=30412 [x]=30413 [j]=30414 [r]=30415)
BN_PORT=30400
stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }
log() { echo "$(stamp) $*" | tee -a $RUN/events.log; }

# setup_node ROLE SEEDDIR KEYSCALAR(0=none) IMPORT(1/0)
setup_node() {
  local r=$1 seed=$2 key=$3 imp=$4 d=$RUN/$1
  mkdir -p $d
  cp -r $seed/efsn $d/efsn
  $BIN/bootnode -genkey $d/nodekey.key
  if [ "$key" != 0 ]; then
    printf '%064x\n' $key > $d/key.hex
    echo "public-t2-password" > $d/password.txt
    $BIN/efsn --datadir $d --lightkdf --password $d/password.txt account import $d/key.hex > $d/account-import.log 2>&1
    rm $d/key.hex
  fi
  if [ "$imp" = 1 ]; then import_recovery $r || return 1; fi
}

# 'efsn import' cannot be used: since v5.0.3 importChain builds a full node (which opens chaindata)
# and then opens chaindata again (LevelDB lock: "resource temporarily unavailable").
# Import instead through admin.importChain on a node started offline, without mining.
import_recovery() {
  local r=$1 d=$RUN/$1
  $NETEXEC $BIN/efsn --datadir $d --nodiscover --maxpeers 0 --nat none --port ${PORT[$r]} --cache 128     --ipcpath $IPCDIR/$r.ipc --verbosity 3 > $d/import.log 2>&1 &
  local p=$!
  for i in $(seq 60); do [ -S $IPCDIR/$r.ipc ] && break; sleep 1; done
  local res=$(js $r "admin.importChain('$RECOVERY')")
  local head=$(js $r "eth.blockNumber + ' ' + eth.getBlock('latest').hash" | tr -d '"')
  kill -TERM $p; wait $p 2>/dev/null
  log "recovery import $r: importChain=$res head=$head"
  [ "$head" = "15130083 0x1d68db766979da529fcaf9a8f8f217bcf08f6e3705eb348febd2d28ca83a78db" ]
}

enode_of() { echo "enode://$($BIN/bootnode -nodekey $RUN/$1/nodekey.key -writeaddress)@127.0.0.1:${PORT[$1]}"; }

write_static() { # ROLE PEER...
  local r=$1; shift
  local list=""
  for p in "$@"; do list="$list\"$(enode_of $p)\","; done
  echo "[${list%,}]" > $RUN/$r/efsn/static-nodes.json
}

# start_node ROLE BINARY EXTRA-FLAGS...  (NETEXEC may prefix a namespace wrapper)
start_node() {
  local r=$1 bin=$2; shift 2
  local d=$RUN/$r
  $NETEXEC $bin --datadir $d --identity t2-$r --port ${PORT[$r]} --nat none --netrestrict 127.0.0.0/8 \
    --nodekey $d/nodekey.key --bootnodes "$BOOTNODES" --maxpeers 10 --syncmode full --cache 128 \
    --ipcpath $IPCDIR/$r.ipc --verbosity 3 "$@" >> $d/node.log 2>&1 &
  echo $! > $d/pid
  log "started $r pid $(cat $d/pid) $*"
}

stop_node() { # ROLE [SIGNAL]
  local r=$1 sig=${2:-TERM} d=$RUN/$1
  [ -f $d/pid ] || return 0
  local p=$(cat $d/pid)
  kill -$sig $p 2>/dev/null || true
  for i in $(seq 60); do kill -0 $p 2>/dev/null || break; sleep 1; done
  kill -0 $p 2>/dev/null && { kill -KILL $p; log "$r did not stop in 60s, killed"; }
  rm -f $d/pid
  log "stopped $r ($sig)"
}

js() { # ROLE EXPR
  $BIN/efsn attach --exec "$2" $IPCDIR/$1.ipc 2>/dev/null
}

status() { # ROLE -> "number hash peers tickets(A) tickets(B)"
  js $1 "var b=eth.getBlock('latest'); [b.number, b.hash.substr(0,18), net.peerCount, fsn.totalNumberOfTicketsByAddress('$A_ADDR','latest'), fsn.totalNumberOfTicketsByAddress('$B_ADDR','latest'), b.miner.substr(0,10)].join(' ')"
}
