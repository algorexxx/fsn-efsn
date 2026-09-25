from pathlib import Path
import hashlib,json,os,time,zipfile

class ForwardOnly:
    def __init__(self, file):
        self.file, self.offset = file, 0
    def write(self, data):
        written = self.file.write(data)
        self.offset += written
        return written
    def tell(self):
        return self.offset
    def flush(self):
        self.file.flush()

root=Path('W:/FusionRestart/restore-rehearsal-2026-09-24')
source=Path('C:/Users/Peter/Documents/CODING/fusion-node/data/efsn/chaindata')
files=json.loads((root/'package/part-00000.json').read_text(encoding='utf-8'))['files']
start=time.monotonic()
target=root/'forward-only-probe.zip'
with target.open('xb',buffering=8*1024**2) as output:
    with zipfile.ZipFile(ForwardOnly(output),'w',allowZip64=True) as archive:
        for item in files:
            assert Path(item['name']).name == item['name']
            checksum=hashlib.sha256()
            with (source/item['name']).open('rb') as reader, archive.open(item['name'],'w',force_zip64=True) as writer:
                while data:=reader.read(4*1024**2):
                    writer.write(data)
                    checksum.update(data)
            assert checksum.hexdigest()==item['sha256']
    output.flush()
    os.fsync(output.fileno())
written=time.monotonic()-start
checksum=hashlib.sha256()
with target.open('rb') as reader:
    while data:=reader.read(4*1024**2): checksum.update(data)
print(json.dumps({'bytes':target.stat().st_size,'write_seconds':written,'total_seconds':time.monotonic()-start,'sha256':checksum.hexdigest()}),flush=True)
