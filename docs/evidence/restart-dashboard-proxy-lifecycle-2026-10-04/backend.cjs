const {createRequire} = require('node:module');
const {writeFileSync, renameSync} = require('node:fs');
const {once} = require('node:events');
const http = require('node:http');
const local = createRequire(process.argv[2] + '/package.json');
const directory = process.argv[3];
Object.assign(process.env, local('./test/fixtures/collector-environment.cjs'), {
    WS_CREDENTIALS_FILE: directory + '/telemetry.json',
    COLLECTOR_HELLO_TIMEOUT_MS: '5000',
    VERBOSITY: '1',
});
const server = local('./server.js');
const createApp = local('./api-server/app.js');
const collect = local('./wsclient/collect-snapshots.js');
const WebSocket = local('websocket').w3cwebsocket;
let snapshot = null;
let writer;
const app = createApp({readSnapshot: async () => snapshot}, Date.now, 10000, 10000);
const api = http.createServer((request, response) => {
    if (request.url.startsWith('/nodes?fault=')) {
        request.socket.destroy();
        return;
    }
    app(request, response);
}).listen(0, '127.0.0.1');

async function start() {
    await Promise.all([once(server, 'listening'), once(api, 'listening')]);
    writer = collect({url: `ws://127.0.0.1:${server.address().port}/primus`, intervalMs: 1000, timeoutMs: 6000, maxBytes: 1048576, maxNodes: 8}, {
        connect: (url, maxBytes) => new WebSocket(url, undefined, undefined, undefined, undefined, {maxReceivedFrameSize: maxBytes, maxReceivedMessageSize: maxBytes}),
        saveSnapshot: async (payload, observed_at) => { snapshot = {payload, observed_at}; },
        now: () => new Date(), setTimeout, clearTimeout, onError: message => console.error(message),
    });
    writeFileSync(directory + '/ready.new', JSON.stringify({collector: server.address().port, api: api.address().port}));
    renameSync(directory + '/ready.new', directory + '/ready.json');
}
process.once('SIGTERM', async () => {
    await writer?.stop();
    process.exit(0);
});
start().catch(error => { console.error(error); process.exit(1); });
