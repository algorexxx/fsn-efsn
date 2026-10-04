const fs = require('node:fs');
const net = require('node:net');
const path = require('node:path');
const {createRequire} = require('node:module');
const scratch = path.resolve(__dirname, '../../../tmp/dashboard-geoip-reader');
const load = createRequire(path.join(scratch, 'candidate/package.json'));
const {Reader} = load('mmdb-lib');
const reader = new Reader(fs.readFileSync(path.join(scratch, 'upstream/test-data/GeoLite2-City-Test.mmdb')));

function toDashboardGeo(record) {
    const country = record?.country?.iso_code;
    if (typeof country !== 'string' || !/^[A-Z]{2}$/.test(country)) {
        return null;
    }
    const latitude = record.location?.latitude;
    const longitude = record.location?.longitude;
    const hasCoordinates = Number.isFinite(latitude) && Number.isFinite(longitude) &&
        Math.abs(latitude) <= 90 && Math.abs(longitude) <= 180;
    return {country, ll: hasCoordinates ? [latitude, longitude] : null};
}

function lookup(ip) {
    if (typeof ip !== 'string' || !net.isIP(ip)) {
        return null;
    }
    return toDashboardGeo(reader.get(ip));
}

module.exports = {lookup, toDashboardGeo};
