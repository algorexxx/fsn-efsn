const { createRequire } = require('node:module');
const { readFileSync } = require('node:fs');
const { resolve, dirname, join } = require('node:path');
const dashboard = resolve(__dirname, '../../../tmp/fsn-stats-auth');
const entries = {
    'server.js': ['lodash', 'chalk', 'primus', 'primus-emit', 'primus-spark-latency'],
    'lib/history.js': ['lodash', 'd3'],
    'lib/node.js': ['lodash', 'geoip-lite'],
    'api-server/app.js': ['express'],
    'db/index.js': ['pg'],
    'wsclient/wsclient.js': ['websocket'],
    'node_modules/primus/transformers/websockets/server.js': ['ws'],
};
const result = [];
for (const [entry, names] of Object.entries(entries)) {
    const request = createRequire(join(dashboard, entry));
    for (const name of names) {
        const file = request.resolve(name + '/package.json');
        const manifest = JSON.parse(readFileSync(file, 'utf8'));
        result.push({ entry, name, file, directory: dirname(file), version: manifest.version });
    }
}
process.stdout.write(JSON.stringify({ node: process.version, entries: result }, null, 2) + '\n');
