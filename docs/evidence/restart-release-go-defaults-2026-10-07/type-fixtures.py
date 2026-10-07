import difflib
import json
from pathlib import Path


evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
patch = []
for stage, directory in (('baseline', 'restart-release-jwt-2026-10-04'), ('candidate', 'restart-release-text-2026-10-04')):
    source = Path('/home/rehearsal/results') / directory / 'node'
    overlay = {}
    for name in ('core/types/block_test.go', 'core/types/transaction_test.go'):
        old = (source / name).read_text(encoding='utf-8')
        new = (workspace / name).read_text(encoding='utf-8')
        if name.endswith('/block_test.go'):
            expected = old.replace('\t"fmt"\n', '').replace('big.NewInt(1426516743)', 'uint64(1426516743)')
            for line in ('fmt.Println(block.Transactions()[0].Hash())', 'fmt.Println(tx1.data)', 'fmt.Println(tx1.Hash())'):
                expected = expected.replace('\t' + line + '\n', '')
        else:
            expected = old.replace('NewTransactionsByPriceAndNonce(signer, groups)', 'NewTransactionsByPriceAndNonce(signer, groups, nil)')
        assert expected == new
        if stage == 'baseline':
            patch.extend(difflib.unified_diff(old.splitlines(True), new.splitlines(True), fromfile='a/' + name, tofile='b/' + name))
        overlay[str(source / name)] = str(workspace / name)
    (evidence / (stage + '-type-overlay.json')).write_text(json.dumps({'Replace': overlay}, indent=2) + '\n', encoding='utf-8')
(evidence / '10-core-types-fixtures.patch').write_text(''.join(patch), encoding='utf-8')
