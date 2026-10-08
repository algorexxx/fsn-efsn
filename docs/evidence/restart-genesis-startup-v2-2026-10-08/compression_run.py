from pathlib import Path
import base64
import datetime
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
RUN = Path('/home/rehearsal/results/restart-genesis-compression-2026-10-08')
SOURCE = Path('/home/rehearsal/results/restart-release-jwt-2026-10-04/node')
COMPILERS = {'old': Path('/opt/fusion-toolchain/go'), 'new': Path('/home/rehearsal/results/restart-release-selection-2026-10-04/toolchain/go')}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def execute(name, argv, env, record):
    entry = {'name': name, 'argv': argv, 'started': now()}
    suffix = '.gz' if name.endswith('-compress') else '.txt'
    with (RUN / (name + suffix)).open('wb') as output, (RUN / (name + '.stderr.txt')).open('wb') as errors:
        entry['exit'] = subprocess.run(argv, cwd=SOURCE, env=env, stdout=output, stderr=errors).returncode
    entry['finished'] = now()
    record['commands'].append(entry)
    (RUN / 'run.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(name, entry['exit'], flush=True)
    if entry['exit']:
        shutil.copytree(RUN, HERE / 'compression', ignore=shutil.ignore_patterns('bin', 'tmp'))
        sys.exit(1)


if __name__ == '__main__':
    assert not RUN.exists()
    assert os.getuid() == 1000 and len(sys.argv) == 2 and sys.argv[1] != os.readlink('/proc/self/ns/net')
    capacity = {p: shutil.disk_usage(p).free for p in ['/home/rehearsal/results', '/mnt/d']}
    assert capacity['/home/rehearsal/results'] > 30*1024**3 and capacity['/mnt/d'] > 60*1024**3
    for root in COMPILERS.values():
        assert (root / 'bin/go').is_file()
    subprocess.run([str(COMPILERS['new'] / 'bin/gofmt'), '-w', str(HERE / 'compress.go'), str(HERE / 'ticket_probe.go')], check=True)
    RUN.mkdir()
    (RUN / 'bin').mkdir()
    (RUN / 'tmp').mkdir()
    record = {'started': now(), 'uid': os.getuid(), 'namespace': os.readlink('/proc/self/ns/net'), 'parent_namespace': sys.argv[1], 'links': subprocess.check_output(['ip','-brief','link'],text=True), 'capacity_bytes': capacity, 'input_sha256': {n:sha(HERE/n) for n in ['compress.go','ticket_probe.go','compression-spec.md','compression_run.py','compression_launch.py']}, 'startup_run_sha256': sha(HERE / 'qualification/run.json'), 'commands': [], 'toolchains': {}, 'source_sha256': {}}
    initial = json.loads((HERE/'qualification/run.json').read_text(encoding='utf-8'))
    for relative, expected in initial['source_sha256'].items():
        assert sha(SOURCE / relative) == expected
        record['source_sha256'][relative] = expected
    environments = {}
    for name, root in COMPILERS.items():
        env = os.environ.copy()
        for key in ['GODEBUG','GOEXPERIMENT','GOENV','GOFLAGS','GOOS','GOARCH','GO111MODULE']:
            env.pop(key,None)
        env.update(PATH=str(root/'bin')+':/usr/bin:/bin',GOENV='off',GOTOOLCHAIN='local',GOWORK='off',GOPROXY='off',GOSUMDB='off',GOFLAGS='-mod=readonly',CGO_ENABLED='1',GOAMD64='v1',GOMAXPROCS='2',GOCACHE='/home/rehearsal/.cache/go-build' if name=='old' else '/home/rehearsal/results/restart-release-selection-2026-10-04/repeat-cache',GOMODCACHE='/home/rehearsal/go/pkg/mod',GOTMPDIR=str(RUN/'tmp'),TMPDIR=str(RUN/'tmp'))
        environments[name] = env
        record['toolchains'][name] = {'root':str(root),'go_binary_sha256':sha(root/'bin/go'),'go_env':json.loads(subprocess.check_output(['go','env','-json'],cwd=SOURCE,env=env,text=True)), 'compression_source_sha256':{f.relative_to(root).as_posix():sha(f) for folder in ['src/compress/gzip','src/compress/flate'] for f in sorted((root/folder).glob('*.go'))}}
    def build(name, source, compiler):
        command=['timeout','--kill-after=20s','7m','go','build','-p=2','-trimpath','-buildvcs=false','-o',str(RUN/'bin'/name),str(HERE/source)]
        env=environments[compiler].copy()
        if source=='compress.go':
            env.update(GO111MODULE='off',GOFLAGS='')
        execute(name+'-build',command,env,record)
        record.setdefault('binary_sha256',{})[name]=sha(RUN/'bin'/name)
    build('ticket-probe','ticket_probe.go','new')
    execute('export',[str(RUN/'bin/ticket-probe')],environments['new'],record)
    exported=json.loads((RUN/'export.txt').read_text(encoding='utf-8'))
    payload=base64.b64decode(exported['Payload'],validate=True)
    (RUN/'tickets.rlp').write_bytes(payload)
    for compiler in COMPILERS:
        build(compiler+'-gzip','compress.go',compiler)
        execute(compiler+'-compress',[str(RUN/'bin'/(compiler+'-gzip')),str(RUN/'tickets.rlp')],environments[compiler],record)
        assert gzip.decompress((RUN/(compiler+'-compress.gz')).read_bytes())==payload
    assert (RUN/'new-compress.gz').read_bytes()==base64.b64decode(exported['Compressed'],validate=True)
    execute('substitute',[str(RUN/'bin/ticket-probe'),str(RUN/'old-compress.gz')],environments['new'],record)
    retained = HERE.parent / 'restart-2026-09-23/responses.json'
    responses=json.loads(retained.read_text(encoding='utf-8'))
    historical=next(x['result'] for x in responses if x['id']==2)
    (RUN/'historical-genesis.json').write_text(json.dumps(historical,indent=2)+'\n',encoding='utf-8')
    record.update(finished=now(),historical_response_sha256=sha(retained),payload_bytes=len(payload),output_bytes={n:(RUN/(n+'-compress.gz')).stat().st_size for n in COMPILERS})
    (RUN/'run.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    shutil.copytree(RUN,HERE/'compression',ignore=shutil.ignore_patterns('bin','tmp'))
