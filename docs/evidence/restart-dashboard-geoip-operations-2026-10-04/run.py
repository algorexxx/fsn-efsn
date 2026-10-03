import hashlib
import ipaddress
import json
import os
import struct
import subprocess
import sys
import zipfile
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
package = dashboard / 'node_modules/geoip-lite'
runtime = root / 'tmp/dashboard-runtime-review/v24.21.0/node'
output = bundle / ('run-' + sys.argv[1])
scratch = root / 'tmp' / ('dashboard-geoip-operations-' + sys.argv[1])
assert sys.argv[1].isdigit()
output.mkdir(exist_ok=False)
scratch.mkdir(exist_ok=False)
os.umask(0o077)


def hashes(directory):
    return {p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(directory.rglob('*')) if p.is_file()}


def binaries(country, region, city, timezone, latitude, longitude):
    network4 = ipaddress.ip_network('192.0.2.0/24')
    network6 = ipaddress.ip_network('2001:db8::/32')
    names = bytearray(88)
    for offset, value in [(0, country), (2, region), (9, '1'), (10, timezone), (42, city)]:
        names[offset:offset + len(value)] = value.encode('utf-8')
    first4, last4 = int(network4.network_address), int(network4.broadcast_address)
    first6, last6 = network6.network_address.packed, network6.broadcast_address.packed
    return {
        'geoip-country.dat': struct.pack('>II2s', first4, last4, country.encode()),
        'geoip-country6.dat': first6 + last6 + country.encode(),
        'geoip-city-names.dat': bytes(names),
        'geoip-city.dat': struct.pack('>IIIiii', first4, last4, 0, latitude, longitude, 10),
        'geoip-city6.dat': first6 + last6 + struct.pack('>Iiii', 0, latitude, longitude, 10),
    }


def write_set(directory, values):
    directory.mkdir()
    for name, value in values.items():
        (directory / name).write_bytes(value)


def zip_csv(edition, rows):
    target = scratch / 'archives' / (edition + '.zip')
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for suffix, content in rows.items():
            info = zipfile.ZipInfo('fixture/' + edition.removesuffix('-CSV') + suffix, (2026, 10, 4, 0, 0, 0))
            archive.writestr(info, content.encode('utf-8'))
    return hashlib.sha256(target.read_bytes()).hexdigest()


def lookup(directory):
    result = subprocess.run([runtime, bundle / 'lookup.cjs'], env=dict(os.environ, GEODATADIR=str(directory)), capture_output=True, timeout=10)
    return {'exit': result.returncode, 'value': json.loads(result.stdout) if result.returncode == 0 else None, 'stderr': result.stderr.decode()}


