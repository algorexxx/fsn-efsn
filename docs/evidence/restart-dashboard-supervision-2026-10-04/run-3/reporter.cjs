const {readFileSync} = require('node:fs');
const {createRequire} = require('node:module');
const local = createRequire(process.argv[2] + '/package.json');
const {connect, login, send} = local('./test/fixtures/wire-client.cjs');
const {block, stats} = local('./test/fixtures/telemetry-report.cjs');
const controlPath = process.argv[3];
let stopped = false;
let connection;
let timer;

async function report() {
    try {
        const control = JSON.parse(readFileSync(controlPath, 'utf8'));
        connection = connect({after() {}}, control.port, 'api');
        connection.closed.catch(() => {});
        await login(connection, 'supervision-node', control.secret);
        function update() {
            const current = JSON.parse(readFileSync(controlPath, 'utf8'));
            send(connection, 'block', {id: 'supervision-node', block: block(current.height)});
            send(connection, 'stats', {id: 'supervision-node', stats: stats()});
            send(connection, 'pending', {id: 'supervision-node', stats: {pending: 0}});
        }
        update();
        timer = setInterval(update, 1000);
        await connection.closed;
    } catch (_) {
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
