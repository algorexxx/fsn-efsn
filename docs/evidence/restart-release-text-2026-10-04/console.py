import json
from pathlib import Path
import subprocess


evidence = Path(__file__).resolve().parent
work = Path('/home/rehearsal/results/restart-release-text-2026-10-04')
base = Path('/home/rehearsal/results/restart-release-jwt-2026-10-04')
script = r"""if ('\u00e9'.normalize('NFD') !== 'e\u0301' || '\u00c5'.normalize('NFKD') !== 'A\u030a' || '\u00df'.toUpperCase() !== 'SS' || '\u00e9'.localeCompare('e\u0301') !== 0) { throw new Error('text console acceptance mismatch'); } console.log('TEXT_CONSOLE_ACCEPTANCE_OK');"""
results = {}
for name, binary in [('baseline', base / 'bin/efsn'), ('candidate', work / 'bin/efsn')]:
    destination = work / (name + '-console-data')
    assert not destination.exists()
    command = [str(binary), '--datadir', str(destination), '--networkid', '32659777',
               '--port', '0', '--nat', 'none', '--maxpeers', '0', '--nodiscover',
               '--ipcdisable', '--cache', '16', '--exec', script, 'console']
    (evidence / (name + '-console-command.json')).write_text(json.dumps(command, indent=2) + '\n', encoding='utf-8')
    with (evidence / (name + '-console-runtime.txt')).open('w', encoding='utf-8') as output:
        result = subprocess.run(command, stdout=output, stderr=subprocess.STDOUT, timeout=45)
    text = (evidence / (name + '-console-runtime.txt')).read_text(encoding='utf-8')
    results[name] = {'exit': result.returncode, 'expected_marker': 'TEXT_CONSOLE_ACCEPTANCE_OK' in text}
    assert result.returncode == 0 and results[name]['expected_marker'], name
(evidence / 'console-runtime-result.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
print(json.dumps(results))
