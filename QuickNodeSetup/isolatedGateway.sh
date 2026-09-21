#!/bin/bash

isIsolatedGateway() {
    [ -f "$CONF_FILE" ] && [ "$(jq -r '.nodeType' "$CONF_FILE")" = "isolated-gateway" ]
}

installNodeService() {
    sudo install -m 644 "$SCRIPT_DIR/fusion.service" /etc/systemd/system/fusion.service
}

setupIsolatedGateway() {
    local repo image_id revision builder runtime config_tmp
    if [ "$EUID" -eq 0 ]; then
        echo "Run the node manager as your normal Ubuntu user; it invokes sudo when needed."
        return 1
    fi
    repo="$(cd "$SCRIPT_DIR/.." && pwd)" || return 1
    command -v git >/dev/null || { echo "Install git before building the gateway."; return 1; }
    revision="$(git -C "$repo" rev-parse HEAD)" || return 1
    if [ -n "$(git -C "$repo" status --porcelain --untracked-files=normal)" ]; then
        echo "Commit or set aside checkout changes before building a reproducible gateway."
        return 1
    fi
    if sudo docker container inspect fusion >/dev/null 2>&1; then
        if [ "$(sudo docker inspect -f '{{index .Config.Labels "io.fusion.mode"}}' fusion)" != "isolated-gateway" ]; then
            echo "An existing fusion container is not an isolated gateway. Stop and remove it through the menu first."
            return 1
        fi
        if [ "$(sudo docker inspect -f '{{.State.Running}}' fusion)" != "false" ]; then
            echo "Stop the gateway before running setup again."
            return 1
        fi
    fi
    echo "Build a historical mainnet gateway from commit $revision?"
    echo "Existing data will be preserved. The container will remain stopped until you start it."
    askToContinue "Continue? [y/n] " || return 1
    sudo docker pull golang:1.21.3-alpine || return 1
    sudo docker pull alpine:3.18 || return 1
    builder="$(sudo docker image inspect -f '{{index .RepoDigests 0}}' golang:1.21.3-alpine)" || return 1
    runtime="$(sudo docker image inspect -f '{{index .RepoDigests 0}}' alpine:3.18)" || return 1
    if [[ "$builder" != *@sha256:* || "$runtime" != *@sha256:* ]]; then
        echo "Could not resolve immutable base image references."
        return 1
    fi
    sudo docker build --file "$repo/Dockerfile.gateway-isolated" \
        --build-arg "BUILDER_IMAGE=$builder" --build-arg "RUNTIME_IMAGE=$runtime" \
        --label "org.opencontainers.image.revision=$revision" \
        --tag "fusion-local/gateway:$revision" "$repo" || return 1
    image_id="$(sudo docker image inspect -f '{{.Id}}' "fusion-local/gateway:$revision")" || return 1
    [[ "$image_id" = sha256:* ]] || return 1
    prepareIsolatedNetwork || return 1
    mkdir -p "$BASE_DIR/fusion-node/data/efsn/chaindata" || return 1
    if [ -f "$CONF_FILE" ]; then
        cp -p "$CONF_FILE" "$CONF_FILE.before-recovery-$(date +%s%N)" || return 1
    fi
    config_tmp="$(mktemp "$BASE_DIR/fusion-node/node.json.XXXXXX")" || return 1
    jq -n --arg image "$image_id" --arg revision "$revision" \
        --arg builder "$builder" --arg runtime "$runtime" \
        '{nodeType:"isolated-gateway", testnet:"false", mining:"false", autobt:"false", nodeName:"", image:$image, revision:$revision, builder:$builder, runtime:$runtime}' \
        > "$config_tmp" || return 1
    installNodeService || return 1
    sudo systemctl daemon-reload || return 1
    sudo systemctl disable fusion || return 1
    if [ "$(systemctl is-active fusion 2>/dev/null)" = "active" ]; then
        sudo systemctl stop fusion || return 1
    fi
    removeContainer || return 1
    sudo docker create --name fusion --pull never --restart no --stop-timeout 300 \
        --label io.fusion.mode=isolated-gateway \
        --network fusion-history --publish 127.0.0.1:9000:9000 \
        --mount "type=bind,source=$BASE_DIR/fusion-node/data/efsn/chaindata,target=/fusion-node/data/efsn/chaindata" \
        "$image_id" --datadir /fusion-node/data --syncmode full \
        --maxpeers 0 --nodiscover --bootnodes "" --nat none --port 0 \
        --http --http.addr 0.0.0.0 --http.port 9000 --http.api eth,net,web3,fsn \
        --http.vhosts localhost,127.0.0.1 || return 1
    mv "$config_tmp" "$CONF_FILE" || return 1
    echo "Gateway prepared and STOPPED. Restore and verify a working copy in:"
    echo "$BASE_DIR/fusion-node/data/efsn/chaindata"
    echo "Then select Start the node. The preserved original backup must remain elsewhere."
}

prepareIsolatedNetwork() {
    if ! sudo docker network inspect fusion-history >/dev/null 2>&1; then
        sudo docker network create --internal --driver bridge \
            --label io.fusion.mode=isolated-gateway fusion-history >/dev/null || return 1
    fi
    if [ "$(sudo docker network inspect -f '{{.Internal}}' fusion-history)" != "true" ]; then
        echo "fusion-history must be an internal Docker network."
        return 1
    fi
    if [ "$(sudo docker network inspect -f '{{.Driver}}' fusion-history)" != "bridge" ]; then
        echo "fusion-history must use the bridge driver."
        return 1
    fi
}

validateIsolatedGateway() {
    local chaindata="$BASE_DIR/fusion-node/data/efsn/chaindata"
    local manifest container_json
    if [ ! -s "$chaindata/CURRENT" ]; then
        echo "No restored database found at $chaindata. Copy and verify the backup before starting."
        return 1
    fi
    manifest="$(tr -d '\r\n' < "$chaindata/CURRENT")"
    if [[ ! "$manifest" =~ ^MANIFEST-[0-9]+$ ]] || [ ! -s "$chaindata/$manifest" ]; then
        echo "Restored database has no valid CURRENT/manifest pair."
        return 1
    fi
    prepareIsolatedNetwork || return 1
    container_json="$(sudo docker inspect fusion)" || return 1
    if ! jq -e --arg image "$(jq -r '.image' "$CONF_FILE")" \
        --arg source "$chaindata" '
        .[0] | .Config.Labels["io.fusion.mode"] == "isolated-gateway" and
        .Image == $image and
        .HostConfig.NetworkMode == "fusion-history" and
        (.NetworkSettings.Networks | keys) == ["fusion-history"] and
        .HostConfig.RestartPolicy.Name == "no" and
        .HostConfig.Privileged == false and
        .HostConfig.PortBindings == {"9000/tcp":[{"HostIp":"127.0.0.1","HostPort":"9000"}]} and
        (.Mounts | length) == 1 and
        .Mounts[0].Source == $source and
        .Mounts[0].Destination == "/fusion-node/data/efsn/chaindata"
        ' <<< "$container_json" >/dev/null; then
        echo "Container does not match the saved isolated gateway. Run isolated gateway setup again."
        return 1
    fi
}
