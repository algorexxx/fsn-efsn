#!/bin/bash
set -euo pipefail

TEST_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export TERM=xterm
export USER="${USER:-gateway-test}"
source "$TEST_DIR/fsnNode.sh"
source "$TEST_DIR/fusion-gateway.sh"

runTest() (
    local test_name="$1"
    BASE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/fusion-gateway-test.XXXXXX")"
    CONF_FILE="$BASE_DIR/fusion-node/node.json"
    CALLS="$BASE_DIR/calls"
    mkdir -p "$BASE_DIR/fusion-node/data/efsn/chaindata"
    printf 'preserved\n' > "$BASE_DIR/fusion-node/data/efsn/chaindata/sentinel"
    printf '{"nodeType":"isolated-gateway","image":"sha256:gateway"}\n' > "$CONF_FILE"
    : > "$CALLS"
    INTERNAL=true
    EXTRA_NETWORK=false
    FAIL_BUILD=false
    FAIL_STOP=false
    FAIL_PULL=false
    FAIL_RPC=false
    RPC_FAILURES=0
    UNIT_STATE=disabled
    FAIL_SOCKET=false
    PUBLISHED=false
    PORT_BINDINGS='{}'
    CONTAINER_EXISTS=false
    LABEL=isolated-gateway
    IMAGE=sha256:gateway
    RUNNING=false
    DEBUG_MODE=1

    sudo() { "$@"; }
    installIsolatedRpc() { printf 'rpc-install\n' >> "$CALLS"; }
    installGatewayBoot() { printf 'boot-install\n' >> "$CALLS"; }
    sleep() { :; }
    curl() {
        printf 'rpc-probe\n' >> "$CALLS"
        if [ "$FAIL_RPC" = true ] || [ "$(grep -c rpc-probe "$CALLS")" -le "$RPC_FAILURES" ]; then
            echo '{"error":{"code":-1}}'
        else
            echo '{"result":"0x7f93"}'
        fi
    }
    askToContinue() { return 0; }
    pauseScript() { return 0; }
    installNodeService() { printf 'service-install\n' >> "$CALLS"; }
    systemctl() {
        printf 'systemctl %s\n' "$*" >> "$CALLS"
        if [ "$*" = "start fusion-rpc.socket" ] && [ "$FAIL_SOCKET" = true ]; then return 1; fi
        if [ "${1:-}" = is-active ]; then echo inactive; return 3; fi
        if [ "${1:-}" = is-enabled ]; then echo "$UNIT_STATE"; [ "$UNIT_STATE" = enabled ]; return; fi
    }
    git() {
        if [[ "$*" = *rev-parse* ]]; then echo abc123; fi
        return 0
    }
    docker() {
        printf 'docker %s\n' "$*" >> "$CALLS"
        case "$1 $2" in
            'container inspect') [ "$CONTAINER_EXISTS" = true ]; return ;;
            'network inspect')
                case "$*" in
                    *Internal*) echo "$INTERNAL" ;;
                    *Driver*) echo bridge ;;
                esac
                return 0 ;;
            'image inspect')
                case "$*" in
                    *RepoDigests*) echo 'example/image@sha256:base' ;;
                    *) echo sha256:gateway ;;
                esac
                return 0 ;;
        esac
        case "$1" in
            inspect)
                if [ "$2" = '-f' ]; then
                    case "$3" in
                        *Labels*) echo "$LABEL" ;;
                        *Running*) echo "$RUNNING" ;;
                    esac
                else
                    jq -n --arg source "$BASE_DIR/fusion-node/data/efsn/chaindata" \
                        --arg image "$IMAGE" --arg label "$LABEL" --argjson extra "$EXTRA_NETWORK" --argjson ports "$PORT_BINDINGS" \
                        '[{Config:{Labels:{"io.fusion.mode":$label}},Image:$image,
                        HostConfig:{NetworkMode:"fusion-history",RestartPolicy:{Name:"no"},Privileged:false,
                        PortBindings:$ports},
                        NetworkSettings:{Networks:(if $extra then {"fusion-history":{},bridge:{}} else {"fusion-history":{}} end)},
                        Mounts:[{Source:$source,Destination:"/fusion-node/data/efsn/chaindata"}]}]'
                fi ;;
            port) if [ "$PUBLISHED" = true ]; then echo "127.0.0.1:9000"; fi ;;
            build) [ "$FAIL_BUILD" = false ] ;;
            pull) [ "$FAIL_PULL" = false ] ;;
            stop) [ "$FAIL_STOP" = false ] ;;
            create) printf '%s\n' "$@" > "$BASE_DIR/create-args" ;;
            *) return 0 ;;
        esac
    }
    restoreManifest() {
        printf 'MANIFEST-000001\n' > "$BASE_DIR/fusion-node/data/efsn/chaindata/CURRENT"
        printf 'fixture\n' > "$BASE_DIR/fusion-node/data/efsn/chaindata/MANIFEST-000001"
    }
    assertPreserved() {
        [ "$(cat "$BASE_DIR/fusion-node/data/efsn/chaindata/sentinel")" = preserved ]
    }
    "$test_name"
    assertPreserved
    printf 'PASS %s\n' "$test_name"
)

