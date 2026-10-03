import ipaddress
import json
import struct
from pathlib import Path

bundle = Path(__file__).resolve().parent
data = bundle.parents[2] / 'tmp/fsn-stats-auth/node_modules/geoip-lite/data'
names = (data / 'geoip-city-names.dat').read_bytes()
result = {}
for filename, size in [('geoip-country6.dat', 34), ('geoip-city6.dat', 48)]:
    content = (data / filename).read_bytes()
    previous = None
    examples = []
    counts = {'start_descends': 0, 'end_descends': 0, 'lower64_nonzero': 0, 'full_overlap_different_result': 0, 'upper64_overlap_different_result': 0}
    for index in range(len(content) // size):
        record = content[index * size:(index + 1) * size]
        first = int.from_bytes(record[:16], 'big')
        last = int.from_bytes(record[16:32], 'big')
        location = struct.unpack_from('>I', record, 32)[0] * 88 if size == 48 else 0
        value = record[32:] if size == 34 else names[location:location + 88] + record[36:]
        counts['lower64_nonzero'] += bool(first & ((1 << 64) - 1) or last & ((1 << 64) - 1))
        if previous is not None:
            counts['start_descends'] += first < previous['first']
            counts['end_descends'] += last < previous['last']
            counts['full_overlap_different_result'] += first <= previous['last'] and value != previous['value']
            counts['upper64_overlap_different_result'] += (first >> 64) <= (previous['last'] >> 64) and value != previous['value']
            if first <= previous['last'] and len(examples) < 3:
                examples.append({'previous_index': index - 1, 'previous_first': str(ipaddress.IPv6Address(previous['first'])), 'previous_last': str(ipaddress.IPv6Address(previous['last'])), 'index': index, 'first': str(ipaddress.IPv6Address(first)), 'last': str(ipaddress.IPv6Address(last)), 'different_result': value != previous['value']})
        previous = {'first': first, 'last': last, 'value': value}
    result[filename] = {'counts': counts, 'examples': examples}
(bundle / 'ipv6-ordering.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
