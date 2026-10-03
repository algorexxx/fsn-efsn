const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const { test } = require('node:test');
const vm = require('node:vm');

const source = readFileSync(join(__dirname, 'baseline', 'server.js'), 'utf8');
const acceptedSecret = 'synthetic-accepted-telemetry-secret';

function loadCollector(environment = { WS_SECRET: acceptedSecret }) {
    const result = { calls: [], logs: [], sockets: new Map(), listening: false };
    const server = { listen() { result.listening = true; } };
    class Primus {
        constructor(_, options) {
            this.handlers = new Map();
            result.sockets.set(options.pathname, this);
        }
        plugin() {}
        on(name, handler) { this.handlers.set(name, handler); }
        write() {}
    }
    class Collection {
        setChartsCallback() {}
        add(data, callback) {
            result.calls.push({ method: 'add', id: data.id, spark: data.spark });
            callback(null, { id: data.id });
        }
        updateStats(id, stats, callback) {
            result.calls.push({ method: 'updateStats', id });
            callback(null, stats);
        }
        inactive(spark, callback) {
            result.calls.push({ method: 'inactive', spark });
            callback(null, { active: false });
        }
    }
    const modules = {
        lodash: { isUndefined: value => value === undefined, isNull: value => value === null, values: Object.values },
        './lib/utils/logger': {},
        './lib/utils/config': { banned: [] },
        chalk: {},
        http: { createServer: () => server },
        primus: Primus,
        'primus-emit': {},
        'primus-spark-latency': {},
        './lib/collection': Collection,
    };
    const consoleStub = Object.fromEntries(['info', 'error', 'success', 'warn', 'log'].map(name => [name, (...args) => result.logs.push(JSON.stringify(args))]));
    const context = vm.createContext({
        require(name) {
            if (name === './ws_secret.json') throw new Error('Synthetic fixture has no secret file');
            if (!Object.hasOwn(modules, name)) throw new Error(`Unexpected dependency: ${name}`);
            return modules[name];
        },
        process: { env: { NODE_ENV: 'production', ...environment } },
        console: consoleStub,
        setInterval: () => 0,
        module: { exports: {} },
    });
    try {
        vm.runInContext(source, context, { filename: 'archived-fsn-stats/server.js', timeout: 1000 });
    } catch (error) {
        result.startupError = error;
    }
    return result;
}

function connectCollector(collector, id = 'synthetic-session-a') {
    assert.equal(collector.startupError, undefined);
    const spark = {
        id,
        address: { ip: '127.0.0.1' },
        handlers: new Map(),
        emitted: [],
        ended: false,
        on(name, handler) { this.handlers.set(name, handler); },
        emit(name) { this.emitted.push(name); },
        end() { this.ended = true; },
    };
    collector.sockets.get('/api').handlers.get('connection')(spark);
    return spark;
}

function hello(spark, id = 'synthetic-node-a', secret = acceptedSecret) {
    spark.handlers.get('hello')({ id, secret, info: { name: id, node: 'synthetic-efsn', network: '99032659' } });
}

test('ordinary hello and same-node stats reach the collector', () => {
    const collector = loadCollector();
    const spark = connectCollector(collector);
    hello(spark);
    spark.handlers.get('stats')({ id: 'synthetic-node-a', stats: { peers: 1, mining: true } });
    assert.deepEqual(spark.emitted, ['ready']);
    assert.deepEqual(collector.calls, [
        { method: 'add', id: 'synthetic-node-a', spark: 'synthetic-session-a' },
        { method: 'updateStats', id: 'synthetic-node-a' },
    ]);
});

test('missing telemetry secret prevents listening', () => {
    const collector = loadCollector({});
    assert.equal(collector.listening, false, 'A deployment without any configured secret must fail before listening');
});

test('empty telemetry secret prevents listening', () => {
    const collector = loadCollector({ WS_SECRET: '' });
    assert.equal(collector.listening, false, 'An empty secret must not enable the telemetry listener');
});

test('stats require a successful hello on the same session', () => {
    const collector = loadCollector();
    const spark = connectCollector(collector);
    spark.handlers.get('stats')({ id: 'synthetic-node-a', stats: { peers: 1 } });
    assert.deepEqual(collector.calls, [], 'Unregistered sessions must not dispatch collection updates');
});

test('stats identity remains bound to the authenticated session', () => {
    const collector = loadCollector();
    const spark = connectCollector(collector);
    hello(spark);
    collector.calls.length = 0;
    spark.handlers.get('stats')({ id: 'synthetic-node-b', stats: { peers: 1 } });
    assert.deepEqual(collector.calls, [], 'A registered session must not dispatch updates for a different node');
});

test('rejected hello does not disclose its secret to logging', () => {
    const collector = loadCollector();
    const spark = connectCollector(collector);
    const rejectedSecret = 'synthetic-rejected-secret-must-be-redacted';
    hello(spark, 'synthetic-node-a', rejectedSecret);
    assert.equal(spark.ended, true);
    assert.equal(collector.logs.some(line => line.includes(rejectedSecret)), false, 'Authentication logs must omit telemetry secrets');
});

test('disconnect marks the originating session inactive', () => {
    const collector = loadCollector();
    const spark = connectCollector(collector);
    hello(spark);
    collector.calls.length = 0;
    spark.handlers.get('end')();
    assert.deepEqual(collector.calls, [{ method: 'inactive', spark: 'synthetic-session-a' }]);
});