installPreservesExistingData() {
    if installNode; then return 1; fi
    [ ! -s "$CALLS" ]
}

initPreservesExistingData() {
    if initConfig; then return 1; fi
    [ ! -s "$CALLS" ]
}

startRejectsEmptyDatabase() {
    if startNode; then return 1; fi
    ! grep -q 'docker start' "$CALLS"
}

startRejectsManifestTraversal() {
    printf '../sentinel\n' > "$BASE_DIR/fusion-node/data/efsn/chaindata/CURRENT"
    if startNode; then return 1; fi
    ! grep -q 'docker start' "$CALLS"
}

startRejectsExternalNetwork() {
    restoreManifest
    INTERNAL=false
    if startNode; then return 1; fi
    ! grep -q 'docker start' "$CALLS"
}

startRejectsExtraNetwork() {
    restoreManifest
    EXTRA_NETWORK=true
    if startNode; then return 1; fi
    ! grep -q 'docker start' "$CALLS"
}

startRejectsChangedImage() {
    restoreManifest
    IMAGE=sha256:other
    if startNode; then return 1; fi
    ! grep -q 'docker start' "$CALLS"
}

startAcceptsRestoredIsolatedContainer() {
    restoreManifest
    startNode
    grep -q 'docker start fusion' "$CALLS"
}

buildFailurePreservesConfiguration() {
    local before
    before="$(cat "$CONF_FILE")"
    FAIL_BUILD=true
    if setupIsolatedGateway; then return 1; fi
    [ "$(cat "$CONF_FILE")" = "$before" ]
    ! grep -Eq 'docker (rm|create|start)' "$CALLS"
}

setupLeavesContainerStoppedAndPinned() {
    setupIsolatedGateway
    [ "$(jq -r '.image' "$CONF_FILE")" = sha256:gateway ]
    grep -qx -- '--pull' "$BASE_DIR/create-args"
    grep -qx -- 'never' "$BASE_DIR/create-args"
    ! grep -qx -- '--publish' "$BASE_DIR/create-args"
    grep -qx -- 'sha256:gateway' "$BASE_DIR/create-args"
    grep -qx -- '--nodiscover' "$BASE_DIR/create-args"
    grep -qx -- '--bootnodes' "$BASE_DIR/create-args"
    [ "$(grep -A 1 -x -- '--bootnodes' "$BASE_DIR/create-args" | tail -n 1)" = "" ]
    ! grep -Eq -- '--mine|--autobt|--unlock|--ethstats|40408|fsntx' "$BASE_DIR/create-args"
    ! grep -q 'docker start' "$CALLS"
    [ "$(find "$BASE_DIR/fusion-node" -name 'node.json.before-recovery-*' | wc -l)" -eq 1 ]
}

setupRejectsExistingMiner() {
    CONTAINER_EXISTS=true
    LABEL=miner
    if setupIsolatedGateway; then return 1; fi
    ! grep -Eq 'docker (build|rm|create|start)' "$CALLS"
}

stopFailurePreventsRemoval() {
    CONTAINER_EXISTS=true
    FAIL_STOP=true
    if removeContainer; then return 1; fi
    ! grep -q 'docker rm' "$CALLS"
}

