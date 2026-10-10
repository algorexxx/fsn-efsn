from pathlib import Path
import datetime
import json
import subprocess
import sys

here = Path(__file__).resolve().parent
mode = sys.argv[1]
assert mode in ['archive', 'retire']
record = {'started': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'argv': [sys.executable, str(here/'archive.py'), mode]}
with (here/(mode+'.stdout.txt')).open('xb') as output, (here/(mode+'.stderr.txt')).open('xb') as error:
    result = subprocess.run(record['argv'], stdout=output, stderr=error)
record.update(exit=result.returncode, finished=datetime.datetime.now(datetime.timezone.utc).isoformat())
with (here/(mode+'-command.json')).open('x', encoding='utf-8') as file:
    file.write(json.dumps(record, indent=2)+'\n')
print(json.dumps(record), flush=True)
sys.exit(result.returncode)
