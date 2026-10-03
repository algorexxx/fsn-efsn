const prepareSnapshot = require('./snapshot-view');

function startSnapshotPolling(config, dependencies) {
    let stopped = false;
    let request = null;
    let pollTimer;
    let deadlineTimer;
    let expiryTimer;

    function clearSnapshot() {
        if (stopped) {
            return;
        }
        dependencies.clearTimeout(expiryTimer);
        dependencies.onUnavailable();
    }

    function finishRequest(current) {
        if (stopped || request !== current) {
            return false;
        }
        request = null;
        dependencies.clearTimeout(deadlineTimer);
        pollTimer = dependencies.setTimeout(poll, config.intervalMs);
        return true;
    }

    function poll() {
        if (stopped || request !== null) {
            return;
        }
        const startedAt = dependencies.now();
        let current;
        try {
            current = dependencies.request();
        } catch (_) {
            clearSnapshot();
            pollTimer = dependencies.setTimeout(poll, config.intervalMs);
            return;
        }
        request = current;
        deadlineTimer = dependencies.setTimeout(() => {
            if (finishRequest(current)) {
                current.cancel();
                clearSnapshot();
            }
        }, config.timeoutMs);
        current.promise.then(response => {
            if (stopped || request !== current) {
                return;
            }
            const snapshot = prepareSnapshot(response);
            const remaining = snapshot.validForMs - (dependencies.now() - startedAt);
            if (remaining <= 0) {
                throw new Error('Snapshot expired in transit');
            }
            finishRequest(current);
            dependencies.clearTimeout(expiryTimer);
            dependencies.onSnapshot(snapshot);
            expiryTimer = dependencies.setTimeout(clearSnapshot, remaining);
        }).catch(() => {
            if (finishRequest(current)) {
                clearSnapshot();
            }
        });
    }

    function refresh() {
        if (stopped) {
            return;
        }
        dependencies.clearTimeout(pollTimer);
        dependencies.clearTimeout(deadlineTimer);
        const previous = request;
        request = null;
        if (previous) {
            previous.cancel();
        }
        clearSnapshot();
        poll();
    }

    function stop() {
        stopped = true;
        dependencies.clearTimeout(pollTimer);
        dependencies.clearTimeout(deadlineTimer);
        dependencies.clearTimeout(expiryTimer);
        if (request) {
            request.cancel();
            request = null;
        }
    }

    poll();
    return { refresh, stop };
}

module.exports = startSnapshotPolling;
