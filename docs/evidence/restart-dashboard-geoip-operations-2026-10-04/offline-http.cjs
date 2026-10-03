const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {EventEmitter} = require('node:events');
const {PassThrough} = require('node:stream');
const {createHash} = require('node:crypto');

const root = fs.realpathSync(process.env.GEOIP_FIXTURE_ROOT);
for (const key of ['GEODATADIR', 'GEOTMPDIR']) {
    const selected = path.resolve(process.env[key]);
    assert.ok(selected.startsWith(root + path.sep));
    assert.notEqual(selected, root);
}
const mode = process.env.GEOIP_FIXTURE_MODE;
const ledger = process.env.GEOIP_FIXTURE_LEDGER;
const blocked = () => { throw new Error('Fixture forbids network connections'); };
require('node:net').Socket.prototype.connect = blocked;
require('node:tls').connect = blocked;
require('node:http').get = blocked;
require('node:http').request = blocked;
require('node:https').request = blocked;
require('node:https').get = (options, callback) => {
    const url = new URL(options.path, 'https://' + options.hostname);
    assert.equal(url.hostname, 'download.maxmind.com');
    const edition = url.searchParams.get('edition_id');
    const suffix = url.searchParams.get('suffix');
    assert.ok(['GeoLite2-Country-CSV', 'GeoLite2-City-CSV'].includes(edition));
    assert.ok(['zip', 'zip.sha256'].includes(suffix));
    fs.appendFileSync(ledger, JSON.stringify({edition, suffix}) + '\n');
    const client = new EventEmitter();
    client.destroy = () => {};
    if (mode === 'stall-city' && edition === 'GeoLite2-City-CSV') {
        setInterval(() => {}, 1000);
        return client;
    }
    const archive = fs.readFileSync(path.join(root, 'archives', edition + '.zip'));
    const digest = createHash('sha256').update(archive).digest('hex');
    const response = new PassThrough();
    response.statusCode = mode === 'checksum-503' || (mode === 'city-503' && edition === 'GeoLite2-City-CSV') ? 503 : 200;
    response.headers = {};
    const checksum = mode === 'checksum-mismatch' ? '0'.repeat(64) : digest;
    const body = suffix === 'zip.sha256' ? (mode === 'empty-checksum' ? '' : checksum) : (mode === 'corrupt-zip' ? Buffer.from('unfinished archive') : archive);
    process.nextTick(() => {
        callback(response);
        response.end(body);
    });
    return client;
};
