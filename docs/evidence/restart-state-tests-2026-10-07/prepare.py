import difflib
import json
from pathlib import Path
import sys


evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
phase = sys.argv[1]
target = evidence / phase
target.mkdir()
paths = ['core/state/' + name for name in ('state_test.go', 'statedb_test.go', 'iterator_test.go', 'sync_test.go', 'suicide_test.go')]
patch = []
for stage, directory in (('baseline', 'restart-release-jwt-2026-10-04'), ('candidate', 'restart-release-text-2026-10-04')):
    source = Path('/home/rehearsal/results') / directory / 'node'
    overlay = {}
    for name in paths:
        old = (source / name).read_text(encoding='utf-8') if (source / name).exists() else ''
        new = (workspace / name).read_text(encoding='utf-8')
        if stage == 'baseline':
            patch.extend(difflib.unified_diff(old.splitlines(True), new.splitlines(True), fromfile='a/' + name, tofile='b/' + name))
            saved = target / Path(name).name
            saved.write_text(new, encoding='utf-8')
        else:
            baseline = Path('/home/rehearsal/results/restart-release-jwt-2026-10-04/node') / name
            assert old == (baseline.read_text(encoding='utf-8') if baseline.exists() else '')
        overlay[str(source / name)] = str(target / Path(name).name)
    (target / (stage + '-overlay.json')).write_text(json.dumps({'Replace': overlay}, indent=2) + '\n', encoding='utf-8')
(target / 'state-tests.patch').write_text(''.join(patch), encoding='utf-8')
