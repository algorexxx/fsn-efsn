from pathlib import Path
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
CANDIDATE = HERE.parent / 'restart-state-rollback-candidate-2026-10-07'
PORTED = HERE.parent / 'restart-state-tests-2026-10-07/verified'
FOLLOWUP = HERE.parent / 'restart-state-rollback-followup-2026-10-07'
EXECUTION = HERE.parent / 'restart-state-rollback-execution-2026-10-07'
RUN = Path('/home/rehearsal/results/restart-state-rollback-persistence-v2-2026-10-07')
TOOLCHAIN = Path('/home/rehearsal/results/restart-release-selection-2026-10-04/toolchain/go')
CACHE = Path('/home/rehearsal/results/restart-release-selection-2026-10-04/repeat-cache')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


if __name__ == '__main__':
    assert not RUN.exists(), 'Use a fresh directory; preserve prior evidence.'
    assert os.getuid() == 1000
    assert len(sys.argv) == 2 and sys.argv[1].startswith('net:[') and os.readlink('/proc/self/ns/net') != sys.argv[1]
    capacity = {p: shutil.disk_usage(p).free for p in ['/home/rehearsal/results', '/mnt/d']}
    assert capacity['/home/rehearsal/results'] > 30 * 1024**3 and capacity['/mnt/d'] > 60 * 1024**3
    previous = {}
    for name in ['restart-state-tests-2026-10-07', FOLLOWUP.name, CANDIDATE.name, 'restart-state-rollback-integration-2026-10-07', 'restart-state-rollback-cli-2026-10-07', EXECUTION.name, 'restart-state-rollback-persistence-2026-10-07']:
        directory = HERE.parent / name
        for line in (directory / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
            expected, relative = line.split(None, 1)
            assert sha(directory / relative) == expected, (name, relative)
        previous[name] = sha(directory / 'SHA256SUMS')
    manifest = json.loads((CANDIDATE / 'base-inputs.json').read_text(encoding='utf-8'))
    tree = manifest['trees']['recovery']
    source = Path(tree['path'])
    for name in ['go.mod', 'go.sum']:
        assert sha(source / name) == tree[name]
    for relative, entry in manifest['files'].items():
        if 'recovery' in entry['trees']:
            assert sha(source / relative) == entry['sha256'], relative
    source_paths = ['go.mod', 'go.sum', 'core/state/statedb.go', 'core/state/state_object.go', 'core/state/journal.go', 'core/vm/evm.go', 'core/vm/instructions.go', 'core/vm/interface.go', 'core/vm/noop.go', 'core/vm/gas_table.go', 'core/vm/operations_acl.go', 'core/vm/eips.go', 'core/vm/jump_table.go', 'params/config.go', 'params/protocol_params.go', 'core/state_processor.go', 'core/state_transition.go', 'internal/recovery/chain.go', 'rlp/decode.go']
    source_hashes = {p: sha(source / p) for p in source_paths}
    subprocess.run([str(TOOLCHAIN / 'bin/gofmt'), '-w', *map(str, HERE.rglob('*.go'))], check=True)
    RUN.mkdir()
    (RUN / 'tmp').mkdir()
    env = os.environ.copy()
    for key in ['GODEBUG', 'GOEXPERIMENT', 'GOENV', 'GOFLAGS', 'GOOS', 'GOARCH', 'F11_ORIGINAL_REGRESSION']:
        env.pop(key, None)
    env.update(PATH=str(TOOLCHAIN / 'bin') + ':/usr/bin:/bin', GOENV='off', GOTOOLCHAIN='local', GOWORK='off', GOPROXY='off', GOSUMDB='off', GOFLAGS='-mod=readonly', CGO_ENABLED='1', GOAMD64='v1', GOMAXPROCS='2', GOCACHE=str(CACHE), GOMODCACHE='/home/rehearsal/go/pkg/mod', GOTMPDIR=str(RUN / 'tmp'), TMPDIR=str(RUN / 'tmp'))
    record = {'started': now(), 'capacity_bytes': capacity, 'uid': os.getuid(), 'network_namespace': os.readlink('/proc/self/ns/net'), 'parent_network_namespace': sys.argv[1], 'links': subprocess.check_output(['ip', '-brief', 'link'], text=True), 'source': str(source), 'candidate_commit': '8357c5fe', 'previous_manifest_sha256': previous, 'source_sha256': source_hashes, 'go_env': json.loads(subprocess.check_output(['go', 'env', '-json'], cwd=source, env=env, text=True)), 'runs': []}
    unexpected = False
    cases = [('baseline', False, '^TestF11TransactionPersistence$', '', 0), ('candidate', True, '^TestF11TransactionPersistence$', '', 0)]
    for name, candidate, pattern, activation, want_exit in cases:
        replacements = {}
        if candidate:
            replacements.update(json.loads((CANDIDATE / 'qualification-v2/recovery-overlay.json').read_text(encoding='utf-8'))['Replace'])
        for filename in ['state_test.go', 'statedb_test.go', 'iterator_test.go', 'sync_test.go', 'suicide_test.go']:
            path = EXECUTION / 'candidate' / filename if candidate and filename in ['statedb_test.go', 'suicide_test.go'] else PORTED / filename
            replacements[str(source / 'core/state' / filename)] = str(path)
        replacements[str(source / 'core/state/suicide_evm_test.go')] = str(FOLLOWUP / 'suicide_evm_test.go')
        for filename in ['inspect_state_test.go', 'transaction_persistence_test.go']:
            replacements[str(source / 'core/state' / ('f11_' + filename))] = str(HERE / filename)
        for filename in ['evm_adapter_test.go']:
            replacements[str(source / 'core/state' / ('f11_' + filename))] = str(EXECUTION / ('candidate' if candidate else 'baseline') / filename)
        overlay_path = RUN / (name + '-overlay.json')
        overlay_path.write_text(json.dumps({'Replace': replacements}, indent=2) + '\n', encoding='utf-8')
        command = ['timeout', '--kill-after=20s', '7m', 'go', 'test', '-overlay=' + str(overlay_path), '-race', '-p=2', '-count=1', '-timeout=2m', '-run', pattern, '-v', './core/state']
        command_env = env.copy()
        command_env['F11_ORIGINAL_REGRESSION'] = activation
        run = {'name': name, 'candidate': candidate, 'activation_environment': activation, 'expected_exit': want_exit, 'started': now(), 'argv': command, 'overlay_input_sha256': {k: sha(Path(v)) for k, v in replacements.items()}}
        with (RUN / (name + '.txt')).open('w', encoding='utf-8') as output:
            result = subprocess.run(command, cwd=source, env=command_env, stdout=output, stderr=subprocess.STDOUT)
        run.update(exit=result.returncode, finished=now())
        record['runs'].append(run)
        (RUN / 'run.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
        print(name, result.returncode, flush=True)
        if result.returncode != want_exit:
            unexpected = True
            break
    for relative, expected in source_hashes.items():
        assert sha(source / relative) == expected, relative
    record.update(finished=now(), unexpected_result=unexpected, remaining_bytes=shutil.disk_usage('/home/rehearsal/results').free)
    (RUN / 'run.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    output = HERE / 'qualification'
    output.mkdir()
    for path in RUN.iterdir():
        if path.is_file():
            shutil.copyfile(path, output / path.name)
    sys.exit(1 if unexpected else 0)
