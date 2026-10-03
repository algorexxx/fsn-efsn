import copy
import json
from pathlib import Path

bundle = Path(__file__).resolve().parent
comparison = json.loads((bundle / 'attempt-2/comparison.json').read_text(encoding='utf-8'))
incoming = [record for record in comparison['captured']['records'] if record['direction'] == 'incoming' and isinstance(record['message'], dict)]
history = next(record for record in incoming if record['message'].get('emit', [None])[0] == 'history')
rows = []
for count in [1, 10, 100, 714]:
    message = copy.deepcopy(history['message'])
    for block in message['emit'][1]['history']:
        block['transactions'] = [block['transactions'][0]] * count
        block['gasUsed'] = count * 21000 + 288
    encoded = json.dumps(message, separators=(',', ':'), ensure_ascii=False).encode('utf-8') + b'\n'
    rows.append({'transactions_per_block': count, 'blocks': 50, 'gas_used_per_block': count * 21000 + 288, 'application_bytes': len(encoded), 'fits_128_kib': len(encoded) < 131072, 'fits_4_mib': len(encoded) < 4194304})
assert rows[1]['application_bytes'] == history['bytes'] == 66076
largest_block = message['emit'][1]['history'][0]
block_bytes = len(json.dumps(largest_block, separators=(',', ':'), ensure_ascii=False).encode('utf-8'))
result = {'kind': 'Offline byte model only; repeated hash strings are not valid distinct transactions and no modeled report is sent to a server.', 'measured_history_bytes': history['bytes'], 'rows': rows, 'retention_example': {'heights': 2000, 'configured_identities': 8, 'maximum_variants_per_height': 9, 'modeled_block_json_bytes': block_bytes, 'all_variant_json_bytes': 2000 * 9 * block_bytes, 'meaning': 'Serialized block content illustration before wrappers and runtime object overhead; not measured resident memory or a populated cache.'}}
(bundle / 'size-model.json').write_bytes((json.dumps(result, indent=2) + '\n').encode('utf-8'))
print(json.dumps(result, indent=2))
