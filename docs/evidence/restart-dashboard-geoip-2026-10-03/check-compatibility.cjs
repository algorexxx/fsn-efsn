const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { createRequire } = require('node:module');
const dashboard = path.resolve(__dirname, '../../../tmp/fsn-stats-auth');
const load = createRequire(path.join(dashboard, 'package.json'));
const Node = load('./lib/node');
const prepareSnapshot = load('./react-frontend/src/snapshot-view');
const colorString = load('color-string');
const colorspace = load('colorspace');
const mode = process.argv[2];
assert.ok(['before', 'after'].includes(mode));
const addresses = ['72.229.28.185', '2001:1c04:400::1', '::ffff:72.229.28.185', '127.0.0.1', '10.0.0.1', '172.16.0.1', '192.168.0.1', '::1'];
const expectedLocations = [
    { country: 'US', region: 'NY', city: 'New York', timezone: 'America/New_York' },
    { country: 'NL', region: 'NH', city: 'Amsterdam', timezone: 'Europe/Amsterdam' },
    { country: 'US', region: 'NY', city: 'New York', timezone: 'America/New_York' },
    null, null, null, null, null,
];
const expectedColors = [[170, 187, 204, 1], [255, 0, 128, 0.5]];
const expectedIps = ['72.229.28.185', '2001:1c04:400::1', '72.229.28.185', '127.0.0.1', '10.0.0.1', '172.16.0.1', '192.168.0.1', '::1'];
const expectedMapNames = ['geo-0', 'geo-1', 'geo-2'];
const observedAt = '2026-10-03T00:00:00.000Z';
const namespaces = ['primus', 'primus:server', 'primus:spark', 'fusion-dashboard'];

const nodes = addresses.map((ip, index) => new Node({ id: 'geo-' + index, ip, info: { node: 'geo-fixture' } }).getInfo());
const locations = nodes.map(node => node.geo === null ? null : Object.fromEntries(['country', 'region', 'city', 'timezone'].map(key => [key, node.geo[key]])));
const snapshot = prepareSnapshot({ status: 200, headers: { 'x-dashboard-observed-at': observedAt, 'x-dashboard-valid-for-ms': '1000' }, data: nodes.map(node => ({ id: node.id, utctime: observedAt, stats: JSON.stringify(node) })) });
const colors = [colorString.get.rgb('#abc'), colorString.get.rgb('rgba(255, 0, 128, 0.5)')];
const diagnostics = namespaces.map(namespace => ({ namespace, color: colorspace(namespace) }));
const sizes = nodes.map(node => Buffer.byteLength(JSON.stringify(node.geo)));
const coordinateChecks = snapshot.geoCharts.map(point => Number.isFinite(point.latitude) && Number.isFinite(point.longitude) && Math.abs(point.latitude) <= 90 && Math.abs(point.longitude) <= 180);
const baseline = mode === 'after' ? JSON.parse(fs.readFileSync(path.join(__dirname, 'compatibility-before.json'), 'utf8')) : null;

assert.deepEqual(colors, expectedColors);
assert.deepEqual(nodes.map(node => node.info.ip), expectedIps);
assert.deepEqual(snapshot.geoCharts.map(point => point.name), expectedMapNames);
assert.deepEqual(coordinateChecks, [true, true, true]);
assert.ok(sizes.every(size => size <= 1024));
if (mode === 'after') {
    assert.deepEqual(locations, expectedLocations);
    assert.deepEqual(diagnostics, baseline.diagnostics);
    assert.equal(load('geoip-lite/package.json').version, '2.0.3');
    assert.equal(load('color-string/package.json').version, '1.9.1');
}
fs.writeFileSync(path.join(__dirname, 'compatibility-' + mode + '.json'), JSON.stringify({ runtime: process.version, geoipVersion: load('geoip-lite/package.json').version, colorStringVersion: load('color-string/package.json').version, addresses, nodes, locations, map: snapshot.geoCharts, sizes, colors, diagnostics, passed: true }, null, 2) + '\n');
console.log(JSON.stringify({ mode, lookups: addresses.length, mapPoints: snapshot.geoCharts.length, maxGeoBytes: Math.max(...sizes), passed: true }));
