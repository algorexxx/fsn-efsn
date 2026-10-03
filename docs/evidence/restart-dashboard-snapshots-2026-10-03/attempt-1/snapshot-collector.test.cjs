const assert = require('node:assert/strict');
const { test } = require('node:test');
const startSnapshotCollection = require('../wsclient/collect-snapshots');
const { loadPersistenceConfig, loadApiConfig } = require('../lib/deployment-config');

const observedAt = new Date('2026-10-03T12:00:00.000Z');
const nodeA = { id: 'node-a', info: { name: "Peter's node", node: 'efsn-test' }, stats: { active: true, block: { number: 10, hash: 'block-a' }, peers: 1 }, history: [], geo: null };
const nodeB = { id: 'node-b', info: { name: 'Node B', node: 'efsn-test' }, stats: { active: true, block: { number: 20, hash: 'block-b' }, peers: 2 }, history: [], geo: null };
const charts = { height: [10, 20] };
const flush = () => new Promise(resolve => setImmediate(resolve));

function setup(t, save) {
    const timers = new Map();
    const connections = [];
    const writes = [];
    const errors = [];
    let nextTimer = 0;
    const collector = startSnapshotCollection({ url: 'ws://127.0.0.1:3000/primus', intervalMs: 100, timeoutMs: 500, maxBytes: 4096, maxNodes: 2 }, {
        connect(url, maxBytes) {
            const connection = { url, maxBytes, sent: [], closed: false, send(value) { this.sent.push(JSON.parse(value)); }, close() { this.closed = true; if (this.onclose) this.onclose(); } };
            connections.push(connection);
            return connection;
        },
        saveSnapshot: (payload, time) => { writes.push({ payload, time }); return save ? save(payload, time) : Promise.resolve(); },
        now: () => observedAt,
        setTimeout: (action, delay) => { timers.set(++nextTimer, { action, delay }); return nextTimer; },
        clearTimeout: timer => timers.delete(timer),
        onError: message => errors.push(message),
    });
    t.after(() => collector.stop());
    function tick() {
        assert.equal(timers.size, 1);
        const [id, timer] = [...timers.entries()][0];
        timers.delete(id);
        timer.action();
    }
    return { collector, timers, connections, writes, errors, tick };
}

function deliver(connection, message) {
    connection.onmessage({ data: JSON.stringify(message) });
}

function snapshot(connection, nodes = [nodeA, nodeB]) {
    deliver(connection, { emit: ['init', { nodes }] });
    deliver(connection, { action: 'charts', data: charts });
}

test('requires explicit positive sampling, deadline, size, node and freshness settings', () => {
    const environment = { COLLECTOR_WS_URL: 'ws://127.0.0.1:3000/primus', SNAPSHOT_INTERVAL_MS: '100', SNAPSHOT_TIMEOUT_MS: '500', SNAPSHOT_MAX_BYTES: '4096', SNAPSHOT_MAX_NODES: '2' };
    assert.deepEqual(loadPersistenceConfig(environment), { url: 'ws://127.0.0.1:3000/primus', intervalMs: 100, timeoutMs: 500, maxBytes: 4096, maxNodes: 2 });
    for (const name of Object.keys(environment).filter(name => name.startsWith('SNAPSHOT_'))) {
        for (const value of [undefined, '0', '-1', '1.5', '2147483648']) {
            assert.throws(() => loadPersistenceConfig({ ...environment, [name]: value }), new RegExp(name));
        }
    }
    assert.throws(() => loadApiConfig({ API_HOST: '127.0.0.1', API_PORT: '3002' }), /SNAPSHOT_MAX_AGE_MS/);
});

test('stores two complete nodes with their own metadata and block after charts arrive', async t => {
    const fixture = setup(t);
    const connection = fixture.connections[0];
    connection.onopen();
    deliver(connection, { action: 'charts', data: { early: true } });
    deliver(connection, { action: 'stats', data: { id: 'node-a', stats: { peers: 999 } } });
    snapshot(connection, [{ ...nodeA, spark: 'private-session', uptime: { internal: true } }, nodeB]);
    await flush();
    assert.deepEqual(connection.sent, [{ emit: ['ready', {}] }]);
    assert.deepEqual(fixture.writes, [{ payload: { nodes: [nodeA, nodeB], charts }, time: observedAt }]);
    assert.deepEqual([...fixture.timers.values()].map(timer => timer.delay), [100]);
});

