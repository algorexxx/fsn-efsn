from pathlib import Path
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUN = Path('/home/rehearsal/results') / HERE.name
SELECTED = Path('/home/rehearsal/results/restart-release-jwt-2026-10-04')
PRIOR = HERE.parent / 'restart-ticket-encoder-candidate-v2-2026-10-08'
VECTORS = HERE.parent / 'restart-ticket-compression-2026-10-08/qualification/vectors'
ROOTS = {'old': Path('/opt/fusion-toolchain/go'), 'modern': Path('/home/rehearsal/results/restart-release-selection-2026-10-04/toolchain/go')}
NODE_FILES = ['fixture_test.go', 'blocks_test.go', 'bridge_test.go', 'replenishment_test.go', 'reconstruction_test.go', 'finalize_parent_test.go', 'handover_test.go', 'purchase_test.go', 'single_block_handover_test.go']
RECOVERY_FILES = ['recovery_guard_test.go', 'recovery_signing_test.go']
NODE_TESTS = ['TestPresentDaySuccessorRejectsExpiredTicket', 'TestHistoricalBridgeImportsOnIndependentState', 'TestSingleRemainingTicketRequiresReplacement', 'TestReconstructionAcrossMissingStates', 'TestReconstructionAtHistoricalExpiryBoundary', 'TestReconstructionWithMissingAncestorReturnsError', 'TestHeaderBatchUsesUnstoredParents', 'TestFinalizeParentIsolatedFromConcurrentImport', 'TestSingleBackupBlockHandover', 'TestSingleBackupBlockRejectsShortSuccessorTicket', 'TestLongPurchaseRequiresHistoricalRefundDespitePoolAdmission', 'TestDefaultHistoricalPurchaseFailsPoolAdmission', 'TestPresentDayPurchaseStartRejectedOnHistoricalHead']
RECOVERY_TESTS = ['TestRecoveryGuard', 'TestRecoveryGuardRejects', 'TestRecoveryGuardInsufficientReplacement', 'TestRecoveryJournalHandover']
HELPERS = {'autobuy_test.go': ['advancePurchaseFixture'], 'anchor_paths_test.go': ['buildAnchorBranch', 'roundTripBlocks', 'blockHeaders'], 'anchor_enforcement_test.go': ['databaseDigest']}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob('*')) if p.is_file()}


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def save():
    (RUN / 'run.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')


def execute(name, argv, cwd, env):
    entry = {'name': name, 'argv': argv, 'cwd': str(cwd), 'started': now()}
    with (RUN / (name+'.stdout.txt')).open('wb') as output, (RUN / (name+'.stderr.txt')).open('wb') as errors:
        entry['exit'] = subprocess.run(argv, cwd=cwd, env=env, stdout=output, stderr=errors).returncode
    entry['finished'] = now()
    record['commands'].append(entry)
    save()
    print(name, entry['exit'], flush=True)
    if entry['exit']:
        raise RuntimeError('command failed: ' + name)


def make_helpers():
    content = b'package restart\n\nimport (\n"crypto/sha256"\n"encoding/binary"\n"testing"\n"time"\n"github.com/FusionFoundation/efsn/v5/common"\n"github.com/FusionFoundation/efsn/v5/core/types"\n"github.com/FusionFoundation/efsn/v5/ethdb"\n"github.com/FusionFoundation/efsn/v5/rlp"\n)\n\n'
    for filename, names in HELPERS.items():
        path = REPO / 'tests/restart' / filename
        raw = path.read_bytes()
        for name in names:
            start = re.search(rb'(?m)^func '+name.encode()+rb'\(', raw).start()
            end = re.search(rb'(?m)^}\r?\n', raw[start:]).end() + start
            body = raw[start:end]
            record['extracted_helpers'].append({'name': name, 'source': str(path.relative_to(REPO)), 'source_sha256': sha(path), 'start_line': raw[:start].count(b'\n')+1, 'end_line': raw[:end].count(b'\n'), 'body_sha256': hashlib.sha256(body).hexdigest()})
            content += body + b'\n'
    return content


