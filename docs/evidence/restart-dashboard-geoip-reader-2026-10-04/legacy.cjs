const assert = require('node:assert/strict');
const path = require('node:path');
const root = path.resolve(__dirname, '../../..');
const reader = process.argv[2] === 'patched'
    ? require(path.join(root, 'tmp/dashboard-geoip-reader/patched-legacy/geoip.js'))
    : require(path.join(root, 'tmp/fsn-stats-auth/node_modules/geoip-lite'));
const inputs = ['2001:db8::', '2001:db8::1', '2001:db8::2', '2001:db8::3', '2001:0DB8:0000:0000:0000:0000:0000:0002'];
const expected = process.argv[2] === 'patched' ? [null, 'NO', 'SE', null, 'SE'] : ['NO', 'NO', 'NO', 'NO', 'NO'];

const actual = inputs.map(ip => reader.lookup(ip)?.country ?? null);

assert.deepStrictEqual(actual, expected);
console.log(JSON.stringify({mode: process.argv[2], inputs, expected, actual}));
