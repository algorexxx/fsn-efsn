import hashlib
import json
from pathlib import Path
import re


evidence = Path(__file__).resolve().parent
candidate = Path('/home/rehearsal/results/restart-release-text-2026-10-04')
baseline = Path('/home/rehearsal/results/restart-release-jwt-2026-10-04')
prefix = 'github.com/FusionFoundation/efsn/v5/'
loops = {}
excerpts = []
for command, folder in (('efsn', 'node'), ('fsn-recovery', 'recovery')):
    text = (evidence / ('loops-' + command + '.txt')).read_text(encoding='utf-8')
    found = set(re.findall(re.escape(prefix) + r'([^:\n]+):(\d+):(\d+): loop variable (\S+) now per-iteration, (\S+)', text))
    loops[command] = []
    for path, line, column, variable, allocation in sorted(found):
        source = candidate / folder / path
        raw = source.read_bytes()
        assert raw == (baseline / folder / path).read_bytes()
        lines = raw.decode('utf-8').splitlines()
        start, end = max(1, int(line) - 6), min(len(lines), int(line) + 26)
        loops[command].append({'path': path, 'line': int(line), 'column': int(column), 'variable': variable,
                               'allocation': allocation, 'source_sha256': hashlib.sha256(raw).hexdigest()})
        excerpts.append('\n' + command + ' ' + path + '\n' + '\n'.join(str(i) + ': ' + lines[i - 1] for i in range(start, end + 1)))
(evidence / 'loops.json').write_text(json.dumps(loops, indent=2) + '\n', encoding='utf-8')
(evidence / 'loop-source-excerpts.txt').write_text('\n'.join(excerpts) + '\n', encoding='utf-8')
print(json.dumps({name: len(values) for name, values in loops.items()}))
