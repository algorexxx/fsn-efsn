#!/bin/bash
set -euo pipefail
TEST_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$TEST_DIR/fusion-rpc-proxy.sh"

running=true
extra=false
internal=true
mode=isolated-gateway
ip=172.18.0.2

docker() {
    if [ "$1" = inspect ]; then
        jq -n --argjson running "$running" --argjson extra "$extra" --arg mode "$mode" --arg ip "$ip" \
            '[{State:{Running:$running},Config:{Labels:{"io.fusion.mode":$mode}},
            NetworkSettings:{Networks:({"fusion-history":{IPAddress:$ip}} +
            (if $extra then {bridge:{}} else {} end))}}]'
    else
        printf '%s\n' "$internal"
    fi
}

[ "$(resolveIsolatedRpcAddress)" = 172.18.0.2 ]
ip=172.18.0.9
[ "$(resolveIsolatedRpcAddress)" = 172.18.0.9 ]
echo 'PASS proxy resolves changed container address'
running=false
if resolveIsolatedRpcAddress; then exit 1; fi
running=true
echo 'PASS proxy rejects stopped node'
extra=true
if resolveIsolatedRpcAddress; then exit 1; fi
extra=false
echo 'PASS proxy rejects extra network'
internal=false
if resolveIsolatedRpcAddress; then exit 1; fi
internal=true
echo 'PASS proxy rejects non-internal network'
mode=miner
if resolveIsolatedRpcAddress; then exit 1; fi
mode=isolated-gateway
echo 'PASS proxy rejects other node mode'
ip=''
if resolveIsolatedRpcAddress; then exit 1; fi
echo 'PASS proxy rejects missing address'
