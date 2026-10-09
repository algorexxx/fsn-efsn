from pathlib import Path
from contextlib import ExitStack
import fcntl
import importlib.util
import json
import os
import sys
import subprocess

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PRIOR = HERE.parent / 'restart-ticket-encoder-job-3600000-2026-10-09'
BASE = HERE.parent / 'restart-ticket-encoder-replay-100000-2026-10-08/run.py'
spec = importlib.util.spec_from_file_location('retained_helpers', BASE)
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
r.RUN = HERE
assert os.getuid() == 1000 and not (HERE/'protected-state.json').exists()
assert r.sha(BASE) == '5fd2ebdb5b7050177d2955ec584b664bc51593718853f53c1ce902b5ec2e5167'
links = json.loads(subprocess.check_output(['ip', '-j', 'link', 'show'], text=True))
assert [link['ifname'] for link in links] == ['lo'] and 'UP' not in links[0]['flags']
for line in (PRIOR/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
    digest, relative = line.split(None, 1)
    assert r.sha(PRIOR/relative) == digest, relative
prior = json.loads((PRIOR/'qualification/run.json').read_text(encoding='utf-8'))
assert json.loads((PRIOR/'completion.json').read_text(encoding='utf-8'))['verified_pass']
for folder in Path('/proc').iterdir():
    if folder.name.isdigit():
        try:
            assert (folder/'comm').read_text(encoding='utf-8').strip() not in ['efsn', 'replay-tests', 'restart-tests', 'observer']
        except (FileNotFoundError, ProcessLookupError):
            pass
backup = Path('/home/rehearsal/data/efsn/chaindata')
working = Path('/home/rehearsal/replay/candidate-ticket-encoding-working')
recovery = Path('/home/rehearsal/replay/candidate-ticket-encoding-2400000-v2')
record = {'started': r.now(), 'uid': os.getuid(), 'namespace': os.readlink('/proc/self/ns/net'), 'helper_sha256': r.sha(BASE), 'script_sha256': r.sha(Path(__file__)), 'prior_manifest_sha256': r.sha(PRIOR/'SHA256SUMS')}
with ExitStack() as stack:
    for path in [backup, working, recovery, *r.BASELINES.values()]:
        assert path.resolve() == path and path.is_dir() and not path.is_symlink()
        lock_paths = [path/'LOCK']
        if Path(str(path)+'.run.lock').exists():
            lock_paths.append(Path(str(path)+'.run.lock'))
        for lock_path in lock_paths:
            lock = stack.enter_context(lock_path.open('rb'))
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    record['backup'] = r.metadata(backup, 'protected-backup')
    assert record['backup'] == prior['backup_after']
    record['baselines'] = {name: r.metadata(path, 'protected-baseline-'+name) for name, path in r.BASELINES.items()}
    assert record['baselines'] == prior['baseline_after']
    for name, path, expected in [('working', working, prior['target_before_cold_sha256']), ('recovery', recovery, prior['recovery_checkpoint_sha256'])]:
        actual = r.inventory(path)
        assert actual == expected, name
        record[name] = {'files': len(actual), 'all_sha256_match': True}
    retained = Path('/home/rehearsal/results')/PRIOR.name
    assert r.inventory(r.SELECTED) == prior['selected_inventory']
    assert r.inventory(retained/'node') == prior['candidate_inventory']
    assert r.sha(retained/'bin/replay-tests') == prior['binary_sha256']
record.update(pass_=True, finished=r.now(), scope='Full file hashes for working/recovery databases and retained source/executable; metadata inventory for original backup and two baselines. No LevelDB open or transaction replay.')
(HERE/'protected-state.json').write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
print(json.dumps(record, indent=2))
