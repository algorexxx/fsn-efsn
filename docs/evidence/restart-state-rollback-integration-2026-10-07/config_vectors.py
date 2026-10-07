from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
records = {}
for name, height in [('legacy', None), ('effective', 100), ('different', 101)]:
    config = {'chainId': 32659, 'eip150Hash': '0x' + '0' * 64, 'datong': {'period': 15}}
    if height is not None:
        config['suicideTimeLockFixBlock'] = height
    encoded = json.dumps(config, separators=(',', ':'))
    records[name] = {'json': encoded, 'sha256': hashlib.sha256(encoded.encode('utf-8')).hexdigest()}
source = 'package recovery\n\n'
source += 'const f11ExpectedConfigJSON = ' + json.dumps(records['effective']['json']) + '\n'
for constant, name in [('f11ExpectedConfigSHA256', 'effective'), ('f11LegacyConfigSHA256', 'legacy'), ('f11DifferentConfigSHA256', 'different')]:
    source += 'const ' + constant + ' = ' + json.dumps(records[name]['sha256']) + '\n'
(HERE / 'config_vectors_test.go').write_text(source, encoding='utf-8', newline='\n')
(HERE / 'config-vectors.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8', newline='\n')
