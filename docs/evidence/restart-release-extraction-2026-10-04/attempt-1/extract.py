import difflib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

root = Path(__file__).resolve().parents[3]
out = Path(__file__).resolve().parent
baseline = 'c5f0174d88ab2b9c3086c6a9cc9ccf38a072992f'
candidate = '6ecc753f00f6c6ec9ee7ad3855f2f8ff71f1f711'
scratch = root / 'tmp/release-extraction-2026-10-04'
scratch.mkdir(parents=True, exist_ok=False)


def git(*args):
    return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True).stdout


def content(ref, path):
    return git('show', ref + ':' + path)


node_owners = {
    'cmd/efsn/main.go': ['P4'], 'cmd/utils/flags.go': ['P12'],
    'common/autobuy.go': ['P4'], 'common/fsntypes.go': ['P4'],
    'consensus/datong/consensus.go': ['P2', 'P9'], 'consensus/datong/snapshot.go': ['P16'],
    'core/blockchain.go': ['P1', 'P4', 'P5', 'P6', 'P7', 'P9'],
    'core/genesis.go': ['P1'], 'core/headerchain.go': ['P1', 'P6', 'P9'],
    'core/rawdb/database.go': ['P7'], 'core/rawdb/freezer_table.go': ['P7'],
    'core/restart_anchor.go': ['P1'], 'eth/api.go': ['P4'],
    'eth/api_backend.go': ['P1', 'P4'], 'eth/backend.go': ['P1'],
    'eth/handler.go': ['P1', 'P4'], 'eth/sync.go': ['P1'],
    'ethdb/leveldb/leveldb.go': ['P8'], 'ethstats/ethstats.go': ['P17'],
    'internal/ethapi/api_fsn.go': ['P4'], 'internal/ethapi/autobuy.go': ['P4'],
    'internal/ethapi/backend.go': ['P4'], 'les/api_backend.go': ['P4'],
    'light/lightchain.go': ['P1'], 'miner/worker.go': ['P1', 'P3'],
    'p2p/discover/bootstrap.go': ['P12'], 'p2p/discover/database.go': ['P13'],
    'p2p/discover/node.go': ['P12'],
    'p2p/discover/table.go': ['P10', 'P11', 'P12', 'P13', 'P14', 'P15'],
    'p2p/discover/udp.go': ['P10', 'P11', 'P12'], 'p2p/server.go': ['P12'],
    'params/config.go': ['P1'], 'params/restart_anchor.go': ['P1'],
}
changed = git('diff', '--name-only', baseline, candidate).decode('utf-8').splitlines()
before_paths = set(git('ls-tree', '-r', '--name-only', baseline).decode('utf-8').splitlines())
runtime = [p for p in changed if p.endswith('.go') and not p.endswith('_test.go') and not p.startswith('tests/')]
recovery = [p for p in runtime if p.startswith(('cmd/fsn-recovery/', 'internal/recovery/'))]
observer = [p for p in runtime if p.startswith(('cmd/fsn-observe/', 'internal/observe/'))]
assert set(runtime) == set(node_owners) | set(recovery) | set(observer), 'unclassified runtime source'
assert content(baseline, 'go.mod') == content(candidate, 'go.mod')
assert content(baseline, 'go.sum') == content(candidate, 'go.sum')
old = {p: content(baseline, p) if p in before_paths else b'' for p in node_owners}
node = {p: content(candidate, p) for p in node_owners}
consensus = 'consensus/datong/consensus.go'
full_consensus = node[consensus]
start = full_consensus.index(b'// SigningPayload returns ')
end = full_consensus.index(b'func sigRlp(', start)
accessor = full_consensus[start:end]
assert accessor.count(b'func ') == 1 and b'func SigningPayload(' in accessor
node[consensus] = full_consensus[:start] + full_consensus[end:]
flags = 'cmd/utils/flags.go'
v4_start = node[flags].index(b'func setBootstrapNodes(')
v4_end = node[flags].index(b'func setBootstrapNodesV5(', v4_start)
v4 = node[flags][v4_start:v4_end]
for flag in ['BootnodesV4Flag', 'BootnodesFlag']:
    needle = f'urls = SplitAndTrim(ctx.String({flag}.Name))'.encode()
    replacement = f'urls = strings.Split(ctx.String({flag}.Name), ",")'.encode()
    assert v4.count(needle) == 1
    v4 = v4.replace(needle, replacement)
