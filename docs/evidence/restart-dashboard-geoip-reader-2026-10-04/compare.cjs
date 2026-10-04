const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {createRequire} = require('node:module');
const root = path.resolve(__dirname, '../../..');
const scratch = path.join(root, 'tmp/dashboard-geoip-reader');
const load = createRequire(path.join(scratch, 'candidate/package.json'));
const {Reader} = load('mmdb-lib');
const prototype = require('./prototype.cjs');
const expected = JSON.parse(fs.readFileSync(path.join(scratch, 'expected.json'), 'utf8'));

function checkCases(file, cases) {
    const reader = new Reader(fs.readFileSync(path.join(scratch, 'upstream/test-data', file)));
    const failures = [];
    for (const row of cases) {
        const actual = reader.get(row.ip);
        try {
            assert.deepStrictEqual(actual, row.expected);
        } catch (error) {
            failures.push({ip: row.ip, expected: row.expected, actual});
        }
    }
    return {file, cases: cases.length, failures, metadata: reader.metadata};
}

const results = [checkCases('GeoLite2-City-Test.mmdb', expected.city)];
for (const size of [24, 28, 32]) {
    results.push(checkCases('MaxMind-DB-test-ipv6-' + size + '.mmdb', expected.precision));
}
const inputs = ['2.125.160.216', '::ffff:2.125.160.216', '::FFFF:027D:A0D8', '2001:218::', '127.0.0.1', 'invalid', null];
const expectedGeo = [
    {country: 'GB', ll: [51.75, -1.25]},
    {country: 'GB', ll: [51.75, -1.25]},
    {country: 'GB', ll: [51.75, -1.25]},
    {country: 'JP', ll: [35.68536, 139.75309]},
    null, null, null,
];
const mappingInputs = [null, {}, {country: {iso_code: 'SE'}}, {registered_country: {iso_code: 'SE'}},
    {country: {iso_code: 'SE'}, location: {latitude: 0, longitude: 0}},
    {country: {iso_code: 'SE'}, location: {latitude: 91, longitude: 18}},
    {country: {iso_code: 'SE'}, location: {latitude: 59}},
    {country: {iso_code: 'se'}, location: {latitude: 59, longitude: 18}}];
const expectedMapping = [null, null, {country: 'SE', ll: null}, null,
    {country: 'SE', ll: [0, 0]}, {country: 'SE', ll: null}, {country: 'SE', ll: null}, null];

const actualGeo = inputs.map(prototype.lookup);
const actualMapping = mappingInputs.map(prototype.toDashboardGeo);

fs.writeFileSync(path.join(__dirname, 'reader-results.json'), JSON.stringify({runtime: process.version, results, actualGeo, actualMapping}, null, 2) + '\n');
assert.deepStrictEqual(results.map(result => result.failures), [[], [], [], []]);
assert.deepStrictEqual(actualGeo, expectedGeo);
assert.deepStrictEqual(actualMapping, expectedMapping);
console.log(JSON.stringify({passed: true, raw_lookup_cases: results.reduce((sum, result) => sum + result.cases, 0), mapped_lookup_cases: inputs.length, mapping_cases: mappingInputs.length}));
