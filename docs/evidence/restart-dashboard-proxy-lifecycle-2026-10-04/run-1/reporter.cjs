const {createRequire} = require('node:module');
const {readFileSync} = require('node:fs');
const local = createRequire(process.argv[2] + '/package.json');
const {connect, login, send} = local('./test/fixtures/wire-client.cjs');
const {block, stats} = local('./test/fixtures/telemetry-report.cjs');
const config = JSON.parse(readFileSync(process.argv[3], 'utf8'));
const ca = readFileSync(config.ca);
let connection;
let timer;
let stopped = false;
let sequence = 0;
function record(event) { console.log(JSON.stringify({event, sequence, time: Date.now()})); }
async function report() {
    try {
        connection = connect({after() {}}, config.port, 'api', {secure: true, ca, servername: 'dashboard.test', headers: {Host: 'dashboard.test'}});
        connection.closed.catch(() => {});
        await login(connection, 'proxy-node', config.secret);
        sequence++;
        record('connected');
        connection.socket.on('message', raw => {
            const message = JSON.parse(String(raw));
            if (message.emit?.[0] === 'node-pong') record('pong');
        });
        function update() {
            send(connection, 'block', {id: 'proxy-node', block: block(901)});
            send(connection, 'stats', {id: 'proxy-node', stats: stats()});
            send(connection, 'pending', {id: 'proxy-node', stats: {pending: 0}});
            send(connection, 'node-ping', {id: 'proxy-node', clientTime: String(Date.now())});
        }
        update();
        timer = setInterval(update, 1000);
        await connection.closed;
        record('disconnected');
    } catch (_) {
        record('connection-failed');
        connection?.socket.terminate();
    } finally {
        clearInterval(timer);
        if (!stopped) setTimeout(report, 500);
    }
}
process.once('SIGTERM', () => {
    stopped = true;
    clearInterval(timer);
    connection?.socket.terminate();
});
report();
