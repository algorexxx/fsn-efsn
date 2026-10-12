from pathlib import Path
import datetime
import json
import os
import subprocess
import winreg

HERE = Path(__file__).resolve().parent
assert os.name == 'nt' and not (HERE/'resize-started.json').exists()
before = json.loads((HERE/'before/verification.json').read_text(encoding='utf-8'))
assert before['pass'] and before['virtual_disk_bytes'] == 220*1024**3
with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Lxss') as root:
    matches = []
    for index in range(winreg.QueryInfoKey(root)[0]):
        with winreg.OpenKey(root, winreg.EnumKey(root, index)) as child:
            if winreg.QueryValueEx(child, 'DistributionName')[0] == 'FusionRehearsal':
                matches.append(winreg.QueryValueEx(child, 'BasePath')[0])
assert matches == [r'D:\FusionRehearsal\Ubuntu']
record = {'started': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'target_virtual_bytes': 230*1024**3, 'distro': 'FusionRehearsal', 'base_path': matches[0], 'commands': []}
(HERE/'resize-started.json').write_bytes((json.dumps(record, indent=2)+'\n').encode('utf-8'))
for name, args in [('terminate', ['wsl.exe', '--terminate', 'FusionRehearsal']), ('resize', ['wsl.exe', '--manage', 'FusionRehearsal', '--resize', '246960619520B']), ('distro-status', ['wsl.exe', '--list', '--verbose'])]:
    entry = {'name': name, 'argv': args, 'started': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    with (HERE/(name+'.stdout.bin')).open('xb') as output, (HERE/(name+'.stderr.bin')).open('xb') as errors:
        result = subprocess.run(args, stdout=output, stderr=errors)
    entry.update(exit=result.returncode, finished=datetime.datetime.now(datetime.timezone.utc).isoformat())
    record['commands'].append(entry)
    (HERE/'resize-progress.json').write_bytes((json.dumps(record, indent=2)+'\n').encode('utf-8'))
    print(json.dumps(entry), flush=True)
    assert result.returncode == 0, name
record['finished'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
record['pass'] = True
(HERE/'resize-completion.json').write_bytes((json.dumps(record, indent=2)+'\n').encode('utf-8'))
