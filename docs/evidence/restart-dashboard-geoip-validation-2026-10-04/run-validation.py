import hashlib
import ipaddress
import json
import struct
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
output = bundle / 'validation-1'
output.mkdir(exist_ok=False)
scratch = root / 'tmp/dashboard-geoip-validation-1'
scratch.mkdir(exist_ok=False)
runtime = '/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/tmp/dashboard-runtime-review/v24.21.0/node'
wsl = ['wsl', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--']


def linux(path):
    return '/mnt/' + path.drive[0].lower() + path.as_posix()[2:]


def hashes(directory):
    return {p.name: hashlib.file_digest(p.open('rb'), 'sha256').hexdigest() for p in directory.iterdir() if p.is_file()}


def run(name, command, expected):
    with (output / (name + '.stdout.txt')).open('wb') as stdout, (output / (name + '.stderr.txt')).open('wb') as stderr:
        result = subprocess.run(command, cwd=dashboard, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=60, creationflags=subprocess.CREATE_NO_WINDOW)
    assert result.returncode == expected, name
    print(name, result.returncode, flush=True)
    return result.returncode


fixture = json.loads((dashboard / 'test/fixtures/geoip-data.json').read_text(encoding='utf-8'))
valid = scratch / 'valid'
valid.mkdir()
for name, value in fixture.items():
    (valid / name).write_bytes(bytes.fromhex(value['hex']))
precision = scratch / 'precision'
precision.mkdir()
for name, value in fixture.items():
    (precision / name).write_bytes(bytes.fromhex(value['hex']))
names = (precision / 'geoip-city-names.dat').read_bytes()
second = bytearray(names)
second[:2] = b'SE'
(precision / 'geoip-city-names.dat').write_bytes(names + second)
country6 = bytearray()
city6 = bytearray()
for index, (ip, country) in enumerate([('2001:db8::1', b'NO'), ('2001:db8::2', b'SE')]):
    address = ipaddress.ip_address(ip).packed
    country6.extend(address + address + country)
    city6.extend(address + address + struct.pack('>Iiii', index, 599139, 107522, 10))
(precision / 'geoip-country6.dat').write_bytes(country6)
(precision / 'geoip-city6.dat').write_bytes(city6)
bundled = dashboard / 'node_modules/geoip-lite/data'
before = {'valid': hashes(valid), 'precision': hashes(precision), 'bundled': hashes(bundled)}
cli = linux(dashboard / 'deploy/validate-geoip.cjs')
run('syntax-module', wsl + [runtime, '--check', linux(dashboard / 'lib/geoip-dataset.js')], 0)
run('syntax-cli', wsl + [runtime, '--check', cli], 0)
run('valid', wsl + [runtime, cli, linux(valid), '204'], 0)
run('precision', wsl + [runtime, cli, linux(precision), '1000'], 1)
run('bundled', wsl + [runtime, cli, linux(bundled), '134217728'], 1)
run('reader', wsl + ['env', 'GEODATADIR=' + linux(precision), runtime, linux(bundle / 'probe-reader.cjs')], 0)
actual = json.loads((output / 'reader.stdout.txt').read_text(encoding='utf-8'))
expected_countries = ['NO', 'SE']
observed_countries = [row['geo']['country'] for row in actual]
assert observed_countries == ['NO', 'NO'] and observed_countries != expected_countries
result = json.loads((output / 'valid.stdout.txt').read_text(encoding='utf-8'))
expected_files = {name: {key: value[key] for key in ['bytes', 'records', 'sha256']} for name, value in fixture.items()}
assert result['files'] == expected_files
assert (output / 'valid.stderr.txt').read_bytes() == b''
assert (output / 'precision.stdout.txt').read_bytes() == (output / 'bundled.stdout.txt').read_bytes() == b''
assert "IPv6 bounds exceed the reader's 64-bit precision" in (output / 'precision.stderr.txt').read_text(encoding='utf-8')
assert "IPv6 bounds exceed the reader's 64-bit precision" in (output / 'bundled.stderr.txt').read_text(encoding='utf-8')
after = {'valid': hashes(valid), 'precision': hashes(precision), 'bundled': hashes(bundled)}
assert after == before
summary = {'passed': True, 'valid_fixture_accepted': True, 'narrow_ipv6_rejected': True, 'bundled_dataset_rejected': True, 'reader_expected_countries_from_encoded_records': expected_countries, 'reader_observed_countries': observed_countries, 'all_data_unchanged': True, 'data_sha256': after, 'runtime': '24.21.0', 'public_connections': 0, 'activation_performed': False}
(output / 'result.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
print(json.dumps({key: value for key, value in summary.items() if key != 'data_sha256'}, indent=2))
