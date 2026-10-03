const path = require('node:path');
const {createRequire} = require('node:module');
const load = createRequire(path.resolve(__dirname, '../../../tmp/fsn-stats-auth/package.json'));
const Node = load('./lib/node');
const snapshot = load('./react-frontend/src/snapshot-view');
const addresses = ['192.0.2.1', '2001:db8::1', '::ffff:192.0.2.1', '127.0.0.1'];
const date = '2026-10-04T00:00:00.000Z';
function readSnapshot() {
    const nodes = addresses.map((ip, index) => new Node({id: 'fixture-' + index, ip, info: {node: 'fixture'}}).getInfo());
    const view = snapshot({status: 200, headers: {'x-dashboard-observed-at': date, 'x-dashboard-valid-for-ms': '1000'}, data: nodes.map(node => ({id: node.id, utctime: date, stats: JSON.stringify(node)}))});
    console.log(JSON.stringify({runtime: process.version, nodes: nodes.map(node => ({id: node.id, ip: node.info.ip, geo: node.geo})), map: view.geoCharts}));
}

readSnapshot();
if (process.argv[2] === '--watch') {
    const lines = require('node:readline').createInterface({input: process.stdin});
    lines.on('line', line => {
        if (line === 'lookup') readSnapshot();
        else if (line === 'stop') lines.close();
        else throw new Error('Unknown fixture command');
    });
}
