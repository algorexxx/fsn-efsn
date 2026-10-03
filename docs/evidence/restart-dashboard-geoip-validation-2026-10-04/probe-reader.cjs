const {createRequire} = require('node:module');
const path = require('node:path');
const load = createRequire(path.resolve(__dirname, '../../../tmp/fsn-stats-auth/package.json'));
const Node = load('./lib/node');
const addresses = ['2001:db8::1', '2001:db8::2'];
console.log(JSON.stringify(addresses.map((ip, index) => ({ip, geo: new Node({id: 'precision-' + index, ip, info: {node: 'fixture'}}).getInfo().geo}))));
