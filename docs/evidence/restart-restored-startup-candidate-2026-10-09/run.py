from pathlib import Path
import datetime
import difflib
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUN = Path('/home/rehearsal/results') / HERE.name
PRIOR = HERE.parent / 'restart-ticket-encoder-candidate-v2-2026-10-08'
SOURCE = Path('/home/rehearsal/results') / PRIOR.name / 'node'
GO = Path('/home/rehearsal/results/restart-release-selection-2026-10-04/toolchain/go/bin/go')
CASES = {'absent': 'existing database required', 'empty': 'existing database required', 'wrong_genesis': 'genesis mismatch', 'wrong_chain_id': 'stored configuration mismatch', 'wrong_fork': 'stored configuration mismatch', 'missing_datong': 'missing DaTong configuration', 'missing_header': 'missing persisted', 'missing_body': 'missing or corrupt head block', 'missing_state': 'head state unavailable', 'wrong_ticket_commitment': 'ticket storage commitment mismatch', 'genesis_head': 'not a restored canonical block', 'wrong_anchor': 'hash mismatch', 'invalid_anchor_identity': 'network identity mismatch', 'missing_canonical_head': 'inconsistent canonical index', 'fast_sync': 'full sync required'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob('*')) if p.is_file() and '.f12-probe' not in p.parts}


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def capacity():
    return {p: shutil.disk_usage(p).free for p in ['/home/rehearsal/results', '/mnt/d']}


def save():
    (RUN / 'run.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')


def execute(name, argv, env, cwd, expected_error=None):
    free = capacity()
    assert free['/home/rehearsal/results'] > 20 * 1024**3 and free['/mnt/d'] > 50 * 1024**3
    entry = {'name': name, 'argv': argv, 'cwd': str(cwd), 'started': now(), 'free_bytes': free}
    with (RUN / (name + '.stdout.txt')).open('wb') as output, (RUN / (name + '.stderr.txt')).open('wb') as errors:
        entry['exit'] = subprocess.run(argv, cwd=cwd, env=env, stdout=output, stderr=errors).returncode
    entry['finished'] = now()
    record['commands'].append(entry)
    save()
    print(name, entry['exit'], flush=True)
    text = (RUN / (name + '.stdout.txt')).read_text(encoding='utf-8') + (RUN / (name + '.stderr.txt')).read_text(encoding='utf-8')
    if expected_error is None:
        assert entry['exit'] == 0, name
    else:
        assert entry['exit'] == 1 and expected_error in text, (name, expected_error)
        assert 'RESTOREDCLI ' not in text and 'Writing default main-net genesis' not in text
    return text


def cli(name, directory, env, extra, sync='full', expected_error=None):
    args = ['timeout', '--kill-after=10s', '45s', str(RUN/'bin/efsn'), '--config', str(RUN/'profile.toml'), '--datadir', str(directory), '--syncmode', sync, '--networkid', '32659', '--cache', '64', '--maxpeers', '0', '--port', '0', '--nat', 'none', '--nodiscover', '--v5disc=false', '--ipcdisable', '--authrpc.port', '0', '--mine=false', '--autobt=false', '--usb=false']
    return execute(name, args + extra, env, RUN/'node', expected_error)


