function isObject(value) {
    return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function projectNodes(nodes, maximum) {
    if (!Array.isArray(nodes) || nodes.length > maximum) {
        throw new Error('Invalid node snapshot');
    }
    const identities = new Set();
    return nodes.map(node => {
        if (!isObject(node) || typeof node.id !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$/.test(node.id) || identities.has(node.id) || !isObject(node.info) || !isObject(node.stats) || !isObject(node.stats.block) || !Array.isArray(node.history) || !(node.geo === null || isObject(node.geo))) {
            throw new Error('Invalid node snapshot');
        }
        identities.add(node.id);
        return { id: node.id, info: node.info, stats: node.stats, history: node.history, geo: node.geo };
    });
}

function startSnapshotCollection(config, dependencies) {
    let stopped = false;
    let socket = null;
    let timer = null;
    let pendingWrite = null;
    let awaitingSnapshot = false;
    let nodes = null;
    let observedAt = null;

    function clearTimer() {
        if (timer !== null) {
            dependencies.clearTimeout(timer);
            timer = null;
        }
    }

    function schedule(action, delay) {
        clearTimer();
        if (!stopped) {
            timer = dependencies.setTimeout(() => { timer = null; action(); }, delay);
        }
    }

    function disconnect(connection) {
        if (socket !== connection) {
            return;
        }
        socket = null;
        awaitingSnapshot = false;
        nodes = null;
        clearTimer();
        try {
            connection.close();
        } catch (_) {
            dependencies.onError('Collector socket close failed');
        }
        if (pendingWrite === null) {
            schedule(connectCollector, config.intervalMs);
        }
    }

    function expireConnection(connection) {
        dependencies.onError('Collector snapshot deadline exceeded');
        disconnect(connection);
    }

    function requestSnapshot(connection) {
        if (stopped || socket !== connection) {
            return;
        }
        nodes = null;
        awaitingSnapshot = true;
        schedule(() => expireConnection(connection), config.timeoutMs);
        try {
            connection.send(JSON.stringify({ emit: ['ready', {}] }));
        } catch (_) {
            dependencies.onError('Collector snapshot request failed');
            disconnect(connection);
        }
    }

    function saveSnapshot(connection, charts) {
        const payload = { nodes, charts };
        const receivedAt = observedAt;
        awaitingSnapshot = false;
        nodes = null;
        clearTimer();
        pendingWrite = Promise.resolve().then(() => dependencies.saveSnapshot(payload, receivedAt))
            .catch(() => {
                dependencies.onError('Dashboard snapshot write failed');
                disconnect(connection);
            }).finally(() => {
                pendingWrite = null;
                schedule(socket === connection ? () => requestSnapshot(connection) : connectCollector, config.intervalMs);
            });
    }

    function receiveMessage(connection, data) {
        if (stopped || socket !== connection) {
            return;
        }
        try {
            if (typeof data !== 'string' || Buffer.byteLength(data, 'utf8') > config.maxBytes) {
                throw new Error('Invalid collector message');
            }
            const message = JSON.parse(data);
            if (typeof message === 'string' && message.startsWith('primus::ping::')) {
                connection.send(JSON.stringify(message.replace('primus::ping::', 'primus::pong::')));
                return;
            }
            if (!awaitingSnapshot || !isObject(message)) {
                return;
            }
            if (Array.isArray(message.emit) && message.emit[0] === 'init') {
                if (nodes !== null || !isObject(message.emit[1])) {
                    throw new Error('Invalid collector snapshot');
                }
                nodes = projectNodes(message.emit[1].nodes, config.maxNodes);
                observedAt = dependencies.now();
                return;
            }
            if (message.action === 'charts' && nodes !== null) {
                if (!isObject(message.data)) {
                    throw new Error('Invalid collector charts');
                }
                saveSnapshot(connection, message.data);
            }
        } catch (_) {
            dependencies.onError('Collector snapshot rejected');
            disconnect(connection);
        }
    }

    function connectCollector() {
        if (stopped) {
            return;
        }
        try {
            const connection = dependencies.connect(config.url, config.maxBytes);
            socket = connection;
            connection.onopen = () => requestSnapshot(connection);
            connection.onmessage = event => receiveMessage(connection, event.data);
            connection.onclose = () => disconnect(connection);
            connection.onerror = () => disconnect(connection);
            schedule(() => expireConnection(connection), config.timeoutMs);
        } catch (_) {
            dependencies.onError('Collector connection failed');
            schedule(connectCollector, config.intervalMs);
        }
    }

    connectCollector();
    return {
        stop() {
            stopped = true;
            clearTimer();
            if (socket !== null) {
                disconnect(socket);
            }
            return pendingWrite || Promise.resolve();
        },
    };
}

module.exports = startSnapshotCollection;