node[flags] = node[flags][:v4_start] + v4 + node[flags][v4_end:]


def write_patch(name, previous, next_files):
    patch = []
    files = []
    for path in sorted(next_files):
        a, b = previous.get(path, b''), next_files[path]
        assert a != b and b.endswith(b'\n')
        patch.append(f'diff --git a/{path} b/{path}\n')
        if not a:
            patch.append('new file mode 100644\n')
        patch.extend(difflib.unified_diff(a.decode('utf-8').splitlines(True), b.decode('utf-8').splitlines(True), fromfile='a/' + path if a else '/dev/null', tofile='b/' + path))
        files.append({'path': path, 'before_sha256': hashlib.sha256(a).hexdigest() if a else None, 'after_sha256': hashlib.sha256(b).hexdigest(), 'review_ids': node_owners.get(path, ['recovery-tool']) if name == '01-node.patch' else ['O1'] if name == '02-optional-bootstrap-trim.patch' else ['recovery-tool']})
    data = ''.join(patch).encode('utf-8')
    (out / name).write_bytes(data)
    return {'patch': name, 'sha256': hashlib.sha256(data).hexdigest(), 'files': files}


patches = [write_patch('01-node.patch', old, node)]
patches.append(write_patch('02-optional-bootstrap-trim.patch', {flags: node[flags]}, {flags: content(candidate, flags)}))
tool_sources = {p: content(candidate, p) for p in recovery}
tool_sources[consensus] = full_consensus
patches.append(write_patch('03-recovery-tool.patch', {consensus: node[consensus]}, tool_sources))
excluded = [p for p in changed if p not in runtime and not p.startswith(('docs/', 'tests/')) and not p.endswith('_test.go')]
manifest = {'baseline': baseline, 'candidate': candidate, 'patches': patches, 'excluded_runtime': observer, 'changed_path_count': len(changed), 'node_file_count': len(node), 'recovery_file_count': len(tool_sources), 'excluded_packaging': excluded, 'test_evidence_path_count': sum(p.startswith(('docs/', 'tests/')) or p.endswith('_test.go') for p in changed)}
(out / 'selection.json').write_bytes((json.dumps(manifest, indent=2) + '\n').encode('utf-8'))
(scratch / 'baseline.tar').write_bytes(git('archive', '--format=tar', baseline))
overlay = {}
for path in git('ls-tree', '-r', '--name-only', candidate, 'tests/restart').decode('utf-8').splitlines():
    if path.endswith('_test.go') and not Path(path).name.startswith('observer_'):
        data = content(candidate, path)
        if b'internal/observe' not in data:
            overlay[path] = data
for path in changed:
    if path.endswith('_test.go') and path.startswith(('params/', 'consensus/datong/', 'ethdb/leveldb/')):
        overlay[path] = content(candidate, path)
fixture = 'docs/evidence/restart-2026-09-23/responses.json'
overlay[fixture] = content(candidate, fixture)
with tarfile.open(scratch / 'tests.tar', 'w') as archive:
    for path, data in sorted(overlay.items()):
        info = tarfile.TarInfo(path)
        info.size, info.mode, info.mtime = len(data), 0o644, 0
        archive.addfile(info, io.BytesIO(data))
records = {name: hashlib.sha256((scratch / name).read_bytes()).hexdigest() for name in ['baseline.tar', 'tests.tar']}
records['test_overlay'] = {p: hashlib.sha256(data).hexdigest() for p, data in sorted(overlay.items())}
(out / 'input-archives.json').write_bytes((json.dumps(records, indent=2) + '\n').encode('utf-8'))
print(json.dumps({'node_files': len(node), 'recovery_files_including_accessor': len(tool_sources), 'observer_files_excluded': len(observer), 'test_overlay_files': len(overlay), 'input_archive_bytes': sum((scratch / name).stat().st_size for name in ['baseline.tar', 'tests.tar'])}))
