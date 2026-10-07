from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
records = {}
for name, height in [('legacy', None), ('effective', 100), ('different', 101)]:
    config = {'chainId': 32659, 'homesteadBlock': 0, 'eip150Hash': '0x' + '0' * 64, 'eip155Block': 0, 'eip158Block': 0, 'byzantiumBlock': 0, 'datong': {'period': 15}}
    if height is not None:
        config['suicideTimeLockFixBlock'] = height
    encoded = json.dumps(config, separators=(',', ':'))
    records[name] = {'json': encoded, 'sha256': hashlib.sha256(encoded.encode('utf-8')).hexdigest()}
source = 'package main\n\n'
source += 'var f11ConfigVectors = map[string]struct { JSON string; SHA256 string }{\n'
for name, vector in records.items():
    source += json.dumps(name) + ': {' + json.dumps(vector['json']) + ', ' + json.dumps(vector['sha256']) + '},\n'
source += '}\n'
(HERE / 'config_vectors_test.go').write_text(source, encoding='utf-8', newline='\n')
(HERE / 'config-vectors.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8', newline='\n')
