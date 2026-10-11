#!/bin/bash

resolveIsolatedRpcAddress() {
    local container address
    container=$(docker inspect fusion) || return 1
    address=$(jq -er '
        .[0] | select(.State.Running == true) |
        select(.Config.Labels["io.fusion.mode"] == "isolated-gateway") |
        select((.NetworkSettings.Networks | keys) == ["fusion-history"]) |
        .NetworkSettings.Networks["fusion-history"].IPAddress |
        select(test("^([0-9]{1,3}\\.){3}[0-9]{1,3}$"))
    ' <<< "$container") || return 1
    [ "$(docker network inspect -f '{{.Internal}}' fusion-history)" = true ] || return 1
    printf '%s\n' "$address"
}

resolveIsolatedRpcTarget() {
    local port="${1:-9000}" address
    case "$port" in 9000|9001) ;; *) return 1 ;; esac
    address=$(resolveIsolatedRpcAddress) || return 1
    printf '%s:%s\n' "$address" "$port"
}

if [[ "${BASH_SOURCE[0]}" = "$0" ]]; then
    set -euo pipefail
    export PATH=/usr/sbin:/usr/bin:/sbin:/bin
    target=$(resolveIsolatedRpcTarget "${1:-9000}")
    exec /usr/lib/systemd/systemd-socket-proxyd "$target"
fi
