from pathlib import Path
import difflib
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
OLD = Path('/opt/fusion-toolchain/go')
SELECTED = Path('/home/rehearsal/results/restart-release-jwt-2026-10-04')
PRIOR = HERE.parent / 'restart-ticket-compression-2026-10-08'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == '__main__':
    assert not (HERE / 'inputs').exists() and not (HERE / 'preparation.json').exists()
    pinned = json.loads((PRIOR / 'source-inspection.json').read_text(encoding='utf-8'))
    sources = json.loads((PRIOR / 'qualification/run.json').read_text(encoding='utf-8'))
    assert sha(OLD / 'bin/go') == sources['toolchains']['old']['go_binary_sha256']
    target = HERE / 'inputs'
    flate = target / 'internal/ticketgzip/internal/flate'
    flate.mkdir(parents=True)
    provenance = {'upstream': {}, 'base_statedb_sha256': {}, 'candidate_sha256': {}}
    for name, expected in pinned['writer_files'].items():
        source = OLD / 'src/compress/flate' / name
        assert sha(source) == expected['sha256']
        (flate / name).write_bytes(source.read_bytes())
        provenance['upstream'][name] = {'path': str(source), 'sha256': sha(source)}
    inflate = OLD / 'src/compress/flate/inflate.go'
    assert sha(inflate) == sources['toolchains']['old']['compression_source_sha256']['src/compress/flate/inflate.go']
    text = inflate.read_text(encoding='utf-8')
    constant = re.search(r'^\s*maxNumLit\s*=\s*286$', text, re.M)[0].strip()
    definition = re.search(r'type InternalError string\n\nfunc \(e InternalError\) Error\(\) string \{[^\n]+\}', text)[0]
    shared = text[:text.index('\n\n')] + '\n\npackage flate\n\nconst ' + re.sub(r'\s+', ' ', constant) + '\n\n' + definition + '\n'
    (flate / 'shared.go').write_text(shared, encoding='utf-8')
    (flate / 'LICENSE').write_bytes((OLD / 'LICENSE').read_bytes())
    (flate / 'README.md').write_bytes((HERE / 'legacy-README.md').read_bytes())
    provenance['shared_definitions'] = {'path': str(inflate), 'sha256': sha(inflate), 'constant': constant, 'definition': definition}
    provenance['license'] = {'path': str(OLD / 'LICENSE'), 'sha256': sha(OLD / 'LICENSE')}
    (target / 'internal/ticketgzip/encode.go').write_bytes((HERE / 'encode.go').read_bytes())
    path = 'core/state/statedb.go'
    baseline = (SELECTED / 'node' / path).read_text(encoding='utf-8')
    assert (SELECTED / 'node' / path).read_bytes() == (SELECTED / 'recovery' / path).read_bytes()
    provenance['base_statedb_sha256'] = {mode: sha(SELECTED / mode / path) for mode in ['node', 'recovery']}
    before = '\tvar buf bytes.Buffer\n\tzw := gzip.NewWriter(&buf)\n\tif _, err := zw.Write(blob); err != nil {\n\t\treturn nil, fmt.Errorf("Unable to zip tickets data")\n\t}\n\tif err := zw.Close(); err != nil {\n\t\treturn nil, fmt.Errorf("Unable to zip tickets")\n\t}\n\tdata := buf.Bytes()\n\treturn data, nil'
    assert baseline.count(before) == 1
    import_line = '\t"github.com/FusionFoundation/efsn/v5/crypto"\n'
    assert baseline.count(import_line) == 1
    edited = baseline.replace(import_line, import_line + '\t"github.com/FusionFoundation/efsn/v5/internal/ticketgzip"\n').replace(before, '\treturn ticketgzip.Encode(blob)')
    (target / path).parent.mkdir(parents=True)
    (target / path).write_text(edited, encoding='utf-8')
    patch = []
    for file in sorted(target.rglob('*')):
        if not file.is_file():
            continue
        relative = file.relative_to(target).as_posix()
        original = (SELECTED / 'node' / relative)
        old = original.read_text(encoding='utf-8') if original.exists() else ''
        new = file.read_text(encoding='utf-8')
        patch.append('diff --git a/' + relative + ' b/' + relative + '\n')
        patch.extend(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True), fromfile='a/'+relative if original.exists() else '/dev/null', tofile='b/'+relative))
        provenance['candidate_sha256'][relative] = sha(file)
    (HERE / 'candidate.patch').write_text(''.join(patch), encoding='utf-8')
    provenance['patch_sha256'] = sha(HERE / 'candidate.patch')
    (HERE / 'preparation.json').write_text(json.dumps(provenance, indent=2) + '\n', encoding='utf-8')
    print('Prepared', len(provenance['candidate_sha256']), 'runtime/license/document files; selected source unchanged.')
