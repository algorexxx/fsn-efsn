import hashlib
import json
from pathlib import Path

workspace = Path('/mnt/c/Users/Peter/Documents/CODING/fsn-efsn')
evidence = workspace / 'docs/evidence/restart-state-export-2026-09-24'
results = Path('/home/rehearsal/results/restart-state-export-2026-09-24')
artifact = json.loads((workspace / 'tmp/preserved-head-state/identity.json').read_text(encoding='utf-8'))
replay = json.loads((workspace / 'tmp/replay-mainnet-c/replay-identity.json').read_text(encoding='utf-8'))
assert artifact['Config'] == json.loads(replay['SourceConfig'])
assert artifact['Config'] == json.loads(replay['ReplayConfig'])
assert artifact['Genesis'] == replay['SourceGenesis']
assert artifact['Head']['hash'] == replay['SourceHead']
assert artifact['ExecutableHash'] == hashlib.sha256((results / 'export-tests').read_bytes()).hexdigest()
source_hashes = {}
for line in (results / 'identity.txt').read_text(encoding='utf-8').splitlines():
    if '  tests/restart/' not in line:
        continue
    expected, path = line.split('  ', 1)
    preserved_source = evidence / ('writer-' + Path(path).name + '.txt')
    source_path = preserved_source if preserved_source.exists() else workspace / path
    actual = hashlib.sha256(source_path.read_bytes()).hexdigest()
    assert actual == expected, f'source differs from retained build: {path}'
    source_hashes[path] = actual
assert len(source_hashes) == 3
result = {'fullStoredConfigurationMatchesEarlierReplayIdentity': True,
          'genesisAndPreservedHeadMatch': True,
          'exportExecutableMatches': artifact['ExecutableHash'],
          'exportSourceMatchesRetainedBuild': source_hashes}
(evidence / 'identity-cross-check.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print('Matched full stored configuration, genesis, preserved head, export binary and all three extraction source files.')