test('answers Primus heartbeats while idle without writing or adding timers', async t => {
    const fixture = setup(t);
    const connection = fixture.connections[0];
    connection.onopen();
    deliver(connection, 'primus::ping::12345');
    await flush();
    assert.deepEqual(connection.sent, [{ emit: ['ready', {}] }, 'primus::pong::12345']);
    assert.deepEqual(fixture.writes, []);
    assert.deepEqual([...fixture.timers.values()].map(timer => timer.delay), [500]);
});

test('database backpressure permits only one write and no queued snapshots', async t => {
    let release;
    const fixture = setup(t, () => new Promise(resolve => { release = resolve; }));
    const connection = fixture.connections[0];
    connection.onopen();
    snapshot(connection);
    await flush();
    snapshot(connection, []);
    deliver(connection, 'primus::ping::1');
    assert.deepEqual(fixture.writes, [{ payload: { nodes: [nodeA, nodeB], charts }, time: observedAt }]);
    assert.equal(fixture.timers.size, 0);
    release();
    await flush();
    assert.deepEqual([...fixture.timers.values()].map(timer => timer.delay), [100]);
});

test('disconnect while writing waits for completion and ignores late old callbacks', async t => {
    let release;
    const fixture = setup(t, () => new Promise(resolve => { release = resolve; }));
    const old = fixture.connections[0];
    old.onopen();
    snapshot(old);
    await flush();
    old.onclose();
    assert.equal(fixture.timers.size, 0);
    release();
    await flush();
    fixture.tick();
    const current = fixture.connections[1];
    old.onopen();
    old.onclose();
    snapshot(old, []);
    current.onopen();
    assert.equal(current.closed, false);
    assert.deepEqual(current.sent, [{ emit: ['ready', {}] }]);
    assert.equal(fixture.writes.length, 1);
    assert.equal(fixture.timers.size, 1);
});

test('uncertain write failure reconnects for a fresh snapshot without replaying the old write', async t => {
    const fixture = setup(t, () => Promise.reject(new Error('private database detail')));
    const old = fixture.connections[0];
    old.onopen();
    snapshot(old);
    await flush();
    fixture.tick();
    fixture.connections[1].onopen();
    assert.equal(old.closed, true);
    assert.equal(fixture.writes.length, 1);
    assert.deepEqual(fixture.errors, ['Dashboard snapshot write failed']);
    assert.deepEqual(fixture.connections[1].sent, [{ emit: ['ready', {}] }]);
});

test('missing charts expire the whole sample and reconnect with one timer', t => {
    const fixture = setup(t);
    const connection = fixture.connections[0];
    connection.onopen();
    deliver(connection, { emit: ['init', { nodes: [nodeA] }] });
    fixture.tick();
    connection.onclose();
    assert.deepEqual(fixture.writes, []);
    assert.equal(connection.closed, true);
    assert.deepEqual([...fixture.timers.values()].map(timer => timer.delay), [100]);
});

test('invalid or oversized snapshots retain the last database state and redact errors', async t => {
    for (const data of ['private-invalid-json', JSON.stringify({ emit: ['init', { nodes: [nodeA, nodeA] }] }), JSON.stringify({ emit: ['init', { nodes: [nodeA, nodeB, { ...nodeA, id: 'node-c' }] }] }), JSON.stringify({ emit: ['init', { nodes: [{ ...nodeA, stats: null }] }] }), 'x'.repeat(4097)]) {
        const fixture = setup(t);
        fixture.connections[0].onopen();
        fixture.connections[0].onmessage({ data });
        await flush();
        assert.deepEqual(fixture.writes, []);
        assert.deepEqual(fixture.errors, ['Collector snapshot rejected']);
        assert.equal(fixture.connections[0].closed, true);
        await fixture.collector.stop();
    }
});

test('stop drains a pending write and prevents further timers or reconnects', async t => {
    let release;
    const fixture = setup(t, () => new Promise(resolve => { release = resolve; }));
    const connection = fixture.connections[0];
    connection.onopen();
    snapshot(connection);
    await flush();
    const stopping = fixture.collector.stop();
    connection.onopen();
    snapshot(connection, []);
    release();
    await stopping;
    assert.equal(connection.closed, true);
    assert.equal(fixture.timers.size, 0);
    assert.equal(fixture.connections.length, 1);
    assert.equal(fixture.writes.length, 1);
});
