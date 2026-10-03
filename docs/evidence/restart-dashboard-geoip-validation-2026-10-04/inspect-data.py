import hashlib
import json
import struct
from pathlib import Path

bundle = Path(__file__).resolve().parent
data = bundle.parents[2] / 'tmp/fsn-stats-auth/node_modules/geoip-lite/data'
names = (data / 'geoip-city-names.dat').read_bytes()
records = len(names) // 88
result = {'location_records': records, 'names_sha256': hashlib.sha256(names).hexdigest(), 'invalid_country_records': [], 'invalid_eu_records': [], 'invalid_utf8_fields': 0, 'ranges': {}}
for index in range(records):
    record = names[index * 88:(index + 1) * 88]
    if record[:2] != b'\0\0' and not all(65 <= value <= 90 for value in record[:2]):
        result['invalid_country_records'].append(index)
    if record[9:10] not in [b'0', b'1', b'\0']:
        result['invalid_eu_records'].append(index)
    for start, end in [(2, 5), (10, 42), (42, 88)]:
        try:
            record[start:end].split(b'\0')[0].decode('utf-8', errors='strict')
        except UnicodeDecodeError:
            result['invalid_utf8_fields'] += 1
for filename, width, size, location in [('geoip-country.dat', 4, 10, False), ('geoip-country6.dat', 16, 34, False), ('geoip-city.dat', 4, 24, True), ('geoip-city6.dat', 16, 48, True)]:
    content = (data / filename).read_bytes()
    counts = {'bytes': len(content), 'records': len(content) // size, 'reversed': 0, 'overlapping': 0, 'overlapping_upper64': 0, 'invalid_location': 0, 'no_location': 0, 'invalid_coordinates': 0, 'negative_area': 0}
    previous = -1
    previous64 = -1
    for offset in range(0, len(content), size):
        first = int.from_bytes(content[offset:offset + width], 'big')
        last = int.from_bytes(content[offset + width:offset + 2 * width], 'big')
        counts['reversed'] += first > last
        counts['overlapping'] += first <= previous
        if width == 16:
            counts['overlapping_upper64'] += (first >> 64) <= previous64
            previous64 = last >> 64
        previous = last
        if location:
            reference, latitude, longitude, area = struct.unpack_from('>Iiii', content, offset + width * 2)
            counts['no_location'] += reference == 0xffffffff
            counts['invalid_location'] += reference != 0xffffffff and reference >= records
            counts['invalid_coordinates'] += abs(latitude) > 900000 or abs(longitude) > 1800000
            counts['negative_area'] += area < 0
    result['ranges'][filename] = counts
(bundle / 'bundled-inspection.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