uninstallPreservesConfigurationAndData() {
    CONTAINER_EXISTS=true
    deinstallNode
    [ -f "$CONF_FILE" ]
    grep -q 'docker rm fusion' "$CALLS"
}

updateDoesNotPullPublicImage() {
    if updateNode; then return 1; fi
    [ ! -s "$CALLS" ]
}

legacyUpdatePullFailurePreservesContainer() {
    printf '{"nodeType":"gateway","testnet":"false"}\n' > "$CONF_FILE"
    CONTAINER_EXISTS=true
    FAIL_PULL=true
    if updateNode; then return 1; fi
    grep -q 'docker pull fusionnetwork/gateway' "$CALLS"
    ! grep -Eq 'docker (stop|rm|create|start)' "$CALLS"
}

legacyLayoutRequiresManualMigration() {
    mkdir -p "$BASE_DIR/fusion-node/efsn"
    printf 'old-database\n' > "$BASE_DIR/fusion-node/efsn/sentinel"
    if createContainer; then return 1; fi
    [ "$(cat "$BASE_DIR/fusion-node/efsn/sentinel")" = old-database ]
    ! grep -q 'docker create' "$CALLS"
}

configureRpcPreservesRunningNode() {
    restoreManifest
    RUNNING=true
    configureIsolatedRpc
    grep -q 'rpc-install' "$CALLS"
    grep -q 'systemctl start fusion-rpc.socket' "$CALLS"
    ! grep -Eq 'docker (start|stop|rm|create|build)' "$CALLS"
}

configureRpcRejectsExternalNetwork() {
    restoreManifest
    RUNNING=true
    EXTRA_NETWORK=true
    if configureIsolatedRpc; then return 1; fi
    ! grep -q 'rpc-install' "$CALLS"
}

configureRpcRejectsPublishedPort() {
    restoreManifest
    RUNNING=true
    PUBLISHED=true
    if configureIsolatedRpc; then return 1; fi
    ! grep -q 'rpc-install' "$CALLS"
}

rpcProbeFailureClosesEndpoint() {
    FAIL_RPC=true
    if startIsolatedRpc; then return 1; fi
    [ "$(grep -c 'systemctl stop fusion-rpc.socket fusion-rpc.service' "$CALLS")" -eq 2 ]
    ! grep -q 'docker stop' "$CALLS"
}

rpcBindFailureIsReported() {
    FAIL_SOCKET=true
    if startIsolatedRpc; then return 1; fi
    ! grep -q 'rpc-probe' "$CALLS"
}

stopClosesRpcBeforeNode() {
    stopNode
    [ "$(grep -n 'systemctl stop fusion-rpc.socket' "$CALLS" | cut -d: -f1)" -lt "$(grep -n 'docker stop' "$CALLS" | cut -d: -f1)" ]
}

startAcceptsLegacyLoopbackBinding() {
    restoreManifest
    PORT_BINDINGS='{"9000/tcp":[{"HostIp":"127.0.0.1","HostPort":"9000"}]}'
    validateIsolatedGateway
}

startRejectsPublicBinding() {
    restoreManifest
    PORT_BINDINGS='{"9000/tcp":[{"HostIp":"0.0.0.0","HostPort":"9000"}]}'
    if startNode; then return 1; fi
    ! grep -q 'docker start' "$CALLS"
}

bootStartVerifiesRpcLikeManualStart() {
    restoreManifest
    RUNNING=true
    startGatewayAtBoot
    [ "$(grep -c 'docker start fusion' "$CALLS")" -eq 1 ]
    [ "$(grep -c 'systemctl start fusion-rpc.socket' "$CALLS")" -eq 1 ]
    ! grep -q 'docker stop' "$CALLS"
}

bootStartRefreshesRpcWhileNodeLoads() {
    restoreManifest
    RUNNING=true
    RPC_FAILURES=20
    startGatewayAtBoot
    [ "$(grep -c 'docker start fusion' "$CALLS")" -eq 1 ]
    [ "$(grep -c 'systemctl start fusion-rpc.socket' "$CALLS")" -eq 2 ]
    [ "$(grep -c 'rpc-probe' "$CALLS")" -eq 21 ]
    ! grep -q 'docker stop' "$CALLS"
}