old = binaries('SE', 'AB', 'Fixture A', 'Europe/Stockholm', 593293, 180686)
expected = binaries('NO', '03', 'Fixture B', 'Europe/Oslo', 599139, 107522)
active = scratch / 'active-a'
write_set(active, old)
initial_active = hashes(active)
baseline = {'dashboard_commit': json.loads((bundle / 'source-baseline.json').read_text(encoding='utf-8'))['dashboard_commit'], 'package_sha256': hashes(package), 'active_sha256': initial_active}
(output / 'baseline.json').write_text(json.dumps(baseline, indent=2) + '\n', encoding='utf-8')
(scratch / 'archives').mkdir()
country_hash = zip_csv('GeoLite2-Country-CSV', {
    '-Locations-en.csv': 'geoname_id,locale_code,continent_code,continent_name,country_iso_code,country_name\n1,en,EU,Europe,NO,Norway\n',
    '-Blocks-IPv4.csv': 'network,geoname_id,registered_country_geoname_id,represented_country_geoname_id,is_anonymous_proxy,is_satellite_provider\n192.0.2.0/24,1,1,,0,0\n',
    '-Blocks-IPv6.csv': 'network,geoname_id,registered_country_geoname_id,represented_country_geoname_id,is_anonymous_proxy,is_satellite_provider\n2001:db8::/32,1,1,,0,0\n',
})
city_hash = zip_csv('GeoLite2-City-CSV', {
    '-Locations-en.csv': 'geoname_id,locale_code,continent_code,continent_name,country_iso_code,country_name,subdivision_1_iso_code,subdivision_1_name,subdivision_2_iso_code,subdivision_2_name,city_name,metro_code,time_zone,is_in_european_union\n1,en,EU,Europe,NO,Norway,03,Oslo,,,Fixture B,0,Europe/Oslo,1\n',
    '-Blocks-IPv4.csv': 'network,geoname_id,registered_country_geoname_id,represented_country_geoname_id,is_anonymous_proxy,is_satellite_provider,postal_code,latitude,longitude,accuracy_radius\n192.0.2.0/24,1,1,,0,0,,59.9139,10.7522,10\n',
    '-Blocks-IPv6.csv': 'network,geoname_id,registered_country_geoname_id,represented_country_geoname_id,is_anonymous_proxy,is_satellite_provider,postal_code,latitude,longitude,accuracy_radius\n2001:db8::/32,1,1,,0,0,,59.9139,10.7522,10\n',
})
expected_with_checksums = dict(expected, **{'country.checksum': country_hash.encode(), 'city.checksum': city_hash.encode()})
expected_hashes = {name: hashlib.sha256(value).hexdigest() for name, value in expected_with_checksums.items()}
(output / 'fixture-inputs.json').write_text(json.dumps({'archive_sha256': hashes(scratch / 'archives'), 'expected_binary_hex': {name: value.hex() for name, value in expected.items()}, 'expected_sha256': expected_hashes}, indent=2) + '\n', encoding='utf-8')
records = []
for mode in ['missing-license', 'checksum-503', 'empty-checksum', 'corrupt-zip', 'city-503', 'stall-city', 'checksum-mismatch', 'unchanged-missing', 'success', 'retry-success']:
    stage = scratch / mode
    initial = {'country.checksum': country_hash.encode(), 'city.checksum': city_hash.encode()} if mode == 'unchanged-missing' else old
    write_set(stage, initial)
    temp = scratch / (mode + '-temp')
    before = hashes(stage)
    assert stage.resolve().is_relative_to(scratch.resolve()) and temp.resolve().is_relative_to(scratch.resolve())
    environment = {key: value for key, value in os.environ.items() if key.lower() not in ['http_proxy', 'https_proxy', 'all_proxy', 'no_proxy', 'license_key', 'node_options', 'geodatadir', 'geotmpdir']}
    environment.update(GEODATADIR=str(stage), GEOTMPDIR=str(temp), GEOIP_FIXTURE_ROOT=str(scratch), GEOIP_FIXTURE_MODE=mode, GEOIP_FIXTURE_LEDGER=str(output / (mode + '-requests.jsonl')))
    if mode != 'missing-license':
        environment['LICENSE_KEY'] = 'offline-fixture-only'
    command = [runtime, '--require', bundle / 'offline-http.cjs', package / 'scripts/updatedb.js']
    killed = False
    with (output / (mode + '.stdout.txt')).open('wb') as stdout, (output / (mode + '.stderr.txt')).open('wb') as stderr:
        child = subprocess.Popen(command, env=environment, cwd=dashboard, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr)
        try:
            code = child.wait(timeout=3 if mode == 'stall-city' else 10)
        except subprocess.TimeoutExpired:
            child.kill()
            code = child.wait(timeout=5)
            killed = True
    after = hashes(stage)
    record = {'mode': mode, 'exit': code, 'killed_after_deadline': killed, 'process_stopped': child.poll() is not None, 'before': before, 'after': after, 'changed_files': sorted(name for name in set(before) | set(after) if before.get(name) != after.get(name)), 'lookup': lookup(stage), 'active_unchanged': hashes(active) == initial_active}
    records.append(record)
    (output / 'results.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
    print(mode, code, 'changed', record['changed_files'], flush=True)
    assert record['active_unchanged'] and record['process_stopped']
    if mode in ['success', 'retry-success']:
        assert code == 0 and after == expected_hashes, record
    elif mode == 'checksum-mismatch':
        mismatch = {name: hashlib.sha256(value).hexdigest() for name, value in dict(expected, **{'country.checksum': b'0' * 64, 'city.checksum': b'0' * 64}).items()}
        assert code == 0 and after == mismatch, record
    elif mode == 'unchanged-missing':
        assert code == 0 and after == before and record['lookup']['exit'] != 0, record
    elif mode in ['city-503', 'stall-city']:
        assert code != 0 and killed == (mode == 'stall-city')
        assert record['changed_files'] == ['country.checksum', 'geoip-country.dat', 'geoip-country6.dat'], record
    else:
        assert code != 0 and not killed and before == after, record
assert hashes(package) == baseline['package_sha256']
summary = {'passed': True, 'cases': len(records), 'runtime': subprocess.check_output([runtime, '--version']).decode().strip(), 'package_unchanged': True, 'active_unchanged': True, 'processes_stopped': True, 'network_connections': 0, 'scratch_bytes': sum(p.stat().st_size for p in scratch.rglob('*') if p.is_file())}
(output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary), flush=True)
