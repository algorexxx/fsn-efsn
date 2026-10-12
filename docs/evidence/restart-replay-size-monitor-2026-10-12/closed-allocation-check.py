from pathlib import Path
import datetime
import fcntl
import hashlib
import json
import os
import subprocess
import sys

sys.dont_write_bytecode=True
here=Path(__file__).resolve().parent
repo=here.parents[2]
sys.path.insert(0,str(repo/'tests/restart'))
import replay_monitor

target=Path('/home/rehearsal/replay/candidate-ticket-encoding-working')
assert os.getuid()==1000 and not (here/'closed-allocation-check.json').exists()
links=subprocess.check_output(['ip','-brief','link'],text=True)
assert len(links.splitlines())==1 and links.startswith('lo ') and 'DOWN' in links
assert target.resolve()==target and not target.is_symlink()
with Path(str(target)+'.run.lock').open('a',encoding='utf-8') as run_lock, (target/'LOCK').open('rb') as db_lock:
    fcntl.flock(run_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    fcntl.flock(db_lock,fcntl.LOCK_SH|fcntl.LOCK_NB)
    for folder in Path('/proc').iterdir():
        if folder.name.isdigit():
            try:
                assert (folder/'comm').read_text(encoding='utf-8').strip() not in ['efsn','replay-tests','observer']
            except (FileNotFoundError,ProcessLookupError):pass
    command=['timeout','--kill-after=2s','15s','du','-sB1',str(target)]
    before=subprocess.run(command,capture_output=True,text=True,check=True)
    scanner_command=['timeout','--kill-after=2s','15s',sys.executable,'-B',str(repo/'tests/restart/replay_monitor.py'),'--allocated-size',str(target)]
    scanner=subprocess.run(scanner_command,capture_output=True,text=True,check=True)
    after=subprocess.run(command,capture_output=True,text=True,check=True)
    result=json.loads(scanner.stdout)
    assert not before.stderr and not after.stderr and not scanner.stderr
    assert before.stdout==after.stdout and result['allocated_bytes']==int(before.stdout.split()[0])
    assert not result['vanished_entries'] and result['path']==str(target)
    record={'observed':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pass':True,'links':links,'run_and_database_locks_held':True,'controller_sha256':hashlib.sha256((repo/'tests/restart/replay_monitor.py').read_bytes()).hexdigest(),'du_before':before.stdout,'du_after':after.stdout,'scanner':result,'scanner_argv':scanner_command,'database_content_read_or_hashed':False,'scope':'Metadata-only allocation comparison on the closed, separately cold-verified target; not another replay or state inspection'}
    with (here/'closed-allocation-check.json').open('x',encoding='utf-8') as f:f.write(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record))