if __name__ == '__main__':
    assert not RUN.exists() and not (HERE / 'qualification').exists()
    assert os.getuid() == 1000 and len(sys.argv) == 2
    namespace = os.readlink('/proc/self/ns/net')
    assert sys.argv[1] != namespace
    links = subprocess.check_output(['ip', '-brief', 'link'], text=True)
    assert len(links.splitlines()) == 1 and links.startswith('lo ') and 'DOWN' in links
    initial = capacity()
    assert initial['/home/rehearsal/results'] > 21 * 1024**3 and initial['/mnt/d'] > 51 * 1024**3
    RUN.mkdir()
    for directory in ['bin', 'tmp', 'cases', 'fixtures']:
        (RUN / directory).mkdir()
    record = {'started': now(), 'uid': os.getuid(), 'namespace': namespace, 'parent_namespace': sys.argv[1], 'links': links, 'capacity_before': initial, 'commands': [], 'refusals': {}, 'completed': False}
    try:
        os.nice(10)
        record['investigation_commit'] = subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip()
        assert record['investigation_commit'].startswith('308bcbae')
        record['input_sha256'] = inventory(HERE)
        for line in (PRIOR/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
            digest, relative = line.split(None, 1)
            assert sha(PRIOR/relative) == digest
        record['prior_manifest_sha256'] = sha(PRIOR/'SHA256SUMS')
        prior = json.loads((PRIOR/'qualification/run.json').read_text(encoding='utf-8'))
        expected = prior['candidate_inventory']['node']
        assert inventory(SOURCE) == expected
        record['source_inventory'] = expected
        assert sha(GO) == prior['toolchains']['new']['go_binary_sha256']
        record['go_binary_sha256'] = sha(GO)
        env = {k:v for k,v in os.environ.items() if not k.startswith(('GO', 'FUSION_', 'F12_'))}
        env.update(PATH=str(GO.parent)+':/usr/bin:/bin', GOENV='off', GOTOOLCHAIN='local', GOWORK='off', GOPROXY='off', GOSUMDB='off', GOFLAGS='-mod=readonly', CGO_ENABLED='1', GOAMD64='v1', GOMAXPROCS='1', GOCACHE='/home/rehearsal/results/restart-release-selection-2026-10-04/repeat-cache', GOMODCACHE='/home/rehearsal/go/pkg/mod', GOTMPDIR=str(RUN/'tmp'), TMPDIR=str(RUN/'tmp'), PYTHONDONTWRITEBYTECODE='1')
        record['go_env'] = json.loads(subprocess.check_output([str(GO), 'env', '-json'], cwd=SOURCE, env=env, text=True))
        node = RUN/'node'
        shutil.copytree(SOURCE, node, ignore=shutil.ignore_patterns('.f12-probe'))
        assert inventory(node) == expected
        changes = {'core/restored_startup.go': HERE/'core_restored_startup.go', 'eth/restored_startup.go': HERE/'eth_restored_startup.go'}
        patch = ''
        for relative, source in changes.items():
            assert not (node/relative).exists()
            shutil.copyfile(source, node/relative)
            patch += ''.join(difflib.unified_diff([], source.read_text(encoding='utf-8').splitlines(True), fromfile='/dev/null', tofile='b/'+relative))
        backend = node/'eth/backend.go'
        old = backend.read_text(encoding='utf-8')
        trigger = 'func New(stack *node.Node, config *ethconfig.Config) (*Ethereum, error) {\n'
        assert old.count(trigger) == 1
        updated = old.replace(trigger, trigger+'\tif err := checkRestoredStartup(stack, config); err != nil {\n\t\treturn nil, err\n\t}\n', 1)
        backend.write_text(updated, encoding='utf-8')
        patch += ''.join(difflib.unified_diff(old.splitlines(True), updated.splitlines(True), fromfile='a/eth/backend.go', tofile='b/eth/backend.go'))
        (RUN/'candidate.patch').write_text(patch, encoding='utf-8')
        record['candidate_runtime_sha256'] = {p:sha(node/p) for p in [*changes, 'eth/backend.go']}
        testdir = node/'tests/restart'
        testdir.mkdir(parents=True)
        for name in ['fixture_test.go', 'blocks_test.go']:
            shutil.copyfile(REPO/'tests/restart'/name, testdir/name)
            shutil.copyfile(testdir/name, RUN/'fixtures'/name)
        shutil.copyfile(HERE/'seed_test.go', testdir/'seed_test.go')
        response = Path('docs/evidence/restart-2026-09-23/responses.json')
        (node/response).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO/response, node/response)
        shutil.copyfile(REPO/response, RUN/'fixtures/responses.json')
        shutil.copyfile(HERE/'profile.go', node/'cmd/efsn/restored_test_profile.go')
        (RUN/'profile.toml').write_text('[Ethstats]\nURL = ""\n[Node]\nHTTPHost = ""\nWSHost = ""\n[Node.P2P]\nNoDial = true\nNoDiscovery = true\nBootstrapNodes = []\nBootstrapNodesV5 = []\nStaticNodes = []\nTrustedNodes = []\n', encoding='utf-8')
        record['build_source_inventory'] = inventory(node)
        for label, args in [('seed', ['test', '-c', '-o', str(RUN/'bin/seed-tests'), './tests/restart']), ('cli', ['build', '-o', str(RUN/'bin/efsn'), './cmd/efsn'])]:
            execute(label+'-build', ['timeout', '--kill-after=10s', '5m', str(GO)] + args[:1] + ['-p=1', '-trimpath', '-buildvcs=false'] + args[1:], env, node)
        record['binary_sha256'] = {name:sha(RUN/'bin'/name) for name in ['seed-tests', 'efsn']}
        console = 'console.log("RESTOREDCLI "+JSON.stringify({head:eth.blockNumber,hash:eth.getBlock("latest").hash,mining:eth.mining,autoBuy:fsn.isAutoBuyTicket()}))'
        console_args = ['--exec', console, 'console']
        for name in ['valid', *[case for case in CASES if case not in ['absent', 'empty']]]:
            directory = RUN/'cases'/name
            execute('seed-'+name, ['timeout', '--kill-after=10s', '90s', str(RUN/'bin/seed-tests'), '-test.run=^TestPrepareRestoredStartup$', '-test.v', '-test.timeout=60s'], dict(env, FUSION_STARTUP_TEST_DIRECTORY=str(directory), FUSION_STARTUP_TEST_CASE=name), testdir)
        for name, error in CASES.items():
            directory = RUN/'cases'/name
            profile = directory/'profile.json'
            if name in ['absent', 'empty']:
                profile = RUN/'cases/valid/profile.json'
                if name == 'empty':
                    (directory/'efsn/chaindata').mkdir(parents=True)
            before = inventory(directory/'efsn/chaindata')
            cli(name, directory, dict(env, FUSION_STARTUP_TEST_PROFILE=str(profile)), console_args, sync='fast' if name=='fast_sync' else 'full', expected_error=error)
            after = inventory(directory/'efsn/chaindata')
            assert before == after, name
            if name == 'absent':
                assert not (directory/'efsn/chaindata').exists()
            record['refusals'][name] = {'expected_error': error, 'cold_files_before': before, 'cold_files_after': after, 'unchanged': True}
            save()
        directory = RUN/'cases/valid'
        valid_env = dict(env, FUSION_STARTUP_TEST_PROFILE=str(directory/'profile.json'))
        expected_heads = json.loads((directory/'expected.json').read_text(encoding='utf-8'))
        record['valid_expected_heads'] = expected_heads
        record['valid_observations'] = []
        for phase, head in [('restored', 'parent'), ('advanced', 'child'), ('restarted', 'child')]:
            if phase == 'advanced':
                cli('import-child', directory, valid_env, ['import', str(directory/'child.rlp')])
            output = cli(phase, directory, valid_env, console_args)
            entries = [json.loads(line.split('RESTOREDCLI ',1)[1]) for line in output.splitlines() if line.startswith('RESTOREDCLI ')]
            assert len(entries) == 1
            observed = entries[0]
            assert observed == {'head': expected_heads[head+'_height'], 'hash': expected_heads[head], 'mining': False, 'autoBuy': False}, observed
            record['valid_observations'].append({'phase':phase, **observed})
            save()
        record['case_files_final'] = inventory(RUN/'cases')
        assert inventory(SOURCE) == expected and inventory(node) == record['build_source_inventory']
        assert inventory(HERE) == record['input_sha256'] and sha(GO) == record['go_binary_sha256']
        record['source_toolchain_inputs_unchanged'] = True
        record['completed'] = True
    except BaseException as exc:
        record['failure'] = repr(exc)
        raise
    finally:
        record['finished'] = now()
        record['capacity_after'] = capacity()
        record['run_file_bytes'] = sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file())
        save()
        shutil.copytree(RUN, HERE/'qualification', ignore=shutil.ignore_patterns('bin', 'tmp', 'node', 'cases'))
