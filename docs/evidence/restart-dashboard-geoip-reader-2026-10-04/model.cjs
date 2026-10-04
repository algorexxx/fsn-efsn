const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const root = path.resolve(__dirname, '../../..');
const modelPath = path.join(root, 'tmp/fsn-stats-auth/lib/node.js');
const source = fs.readFileSync(modelPath, 'utf8').replace(/\r\n/g, '\n');
const oldPrefixStrip = '\tif (ip.substr(0, 7) == "::ffff:") {\n\t\tip = ip.substr(7)\n        }\n';
assert.equal(source.split(oldPrefixStrip).length, 2);
assert.equal(source.split("require('geoip-lite')").length, 2);
const candidateSource = source.replace(oldPrefixStrip, '').replace("require('geoip-lite')", 'require(' + JSON.stringify(path.join(__dirname, 'prototype.cjs')) + ')');
const candidateModule = new Module(modelPath, module);
candidateModule.filename = modelPath;
candidateModule.paths = Module._nodeModulePaths(path.dirname(modelPath));
candidateModule._compile(candidateSource, modelPath);
const Node = candidateModule.exports;
const snapshot = require(path.join(root, 'tmp/fsn-stats-auth/react-frontend/src/snapshot-view'));
const inputs = ['2.125.160.216', '::ffff:2.125.160.216', '::FFFF:027D:A0D8', '2001:218::', '127.0.0.1'];
const date = '2026-10-04T00:00:00.000Z';
const expected = [
    {country: 'GB', ll: [51.75, -1.25]}, {country: 'GB', ll: [51.75, -1.25]},
    {country: 'GB', ll: [51.75, -1.25]}, {country: 'JP', ll: [35.68536, 139.75309]}, null,
];
const expectedMap = [
    {name: 'fixture-0', radius: 2, latitude: 51.75, longitude: -1.25, fillKey: 'bubbleFill'},
    {name: 'fixture-1', radius: 2, latitude: 51.75, longitude: -1.25, fillKey: 'bubbleFill'},
    {name: 'fixture-2', radius: 2, latitude: 51.75, longitude: -1.25, fillKey: 'bubbleFill'},
    {name: 'fixture-3', radius: 2, latitude: 35.68536, longitude: 139.75309, fillKey: 'bubbleFill'},
];

const nodes = inputs.map((ip, index) => new Node({id: 'fixture-' + index, ip, info: {node: 'fixture'}}).getInfo());
const rows = nodes.map(node => ({id: node.id, utctime: date, stats: JSON.stringify(node)}));
const view = snapshot({status: 200, headers: {'x-dashboard-observed-at': date, 'x-dashboard-valid-for-ms': '1000'}, data: rows});
const actual = nodes.map(node => node.geo);
const actualView = view.nodesList.map(node => node.geo);

assert.deepStrictEqual(actual, expected);
assert.deepStrictEqual(actualView, expected);
assert.deepStrictEqual(view.geoCharts, expectedMap);
console.log(JSON.stringify({passed: true, candidate_in_memory_only: true, node_geo: actual, snapshot_geo: actualView, map: view.geoCharts}));

const missingCoordinateNode = new Node({id: 'country-only', ip: '127.0.0.1', info: {node: 'fixture'}}).getInfo();
missingCoordinateNode.geo = {country: 'SE', ll: null};
const expectedCurrentView = {geo: null, map: []};

const currentView = snapshot({status: 200, headers: {'x-dashboard-observed-at': date, 'x-dashboard-valid-for-ms': '1000'}, data: [{id: missingCoordinateNode.id, utctime: date, stats: JSON.stringify(missingCoordinateNode)}]});
const actualCurrentView = {geo: currentView.nodesList[0].geo, map: currentView.geoCharts};

assert.deepStrictEqual(actualCurrentView, expectedCurrentView);
console.log(JSON.stringify({characterization: 'Existing snapshot discards a known country when coordinates are absent', input: missingCoordinateNode.geo, observed: actualCurrentView, required_after_integration: {geo: {country: 'SE', ll: null}, map: []}}));
