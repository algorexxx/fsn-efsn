import hashlib
import ipaddress
import json
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
scratch = root / 'tmp/dashboard-geoip-reader'
source = json.loads((scratch / 'upstream/source-data/GeoLite2-City-Test.json').read_text(encoding='utf-8'))
networks = [(ipaddress.ip_network(cidr), value) for row in source for cidr, value in row.items()]
networks.sort(key=lambda pair: pair[0].prefixlen, reverse=True)
addresses = set()
for network, value in networks:
    for number in [int(network.network_address) - 1, int(network.network_address), (int(network.network_address) + int(network.broadcast_address)) // 2, int(network.broadcast_address), int(network.broadcast_address) + 1]:
        if 0 <= number < 2 ** network.max_prefixlen:
            addresses.add(str(network.network_address.__class__(number)))
cases = []
for text in sorted(addresses):
    address = ipaddress.ip_address(text)
    expected = next((value for network, value in networks if address.version == network.version and address in network), None)
    variants = [text]
    if address.version == 6:
        variants.append(address.exploded.upper())
    else:
        variants.extend(['::ffff:' + text, '::FFFF:' + format(int(address) >> 16, 'x') + ':' + format(int(address) & 65535, 'x')])
    cases.extend({'ip': variant, 'expected': expected} for variant in variants)
precision_networks = list(ipaddress.summarize_address_range(ipaddress.IPv6Address('::1:ffff:ffff'), ipaddress.IPv6Address('::2:0:59')))
precision = []
for number in range(int(ipaddress.IPv6Address('::1:ffff:fffe')), int(ipaddress.IPv6Address('::2:0:5a')) + 1):
    address = ipaddress.IPv6Address(number)
    network = next((network for network in precision_networks if address in network), None)
    expected = {'ip': str(network.network_address)} if network else None
    precision.extend({'ip': variant, 'expected': expected} for variant in [str(address), address.exploded.upper()])
value = {'source_networks': len(networks), 'city': cases, 'precision': precision}
path = scratch / 'expected.json'
path.write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
summary = {'source_networks': len(networks), 'city_cases': len(cases), 'precision_cases_per_record_size': len(precision), 'expected_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'expected_bytes': path.stat().st_size}
(bundle / 'expectations.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, indent=2))
