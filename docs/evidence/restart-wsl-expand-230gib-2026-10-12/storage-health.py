from pathlib import Path
import datetime
import json
import os
import re
import subprocess

here = Path(__file__).resolve().parent
assert os.getuid() == 0 and not (here/'storage-health.json').exists()
links = subprocess.check_output(['ip', '-brief', 'link'], text=True)
assert len(links.splitlines()) == 1 and links.startswith('lo ') and 'DOWN' in links
mount = json.loads(subprocess.check_output(['findmnt', '--json', '--target', '/', '--output', 'SOURCE,TARGET,FSTYPE,OPTIONS'], text=True))['filesystems'][0]
kernel = subprocess.check_output(['dmesg', '--color=never'], text=True)
(here/'post-storage-kernel.txt').write_text(kernel, encoding='utf-8')
errors = [line for line in kernel.splitlines() if re.search(r'I/O error|EXT4-fs error|Buffer I/O|blk_update_request.*error|EXT4-fs.*remount.*read.only', line, re.I)]
record = {'observed': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'mount': mount, 'links': links, 'observed_storage_errors': errors, 'scope': 'Mounted ext4/rw state and recorded kernel storage-error patterns; not an offline fsck or independent restore rehearsal.'}
record['pass'] = mount['fstype'] == 'ext4' and 'rw' in mount['options'].split(',') and not errors
(here/'storage-health.json').write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
print(json.dumps(record), flush=True)
assert record['pass']