if __name__ == '__main__':
    assert not RUN.exists() and not (HERE / 'qualification').exists()
    assert os.getuid() == 1000 and len(sys.argv) == 2
    assert sys.argv[1] != os.readlink('/proc/self/ns/net')
    links = subprocess.check_output(['ip', '-brief', 'link'], text=True)
    assert len(links.splitlines()) == 1 and links.startswith('lo ') and 'DOWN' in links
    capacity = {p: shutil.disk_usage(p).free for p in ['/home/rehearsal/results', '/mnt/d']}
    assert capacity['/home/rehearsal/results'] > 30*1024**3 and capacity['/mnt/d'] > 60*1024**3
    RUN.mkdir()
    (RUN / 'bin').mkdir()
    (RUN / 'tmp').mkdir()
    record = {'started': now(), 'uid': os.getuid(), 'namespace': os.readlink('/proc/self/ns/net'), 'parent_namespace': sys.argv[1], 'links': links, 'capacity_bytes': capacity, 'commands': [], 'toolchains': {}, 'binary_sha256': {}, 'source_inventories': {}, 'extracted_helpers': [], 'input_sha256': inventory(HERE), 'tests': {'node': NODE_TESTS, 'recovery': RECOVERY_TESTS}}
    try:
        record['investigation_commit'] = subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip()
        assert record['investigation_commit'].startswith('94113b0b')
        prior = json.loads((PRIOR/'qualification/run.json').read_text(encoding='utf-8'))
        previous = dict(prior['previous_manifest_sha256'], **{PRIOR.name: sha(PRIOR/'SHA256SUMS')})
        checked = 0
        for name, expected in previous.items():
            directory = HERE.parent/name
            assert sha(directory/'SHA256SUMS') == expected
            for line in (directory/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
                digest, relative = line.split(None, 1)
                assert sha(directory/relative) == digest, (name, relative)
                checked += 1
        record['previous_manifest_sha256'] = previous
        record['previous_files_verified'] = checked
        environments = {}
        for name, root in ROOTS.items():
            compiler = 'old' if name == 'old' else 'new'
            assert sha(root/'bin/go') == prior['toolchains'][compiler]['go_binary_sha256']
            env = os.environ.copy()
            for key in list(env):
                if key.startswith('GO') or key.startswith('FUSION_') or key.startswith('F12_'):
                    env.pop(key)
            env.update(PATH=str(root/'bin')+':/usr/bin:/bin', GOENV='off', GOTOOLCHAIN='local', GOWORK='off', GOPROXY='off', GOSUMDB='off', GOFLAGS='-mod=readonly', CGO_ENABLED='1', GOAMD64='v1', GOMAXPROCS='2', GOCACHE='/home/rehearsal/.cache/go-build' if name=='old' else '/home/rehearsal/results/restart-release-selection-2026-10-04/repeat-cache', GOMODCACHE='/home/rehearsal/go/pkg/mod', GOTMPDIR=str(RUN/'tmp'), TMPDIR=str(RUN/'tmp'), PYTHONDONTWRITEBYTECODE='1')
            environments[name] = env
            record['toolchains'][name] = {'root': str(root), 'go_binary_sha256': sha(root/'bin/go'), 'go_env': json.loads(subprocess.check_output(['go', 'env', '-json'], cwd=SELECTED/'node', env=env, text=True))}
        helpers = make_helpers()
        (RUN/'helpers_test.go').write_bytes(helpers)
        response = Path('docs/evidence/restart-2026-09-23/responses.json')
        record['fixture_inputs'] = {str(p): sha(REPO/p) for p in [response, Path('consensus/datong/snapshot_test.go')] + [Path('tests/restart')/f for f in NODE_FILES+RECOVERY_FILES]}
        base = {name: json.loads((HERE.parent/'restart-release-jwt-2026-10-04'/(name+'-inventory.json')).read_text(encoding='utf-8')) for name in ['node','recovery']}
        for name in base:
            assert inventory(SELECTED/name) == base[name]
        for mode, compiler in [('old','old'), ('candidate','modern')]:
            for kind in ['node','recovery']:
                label = mode+'-'+kind
                folder = RUN/label
                env = environments[compiler]
                shutil.copytree(SELECTED/kind, folder)
                expected = base[kind].copy()
                if mode == 'candidate':
                    execute(label+'-patch-check', ['git','apply','--check',str(PRIOR/'candidate.patch')], folder, env)
                    execute(label+'-patch-apply', ['git','apply',str(PRIOR/'candidate.patch')], folder, env)
                    expected.update(prior['runtime_input_sha256'])
                assert inventory(folder) == expected
                testdir = folder/'tests/restart'
                testdir.mkdir(parents=True, exist_ok=True)
                assert not list(testdir.glob('*_test.go'))
                for filename in NODE_FILES + (RECOVERY_FILES if kind == 'recovery' else []):
                    relative = 'tests/restart/'+filename
                    shutil.copyfile(REPO/relative, folder/relative)
                    expected[relative] = sha(REPO/relative)
                (testdir/'helpers_test.go').write_bytes(helpers)
                expected['tests/restart/helpers_test.go'] = sha(RUN/'helpers_test.go')
                (folder/response).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(REPO/response, folder/response)
                expected[response.as_posix()] = sha(REPO/response)
                relative = 'consensus/datong/snapshot_test.go'
                shutil.copyfile(REPO/relative, folder/relative)
                expected[relative] = sha(REPO/relative)
                assert inventory(folder) == expected
                record['source_inventories'][label] = expected
                binary = RUN/'bin'/label
                execute(label+'-build', ['timeout','--kill-after=20s','7m','go','test','-c','-race','-p=2','-trimpath','-buildvcs=false','-o',str(binary),'./tests/restart'], folder, env)
                record['binary_sha256'][label] = sha(binary)
                for test in NODE_TESTS if kind=='node' else RECOVERY_TESTS:
                    execute(label+'-'+test, ['timeout','--kill-after=10s','90s',str(binary),'-test.run=^'+test+'$','-test.v','-test.count=1','-test.timeout=75s'], testdir, env)
                if kind == 'node':
                    execute(label+'-snapshot', ['timeout','--kill-after=20s','3m','go','test','-race','-p=2','-count=1','-v','-timeout=75s','-run','^TestSnapshot(RejectsTruncatedCount|PreservesValidEncoding|RejectsInvalidFraming)$','./consensus/datong'], folder, env)
        for mode, compiler, source in [('old','old','old-node'), ('modern','modern','old-node'), ('candidate','modern','candidate-node')]:
            folder = RUN/source
            probe = folder/('.f12-bench-'+mode)
            probe.mkdir()
            shutil.copyfile(HERE/'benchmark_test.go', probe/'benchmark_test.go')
            encoder = PRIOR/('candidate_encoder.go' if mode=='candidate' else 'stdlib_encoder.go')
            (probe/'encoder.go').write_bytes(encoder.read_bytes().replace(b'package main', b'package encoderbench', 1))
            for p in probe.iterdir():
                record['source_inventories'][source][p.relative_to(folder).as_posix()] = sha(p)
            execute(mode+'-benchmark-build', ['timeout','--kill-after=20s','7m','go','test','-c','-p=2','-trimpath','-buildvcs=false','-o',str(RUN/'bin'/('bench-'+mode)),'./'+probe.name], folder, environments[compiler])
            record['binary_sha256']['bench-'+mode] = sha(RUN/'bin'/('bench-'+mode))
        record['vectors_sha256'] = inventory(VECTORS)
        for round_number in range(1,6):
            for mode, compiler in [('old','old'), ('modern','modern'), ('candidate','modern')]:
                env = dict(environments[compiler], GOMAXPROCS='1', F12_VECTORS=str(VECTORS), F12_EXPECT_PRESERVED='0' if mode=='modern' else '1')
                execute('benchmark-'+str(round_number)+'-'+mode, ['timeout','--kill-after=10s','60s',str(RUN/'bin'/('bench-'+mode)),'-test.run=^$','-test.bench=^BenchmarkEncode$','-test.benchtime=100x','-test.count=1','-test.cpu=1','-test.benchmem'], RUN, env)
        for name in base:
            assert inventory(SELECTED/name) == base[name]
        for name, expected in record['source_inventories'].items():
            assert inventory(RUN/name) == expected
        assert inventory(VECTORS) == record['vectors_sha256']
        assert inventory(HERE) == record['input_sha256']
        record['source_inventories_unchanged'] = True
        record['completed'] = True
    except BaseException as exc:
        record['failure'] = repr(exc)
        raise
    finally:
        record['finished'] = now()
        record['remaining_bytes'] = {p: shutil.disk_usage(p).free for p in ['/home/rehearsal/results', '/mnt/d']}
        save()
        shutil.copytree(RUN, HERE/'qualification', ignore=shutil.ignore_patterns('bin','tmp','old-node','old-recovery','candidate-node','candidate-recovery'))
