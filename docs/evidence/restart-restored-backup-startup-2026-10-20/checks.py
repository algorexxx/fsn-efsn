from pathlib import Path
import ast
import hashlib
import json
import re
import worker

here = Path(__file__).resolve().parent
for name in ['worker.py', 'launch.py', 'preflight.py', 'checks.py']:
    ast.parse((here / name).read_text(encoding='utf-8'), filename=name)
profile = worker.read(here / 'profile.json')
source = (worker.RETAINED / 'node/params/config.go').read_text(encoding='utf-8')
mainnet = source.split('MainnetChainConfig = &ChainConfig{', 1)[1].split('// MainnetTrustedCheckpoint', 1)[0]
numeric = {name: int(value.replace('_', '')) for name, value in
           re.findall(r'(\w+):\s+big.NewInt\(([0-9_]+)\)', mainnet)}
assert len(numeric) == 13
for field, value in numeric.items():
    json_name = re.search(r'\b' + field + r'\s+\*big.Int\s+`json:"([^",]+)', source).group(1)
    assert profile['Config'][json_name] == value, field
assert len(profile['Config']) == 16
assert 'DAOForkSupport:      false,' in mainnet and profile['Config']['daoForkSupport'] is False
assert 'EIP150Hash:          common.HexToHash("0x0"),' in mainnet
assert profile['Config']['eip150Hash'] == '0x' + '0' * 64
assert re.search(r'DaTong: &DaTongConfig\{\s+Period: 15,', mainnet)
assert profile['Config']['datong'] == {'period': 15}
genesis = '0xc2422b1d9d16331be2a5b207c0783027d4419498003f729f4b9e9c5c1838623a'
assert profile['Genesis'] == genesis
assert profile['Anchor'] == {'GenesisHash': genesis, 'ChainID': 32659, 'Number': 15130080,
                             'Hash': worker.read(here / 'expected-endpoint.json')['Hash']}
prior = here.parent / 'restart-restored-startup-pruning-v2-2026-10-09/qualification'
output = (prior / 'restored.stdout.txt').read_text(encoding='utf-8')
errors = (prior / 'restored.stderr.txt').read_text(encoding='utf-8')
record = worker.read(prior / 'run.json')
want = dict(record['expected']['parent'], mining=False, autoBuy=False)
worker.parse_cli(output, errors, want)
cases = {
    'wrong_head': (output.replace('"head":129', '"head":128'), errors),
    'missing_readonly_guard': (output, errors.replace('readonly=true', 'readonly=false')),
    'missing_shutdown_write': (output, re.sub(r'^.*Writing cached state to disk.*\n', '', errors, count=1, flags=re.M)),
    'failed_state_commit': (output, errors + '\nFailed to commit recent state trie\n'),
}
for name, (out, err) in cases.items():
    try:
        worker.parse_cli(out, err, want)
    except (AssertionError, ValueError):
        continue
    raise AssertionError(name + ' incorrectly accepted')
worker.save('controls.json', {'pass': True, 'checked': worker.now(), 'profile_matches_pinned_source': True,
                              'sealed_pruning_log_accepted': True, 'rejected_log_mutations': list(cases),
                              'database_opened': False})
print('Source-derived profile and retained-log acceptance controls passed')
