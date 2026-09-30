#!/bin/bash

GATEWAY_RPC_ATTEMPTS=40
GATEWAY_RPC_INTERVAL=30

startGatewayAtBoot() {
    trap 'stopNode; exit 1' TERM
    if ! isIsolatedGateway; then
        echo "No isolated historical gateway is configured in $CONF_FILE."
        return 1
    fi
    startNode && return 0
    local attempt
    for ((attempt = 1; attempt <= GATEWAY_RPC_ATTEMPTS; attempt++)); do
        isGatewayRunning || return 1
        echo "Refreshing private RPC while the node loads (attempt $attempt of $GATEWAY_RPC_ATTEMPTS)"
        sleep "$GATEWAY_RPC_INTERVAL"
        startIsolatedRpc && return 0
    done
    return 1
}

if [[ "${BASH_SOURCE[0]}" = "$0" ]]; then
    action="${1:-}"
    set --
    source "$(dirname -- "$(readlink -f -- "${BASH_SOURCE[0]}")")/fsnNode.sh" || exit 1
    case "$action" in
        start) startGatewayAtBoot ;;
        stop) stopNode ;;
        *) echo "Usage: $0 start|stop"; exit 2 ;;
    esac
fi
