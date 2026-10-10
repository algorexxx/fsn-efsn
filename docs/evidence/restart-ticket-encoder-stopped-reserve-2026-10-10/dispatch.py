from pathlib import Path
import datetime
import json
import os
import subprocess
import sys


def dispatch(bundle, host_run):
    bundle = bundle.resolve(strict=True)
    assert os.name == 'nt' and (bundle/'launch.py').is_file()
    host_run.mkdir(parents=True,exist_ok=False)
    linux = '/mnt/'+bundle.drive[0].lower()+bundle.as_posix()[2:]
    command = ['wsl.exe','-d','FusionRehearsal','-u','root','--','timeout','--kill-after=20s','20m','python3',linux+'/launch.py']
    record = {'started':datetime.datetime.now(datetime.timezone.utc).isoformat(),'argv':command,'dispatcher_pid':os.getpid(),'bundle':str(bundle)}
    with (host_run/'stdout.txt').open('xb') as output, (host_run/'stderr.txt').open('xb') as errors:
        child = subprocess.Popen(command,stdout=output,stderr=errors,creationflags=subprocess.CREATE_NO_WINDOW)
        record['wsl_pid'] = child.pid
        (host_run/'dispatch.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
        record['exit'] = child.wait()
    record['finished'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (host_run/'dispatch-finished.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    return record['exit']


if __name__ == '__main__':
    assert len(sys.argv) == 3
    sys.exit(dispatch(Path(sys.argv[1]),Path(sys.argv[2])))
