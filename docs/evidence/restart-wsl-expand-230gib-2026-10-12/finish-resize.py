from pathlib import Path
import datetime
import json
import subprocess

HERE = Path(__file__).resolve().parent
assert not (HERE/'finish-started.json').exists()
prior = json.loads((HERE/'resize-progress.json').read_text(encoding='utf-8'))
assert prior['commands'][-1]['name'] == 'resize' and prior['commands'][-1]['exit'] != 0
message = (HERE/'resize.stdout.bin').read_bytes().decode('utf-16le')
assert 'WSL_E_DISTRO_NOT_STOPPED' in message
record = {'started': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'commands': [], 'target_virtual_bytes': 246960619520, 'reason': 'Native resize refused attached VHD; brief restart of idle Docker backend permits approved expansion.'}


def run(name, args):
    entry = {'name': name, 'argv': args, 'started': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    with (HERE/(name+'.stdout.bin')).open('xb') as output, (HERE/(name+'.stderr.bin')).open('xb') as errors:
        result = subprocess.run(args, stdout=output, stderr=errors)
    entry.update(exit=result.returncode, finished=datetime.datetime.now(datetime.timezone.utc).isoformat())
    record['commands'].append(entry)
    (HERE/'finish-progress.json').write_bytes((json.dumps(record, indent=2)+'\n').encode('utf-8'))
    print(json.dumps(entry), flush=True)
    assert result.returncode == 0, name
    data = (HERE/(name+'.stdout.bin')).read_bytes()
    return data.decode('utf-16le') if b'\x00' in data else data.decode('utf-8')


(HERE/'finish-started.json').write_bytes((json.dumps(record, indent=2)+'\n').encode('utf-8'))
assert not run('docker-running-before', ['docker', 'ps', '--quiet']).strip()
running = run('wsl-running-before', ['wsl.exe', '--list', '--running', '--quiet'])
assert set(running.split()) <= {'FusionRehearsal', 'docker-desktop'}
try:
    run('docker-stop', ['docker', 'desktop', 'stop'])
    run('wsl-stop-idle', ['wsl.exe', '--shutdown'])
    run('resize-idle', ['wsl.exe', '--manage', 'FusionRehearsal', '--resize', '246960619520B'])
finally:
    run('docker-restart', ['docker', 'desktop', 'start'])
run('docker-status-after', ['docker', 'desktop', 'status'])
assert not run('docker-running-after', ['docker', 'ps', '--quiet']).strip()
record.update(pass_operation=True, finished=datetime.datetime.now(datetime.timezone.utc).isoformat())
(HERE/'finish-completion.json').write_bytes((json.dumps(record, indent=2)+'\n').encode('utf-8'))