bootStartGivesUpButLeavesNodeRunning() {
    restoreManifest
    RUNNING=true
    FAIL_RPC=true
    GATEWAY_RPC_ATTEMPTS=2
    if startGatewayAtBoot; then return 1; fi
    [ "$(grep -c 'systemctl start fusion-rpc.socket' "$CALLS")" -eq 3 ]
    ! grep -q 'docker stop' "$CALLS"
}

bootStartStopsNodeWhenTerminatedWhileLoading() {
    restoreManifest
    RUNNING=true
    FAIL_RPC=true
    sleep() { kill -TERM "$BASHPID"; }
    if (startGatewayAtBoot); then return 1; fi
    [ "$(grep -c 'systemctl start fusion-rpc.socket' "$CALLS")" -eq 1 ]
    [ "$(grep -n 'systemctl stop fusion-rpc.socket' "$CALLS" | tail -n 1 | cut -d: -f1)" -lt "$(grep -n 'docker stop' "$CALLS" | cut -d: -f1)" ]
}

bootStartStopsRefreshingWhenNodeExits() {
    restoreManifest
    FAIL_RPC=true
    if startGatewayAtBoot; then return 1; fi
    [ "$(grep -c 'systemctl start fusion-rpc.socket' "$CALLS")" -eq 1 ]
    ! grep -q 'docker stop' "$CALLS"
}

bootStartRejectsEmptyDatabase() {
    if startGatewayAtBoot; then return 1; fi
    ! grep -q 'docker start' "$CALLS"
}

bootStartRequiresIsolatedGateway() {
    printf '{"nodeType":"gateway","testnet":"false"}\n' > "$CONF_FILE"
    if startGatewayAtBoot; then return 1; fi
    [ ! -s "$CALLS" ]
}

bootEntryRejectsUnknownAction() {
    local status=0
    bash "$TEST_DIR/fusion-gateway.sh" restart > /dev/null || status=$?
    [ "$status" -eq 2 ]
}

autostartEnableInstallsAndStartsUnit() {
    restoreManifest
    changeGatewayAutostart
    [ "$(grep -n 'boot-install' "$CALLS" | cut -d: -f1)" -lt "$(grep -n 'systemctl enable' "$CALLS" | cut -d: -f1)" ]
    grep -qx "systemctl enable --now fusion-gateway@$USER.service" "$CALLS"
}

autostartRejectsInvalidGateway() {
    if changeGatewayAutostart; then return 1; fi
    ! grep -Eq 'boot-install|systemctl enable' "$CALLS"
}

autostartDisableKeepsNodeRunning() {
    UNIT_STATE=enabled
    changeGatewayAutostart
    grep -qx "systemctl disable fusion-gateway@$USER.service" "$CALLS"
    ! grep -Eq 'docker stop|systemctl stop' "$CALLS"
}

for test_name in installPreservesExistingData initPreservesExistingData \
    startRejectsEmptyDatabase startRejectsManifestTraversal startRejectsExternalNetwork \
    startRejectsExtraNetwork startRejectsChangedImage startAcceptsRestoredIsolatedContainer \
    buildFailurePreservesConfiguration setupLeavesContainerStoppedAndPinned \
    setupRejectsExistingMiner stopFailurePreventsRemoval uninstallPreservesConfigurationAndData \
    updateDoesNotPullPublicImage legacyUpdatePullFailurePreservesContainer \
    legacyLayoutRequiresManualMigration configureRpcPreservesRunningNode \
    configureRpcRejectsExternalNetwork configureRpcRejectsPublishedPort \
    rpcProbeFailureClosesEndpoint rpcBindFailureIsReported stopClosesRpcBeforeNode \
    startAcceptsLegacyLoopbackBinding startRejectsPublicBinding \
    bootStartVerifiesRpcLikeManualStart bootStartRefreshesRpcWhileNodeLoads \
    bootStartGivesUpButLeavesNodeRunning bootStartStopsNodeWhenTerminatedWhileLoading \
    bootStartStopsRefreshingWhenNodeExits \
    bootStartRejectsEmptyDatabase bootStartRequiresIsolatedGateway bootEntryRejectsUnknownAction \
    autostartEnableInstallsAndStartsUnit autostartRejectsInvalidGateway \
    autostartDisableKeepsNodeRunning; do
    runTest "$test_name"
done
