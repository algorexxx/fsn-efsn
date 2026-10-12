from pathlib import Path
import datetime,json,shutil
here=Path(__file__).resolve().parent
active=[]
for folder in Path('/proc').iterdir():
    if folder.name.isdigit():
        try:
            name=(folder/'comm').read_text(encoding='utf-8').strip()
            if name in ['efsn','replay-tests','observer']:active.append({'pid':int(folder.name),'name':name})
        except (FileNotFoundError,ProcessLookupError):pass
record={'observed':datetime.datetime.now(datetime.timezone.utc).isoformat(),'active':active,'free_bytes':{p:shutil.disk_usage(p).free for p in ['/home/rehearsal/results','/mnt/d']}}
with (here/'preinspection-resources.json').open('x',encoding='utf-8') as f:f.write(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
assert not active
assert record['free_bytes']['/home/rehearsal/results']>21*1024**3 and record['free_bytes']['/mnt/d']>51*1024**3
