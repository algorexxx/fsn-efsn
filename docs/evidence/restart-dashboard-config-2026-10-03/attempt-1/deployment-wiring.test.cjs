const assert = require('node:assert/strict');
const { test } = require('node:test');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const { once } = require('node:events');
const http = require('node:http');
const vm = require('node:vm');
const config = require('../lib/deployment-config');
const { credentialFile, loadCollector } = require('./fixtures/collector.cjs');

function evaluate(file, environment, requireDependency, globals = {}) {
    const module = { exports: {} };
    vm.runInNewContext(readFileSync(join(__dirname, '..', file), 'utf8'), {
        process: { env: environment }, module, require: requireDependency,
        console: { log() {}, error() {} }, ...globals,
    }, { filename: file, timeout: 1000 });
    return module.exports;
}

function loadDatabase(environment, Pool) {
    return evaluate('db/index.js', environment, name => {
        if (name === '../lib/deployment-config') return config;
        assert.equal(name, 'pg');
        return { Pool };
    });
}

function databaseEnvironment(t) {
    return { DB_HOST: '127.0.0.1', DB_PORT: '5439', DB_NAME: 'stats_test', DB_USER: 'stats_reader', DB_PASSWORD_FILE: credentialFile(t, 'synthetic-password', true) };
}

test('collector passes explicit settings to listen and refuses missing or public binds', t => {
    const collector = loadCollector(t, { environment: { COLLECTOR_PORT: '3100' } });
    assert.equal(collector.startupError, undefined);
    assert.deepEqual(collector.listener, { port: 3100, host: '127.0.0.1' });
    for (const environment of [{ COLLECTOR_PORT: undefined }, { COLLECTOR_HOST: '0.0.0.0' }]) {
        const invalid = loadCollector(t, { environment });
        assert.match(invalid.startupError.message, /COLLECTOR_/);
        assert.equal(invalid.listening, false);
        assert.equal(invalid.sockets.size, 0);
    }
});

test('database pool receives configured credentials without inherited defaults', t => {
    const environment = databaseEnvironment(t);
    let actual;
    class Pool { constructor(settings) { actual = settings; } }

    loadDatabase(environment, Pool);

    assert.deepEqual(actual, { host: '127.0.0.1', port: 5439, database: 'stats_test', user: 'stats_reader', password: 'synthetic-password', max: 5, ssl: false });
});

test('invalid database configuration stops before constructing a pool', () => {
    let constructions = 0;
    class Pool { constructor() { constructions++; } }

    assert.throws(() => loadDatabase({}, Pool), /DB_HOST/);
    assert.equal(constructions, 0);
});

test('API listener validation happens before loading Express or the database', () => {
    const dependencies = [];

    assert.throws(() => evaluate('api-server/server.js', { API_HOST: '0.0.0.0', API_PORT: '3002' }, name => {
        dependencies.push(name);
        if (name === '../lib/deployment-config') return config;
        throw new Error('Unexpected dependency');
    }), /API_HOST/);
    assert.deepEqual(dependencies, ['../lib/deployment-config']);
});

test('real HTTP API binds to configured loopback and serves data without wildcard CORS', { timeout: 5000 }, async t => {
    class Retrieve { nodeGetAllDb() { return Promise.resolve('[{"id":"synthetic-node"}]'); } }
    const server = evaluate('api-server/server.js', { API_HOST: '127.0.0.1', API_PORT: '0' }, name => {
        if (name === '../lib/deployment-config') return config;
        if (name === '../db_methods/retrieve') return Retrieve;
        assert.equal(name, 'express');
        return require('express');
    });
    t.after(() => new Promise(resolve => server.close(resolve)));
    await once(server, 'listening');
    assert.equal(server.address().address, '127.0.0.1');
    const response = await new Promise((resolve, reject) => {
        const request = http.get({ host: '127.0.0.1', port: server.address().port, path: '/nodes', agent: false, headers: { Origin: 'https://unrelated.example' } }, res => {
            let body = '';
            res.setEncoding('utf8');
            res.on('data', chunk => { body += chunk; });
            res.on('end', () => resolve({ status: res.statusCode, body, origin: res.headers['access-control-allow-origin'] }));
            res.on('error', reject);
        });
        request.on('error', reject);
    });
    assert.deepEqual(response, { status: 200, body: '[{"id":"synthetic-node"}]', origin: undefined });
});

test('persistence uses the configured URL and validates database settings before connecting', t => {
    const environment = { ...databaseEnvironment(t), COLLECTOR_WS_URL: 'ws://127.0.0.1:3100/primus' };
    const connections = [];
    let initializations = 0;
    class Populate { initDbAndTables() { initializations++; } }
    class WebSocket { constructor(url) { connections.push(url); } }
    class Pool {}
    const requireDependency = name => {
        if (name === '../lib/deployment-config') return config;
        if (name === '../db_methods/populate') {
            loadDatabase(environment, Pool);
            return Populate;
        }
        assert.equal(name, 'websocket');
        return { w3cwebsocket: WebSocket };
    };

    evaluate('wsclient/wsclient.js', environment, requireDependency, { setTimeout() { return 0; } });
    assert.deepEqual(connections, ['ws://127.0.0.1:3100/primus']);
    assert.equal(initializations, 1);
    delete environment.DB_PASSWORD_FILE;
    assert.throws(() => evaluate('wsclient/wsclient.js', environment, requireDependency), /DB_PASSWORD_FILE/);
    assert.deepEqual(connections, ['ws://127.0.0.1:3100/primus']);
});

test('missing persistence URL stops before loading the database or opening a socket', () => {
    const dependencies = [];

    assert.throws(() => evaluate('wsclient/wsclient.js', {}, name => {
        dependencies.push(name);
        if (name === '../lib/deployment-config') return config;
        throw new Error('Unexpected dependency');
    }), /COLLECTOR_WS_URL/);
    assert.deepEqual(dependencies, ['../lib/deployment-config']);
});
