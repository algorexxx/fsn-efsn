import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


evidence = Path(__file__).resolve().parent
prior = evidence.parent / 'restart-release-text-2026-10-04'
previous = json.loads((prior / 'review.json').read_text(encoding='utf-8'))
subprocess.run([sys.executable, str(prior / 'report.py'), '--check'], check=True, capture_output=True)
loops = json.loads((evidence / 'loops.json').read_text(encoding='utf-8'))
loop_counts = {}
defaults = {}
for command, entries in loops.items():
    assert int((evidence / ('loops-' + command + '-exit.txt')).read_text(encoding='utf-8')) == 0
    folder = 'node' if command == 'efsn' else 'recovery'
    for entry in entries:
        path = Path('/home/rehearsal/results/restart-release-text-2026-10-04') / folder / entry['path']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry['source_sha256']
    loop_counts[command] = {'diagnostic_records_without_inlining_duplicates': len(entries),
                            'distinct_variables': len({(v['path'], v['line'], v['variable'].split('.')[-1]) for v in entries}),
                            'distinct_loop_sites': len({(v['path'], v['line']) for v in entries})}
    settings = previous['build_settings_changes'][command]['DefaultGODEBUG']
    old = dict(v.split('=', 1) for v in settings['before'].split(','))
    new = dict(v.split('=', 1) for v in settings['after'].split(','))
    defaults[command] = {'removed_legacy_overrides': {k: v for k, v in old.items() if k not in new},
                          'retained_overrides': new}
    assert all(old[k] == v for k, v in new.items())
    assert len(defaults[command]['removed_legacy_overrides']) == 22
tests = {}
for file in sorted(evidence.glob('*-exit.txt')):
    label = file.name.removesuffix('-exit.txt')
    log = evidence / (label + '.txt')
    text = log.read_text(encoding='utf-8') if log.exists() else ''
    tests[label] = {'exit': int(file.read_text(encoding='utf-8')),
                    'package_results': re.findall(r'^(?:ok|FAIL)[ \t]+.*$', text, re.M),
                    'passed_top_level': re.findall(r'^--- PASS: (\S+)', text, re.M),
                    'skipped_top_level': re.findall(r'^--- SKIP: (\S+)', text, re.M)}
for stage in ('baseline', 'candidate'):
    for name in ('common-corrected', 'rlp', 'core-types-repaired'):
        result = tests[stage + '-' + name]
        assert result['exit'] == 0 and result['passed_top_level'] and not result['skipped_top_level']
    assert tests[stage + '-core-state-corrected']['exit'] == 1
    assert tests[stage + '-core-types']['exit'] == 1
for name in ('core-state-corrected', 'core-types'):
    assert (evidence / ('baseline-' + name + '.txt')).read_bytes() == (evidence / ('candidate-' + name + '.txt')).read_bytes()
references = {name: json.loads((evidence / ('references-' + name + '.json')).read_text(encoding='utf-8')) for name in loops}
assert all(not any(v['Symbol'] == 'math/rand.Seed' for v in refs) for refs in references.values())
for file in ('network.txt', 'test-network.txt', 'test-cached-network.txt', 'test-complete-network.txt', 'test-corrected-network.txt'):
    lines = (evidence / file).read_text(encoding='utf-8').strip().splitlines()
    assert len(lines) == 1 and lines[0].split()[:2] == ['lo', 'DOWN']
for file, expected in json.loads((evidence / 'supporting-source-hashes.json').read_text(encoding='utf-8')).items():
    assert hashlib.sha256(Path(file).read_bytes()).hexdigest() == expected
for file in evidence.glob('*.sh'):
    subprocess.run(['bash', '-n', str(file)], check=True)
result = {'status': 'language-default-review-complete-with-coverage-hold', 'loops': loop_counts, 'defaults': defaults,
          'tests': tests, 'direct_reference_inventory': references,
          'production_selection': 'P1-P17+B1+D1', 'text_upgrade_selected': False,
          'test_only_patch': '10-core-types-fixtures.patch', 'full_regression_pass': False,
          'historical_compatibility_established': False, 'launch_approved': False}
if '--check' in sys.argv:
    assert result == json.loads((evidence / 'review.json').read_text(encoding='utf-8'))
else:
    (evidence / 'review.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print(json.dumps({'status': result['status'], 'loops': loop_counts,
                  'passing_top_level': {k: len(v['passed_top_level']) for k, v in tests.items() if v['passed_top_level']}}, indent=2))
