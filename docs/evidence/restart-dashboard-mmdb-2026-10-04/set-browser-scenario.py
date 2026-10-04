from datetime import datetime, timezone
import json
from pathlib import Path
import sys

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
mode = sys.argv[1]
if mode not in ['ready', 'empty', 'unavailable', 'expired', 'hanging', 'stop']:
    raise ValueError('Unknown scenario')
scenario = {'mode': mode, 'nodeId': sys.argv[2] if len(sys.argv) > 2 else 'synthetic-alpha', 'geoMode': sys.argv[3] if len(sys.argv) > 3 else 'coordinates'}
control = workspace / 'tmp/dashboard-browser-mmdb-scenario.json'
pending = control.with_suffix('.pending')
pending.write_text(json.dumps(scenario) + '\n', encoding='utf-8')
pending.replace(control)
with (evidence / 'browser-scenarios.jsonl').open('a', encoding='utf-8') as stream:
    stream.write(json.dumps({'time': datetime.now(timezone.utc).isoformat(), 'scenario': scenario}) + '\n')
print(json.dumps(scenario))
