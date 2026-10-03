const assert = require('node:assert/strict');
const { existsSync, readFileSync } = require('node:fs');
const { createRequire } = require('node:module');
const { join, resolve } = require('node:path');

const directory = resolve(process.argv[2]);
const rootRequire = createRequire(join(directory, 'package.json'));
const apiRequire = createRequire(join(directory, 'api-server/server.js'));
const manifest = JSON.parse(readFileSync(join(directory, 'package.json'), 'utf8'));
const rootExpress = rootRequire.resolve('express');
const apiExpress = apiRequire.resolve('express');
const version = apiRequire('express/package.json').version;
const legacyPaths = ['api-server/package.json', 'api-server/package-lock.json', 'api-server/node_modules'];
assert.equal(apiExpress, rootExpress);
assert.equal(version, '4.22.3');
assert.equal(manifest.dependencies.express, version);
assert.equal(manifest.scripts['start:api'], 'node api-server/server.js');
for (const name of legacyPaths) {
    assert.equal(existsSync(join(directory, name)), false);
}
console.log(JSON.stringify({ runtime: process.version, rootExpress, apiExpress, version, apiStart: manifest.scripts['start:api'], absent: legacyPaths }));
