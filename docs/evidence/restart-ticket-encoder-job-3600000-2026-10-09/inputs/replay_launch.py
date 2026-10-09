from pathlib import Path
import datetime
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
import replay_monitor as monitor

HERE = Path(__file__).resolve().parent
BUNDLE = HERE.parent
CONFIG = json.loads((HERE/'config.json').read_text(encoding='utf-8'))
monitor.validate_configuration(CONFIG)
assert BUNDLE.name == CONFIG['job'] and os.getuid() == 0
ROOT = Path('/home/rehearsal/replay')
SOURCE = Path('/home/rehearsal/data/efsn/chaindata')
TARGET,CHECKPOINT,RECOVERY = [ROOT/CONFIG[name] for name in ['target','checkpoint','recovery_checkpoint']]
RUN = Path('/home/rehearsal/results')/CONFIG['job']
assert not RUN.exists() and not (BUNDLE/'qualification').exists() and not (BUNDLE/'completion.json').exists()
assert TARGET.exists() == (CONFIG['mode'] == 'resume')
for line in (HERE/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
    digest,name = line.split(None,1)
    assert hashlib.sha256((HERE/name).read_bytes()).hexdigest() == digest,name
if len(sys.argv) == 1:
    os.execvp('unshare',['unshare','--mount','--net','--','python3',str(HERE/'replay_launch.py'),os.readlink('/proc/self/ns/net'),os.readlink('/proc/self/ns/mnt')])
assert len(sys.argv) == 3
assert sys.argv[1] != os.readlink('/proc/self/ns/net') and sys.argv[2] != os.readlink('/proc/self/ns/mnt')
for path in [SOURCE,CHECKPOINT,RECOVERY]:
    assert path.resolve() == path and path.is_dir() and not path.is_symlink()
assert TARGET.parent.resolve() == ROOT
assert Path('/home/rehearsal/results/backup-copy-2026-09-23/verified.txt').is_file()
locks = [open(str(path)+'.run.lock','a',encoding='utf-8') for path in sorted(set([CHECKPOINT,TARGET,RECOVERY]))]
for lock in locks:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
subprocess.run(['mount','--make-rprivate','/'],check=True)
directories = [tempfile.mkdtemp(prefix='f12-job-'+name+'-') for name in ['source','checkpoint','recovery','closed']]
source,checkpoint,recovery,closed = directories
mounted = []
result = 1
try:
    for path,mountpoint in [(SOURCE,source),(CHECKPOINT,checkpoint),(RECOVERY,recovery)]:
        subprocess.run(['mount','--bind',str(path),mountpoint],check=True)
        mounted.append(mountpoint)
        subprocess.run(['mount','-o','remount,bind,ro',mountpoint],check=True)
    command = ['runuser','-u','rehearsal','--','python3',str(HERE/'replay_job.py')]
    args = [sys.argv[1],sys.argv[2],source,checkpoint,recovery]
    result = subprocess.run(command+['replay']+args).returncode
    if result == 0:
        subprocess.run(['mount','--bind',str(TARGET),closed],check=True)
        mounted.append(closed)
        subprocess.run(['mount','-o','remount,bind,ro',closed],check=True)
        result = subprocess.run(command+['inspect']+args+[closed]).returncode
finally:
    if RUN.exists():
        final = subprocess.run(['runuser','-u','rehearsal','--','python3',str(HERE/'replay_job.py'),'finalize',sys.argv[1],sys.argv[2],source,checkpoint,recovery])
        if final.returncode:
            result = final.returncode
    for directory in reversed(mounted):
        subprocess.run(['umount',directory],check=True)
    for directory in reversed(directories):
        os.rmdir(directory)

if result == 0:
    invocation = {'started':datetime.datetime.now(datetime.timezone.utc).isoformat(),'argv':['runuser','-u','rehearsal','--','python3',str(HERE/'replay_verify.py')]}
    with (BUNDLE/'verification.stdout.txt').open('xb') as output, (BUNDLE/'verification.stderr.txt').open('xb') as errors:
        result = subprocess.run(invocation['argv'],stdout=output,stderr=errors).returncode
    invocation.update(exit=result,finished=datetime.datetime.now(datetime.timezone.utc).isoformat())
    (BUNDLE/'verification-run.json').write_text(json.dumps(invocation,indent=2)+'\n',encoding='utf-8')
completion = {'finished':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit':result,'verified_pass':result == 0,'job':CONFIG['job'],'requested_end':CONFIG['end_height'],'automatic_continuation':False}
(BUNDLE/'completion.json').write_text(json.dumps(completion,indent=2)+'\n',encoding='utf-8')
files = sorted([p for p in (BUNDLE/'qualification').rglob('*') if p.is_file()]+[p for p in BUNDLE.iterdir() if p.name.startswith('verification') or p.name == 'completion.json'])
(BUNDLE/'OUTPUT_SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(BUNDLE).as_posix()+'\n' for p in files),encoding='utf-8')
files = sorted(p for p in BUNDLE.rglob('*') if p.is_file() and p != BUNDLE/'SHA256SUMS')
(BUNDLE/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(BUNDLE).as_posix()+'\n' for p in files),encoding='utf-8')
print(json.dumps(completion),flush=True)
sys.exit(result)
