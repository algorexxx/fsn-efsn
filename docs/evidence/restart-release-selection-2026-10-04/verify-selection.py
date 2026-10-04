import hashlib
import json
from pathlib import Path
import subprocess

evidence = Path(__file__).resolve().parent
root = evidence.parents[2]
work = Path('/home/rehearsal/results/restart-release-selection-2026-10-04')
selection = json.loads((evidence / 'selection.json').read_text(encoding='utf-8'))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

references = selection['node_patch_order'] + selection['test_only_corrections'] + [
    selection[name] for name in ['extraction_selection', 'hunk_map', 'recovery_addition',
                               'node_inventory', 'recovery_inventory', 'toolchain']
]
for item in references:
    assert digest(root / item['path']) == item['sha256'], item['path']
assert selection['launch_approved'] is False
decisions = {item['id']: item for item in selection['review_decisions']}
assert all(decisions[f'P{i}']['decision'] == 'include' for i in range(1, 18))
assert decisions['O1']['decision'] == 'exclude' and decisions['B1']['decision'] == 'include'
hunks = json.loads((root / selection['hunk_map']['path']).read_text(encoding='utf-8'))['hunks']
assert len(hunks) == 109
for hunk in hunks:
    for review_id in hunk['review_ids']:
        assert {'path': hunk['path'], 'hunk': hunk['hunk']} in decisions[review_id]['hunks']
compiler = json.loads((evidence / 'selected-toolchain.json').read_text(encoding='utf-8'))
assert digest(work / 'toolchain' / compiler['filename']) == compiler['sha256']
assert compiler['version'] == 'go1.27.1'

inventories = {}
for name, folder in [('node', 'source'), ('recovery', 'repeat')]:
    expected = json.loads((evidence / f'selected-{name}-inventory.json').read_text(encoding='utf-8'))
    if name == 'recovery':
        path = 'p2p/rlpx_test.go'
        expected[path] = hashlib.sha256((root / path).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
    actual = {p.relative_to(work / folder).as_posix(): digest(p)
              for p in (work / folder).rglob('*') if p.is_file()}
    assert expected == actual, name
    inventories[name] = {'files': len(actual), 'go_files': sum(p.endswith('.go') for p in actual)}

compatibility = json.loads((evidence / 'build-compatibility.json').read_text(encoding='utf-8'))
for item in compatibility['files']:
    actual = hashlib.sha256((root / item['path']).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
    assert actual == item['after_sha256'], item['path']
for path in ['cmd/efsn/main.go', 'internal/debug/flags.go', 'p2p/rlpx_test.go']:
    data = (root / path).read_bytes().replace(b'\r\n', b'\n')
    formatted = subprocess.check_output([str(work / 'toolchain/go/bin/gofmt')], input=data)
    assert formatted == data, path
for runner in evidence.glob('*.sh'):
    subprocess.run(['bash', '-n', str(runner)], check=True)

expected_exits = {
    'build-node': 1, 'compatibility-build': 0, 'compatibility': 0,
    'repeat-build': 0, 'recovery-build': 0, 'continuation': 0,
    'module-graph-recheck': 1, 'finding-parse': 1, 'finding-forward': 1,
    'finding-handshake': 1, 'handshake-loopback-before': 1, 'handshake-loopback-after': 0,
}
for name, code in expected_exits.items():
    assert int((evidence / f'{name}-exit.txt').read_text(encoding='utf-8')) == code, name
assert 'invalid reference to runtime.stopTheWorld' in (evidence / 'build-node.txt').read_text(encoding='utf-8')
assert 'test timed out after 1m30s' in (evidence / 'finding-handshake.txt').read_text(encoding='utf-8')
assert 'message size mismatch: got 2, want 1' in (evidence / 'handshake-loopback-before.txt').read_text(encoding='utf-8')
assert '--- PASS: TestProtocolHandshake' in (evidence / 'handshake-loopback-after.txt').read_text(encoding='utf-8')
assert 'WARNING: DATA RACE' not in (evidence / 'handshake-loopback-after.txt').read_text(encoding='utf-8')
assert 'github.com/fjl/memsize' not in (evidence / 'selected-build-info.txt').read_text(encoding='utf-8')
assert 'Go Version: go1.27.1' in (evidence / 'cli-version.txt').read_text(encoding='utf-8')
binaries = {name: digest(work / 'bin' / name) for name in ['efsn', 'efsn-repeat', 'fsn-recovery']}
assert binaries['efsn'] == binaries['efsn-repeat']
for name, manifest in [('efsn', 'selected-binary.sha256'), ('fsn-recovery', 'recovery-binary.sha256')]:
    assert (evidence / manifest).read_text(encoding='utf-8').split()[0] == binaries[name]
acceptance = {
    'selection_verified': True,
    'inventories': inventories,
    'binary_sha256': binaries,
    'same_host_clean_source_and_cache_repeatability': True,
    'node_cli_version_and_help': 'pass',
    'separate_recovery_build': 'pass',
    'corrected_handshake_race_test': 'pass',
    'retained_failures': expected_exits,
    'remaining_network_fixture_repairs': ['TestParseNode', 'TestForwardCompatibility'],
    'historical_compatibility_claim': False,
    'full_suite_pass_claim': False,
    'dependency_security_approval': False,
    'independent_review_approval': False,
    'launch_approved': False,
}
(evidence / 'acceptance.json').write_text(json.dumps(acceptance, indent=2) + '\n', encoding='utf-8')
print(json.dumps(acceptance, indent=2))
