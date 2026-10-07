from pathlib import Path
import re


workspace = Path(__file__).resolve().parents[3]
for name in ('state_test.go', 'statedb_test.go', 'iterator_test.go', 'sync_test.go'):
    path = workspace / 'core/state' / name
    text = path.read_text(encoding='utf-8')
    assert 'ethdb.NewMemDatabase()' in text or name == 'iterator_test.go'
    if name != 'iterator_test.go':
        text = text.replace('"github.com/FusionFoundation/efsn/v5/ethdb"', '"github.com/FusionFoundation/efsn/v5/ethdb"\n\t"github.com/FusionFoundation/efsn/v5/core/rawdb"')
    text = text.replace('ethdb.NewMemDatabase()', 'rawdb.NewMemoryDatabase()')
    text = text.replace('*ethdb.MemDatabase', 'ethdb.Database')
    text = re.sub(r'(?<![\w.])New\((common\.Hash\{\}|root), ', r'New(\1, common.Hash{}, ', text)
    text = re.sub(r'\.(AddBalance|SetBalance)\(addr, ', r'.\1(addr, common.SystemAssetID, ', text)
    text = text.replace('.AddBalance(common.Address{}, ', '.AddBalance(common.Address{}, common.SystemAssetID, ')
    text = re.sub(r'\.(AddBalance|SetBalance)\((big\.NewInt\()', r'.\1(common.SystemAssetID, \2', text)
    text = re.sub(r'\.GetBalance\((addr|acc\.address)\)', r'.GetBalance(common.SystemAssetID, \1)', text)
    text = text.replace('.Balance()', '.Balance(common.SystemAssetID)')
    text = text.replace('s.state.Dump()', 's.state.Dump(nil)')
    text = text.replace('db.Keys()', 'stateDatabaseKeys(t, db)')
    text = text.replace('finalDb.Keys()', 'stateDatabaseKeys(t, finalDb)')
    text = text.replace('transDb.Keys()', 'stateDatabaseKeys(t, transDb)')
    if name == 'statedb_test.go':
        text = text.replace('config := &quick.Config{MaxCount: 1000}', 'config := &quick.Config{MaxCount: 1000, Rand: rand.New(rand.NewSource(1))}')
        text = text.replace('for _, i := range action.args {\n\t\taction.args[i] = rand.Int63n(100)', 'for i := range action.args {\n\t\taction.args[i] = r.Int63n(100)')
        text = text.replace('checkstate.ForEachStorage(addr, func(key, value common.Hash) bool {\n\t\t\t\treturn checkeq("GetState("+key.Hex()+")", checkstate.GetState(addr, key), value)', 'checkstate.ForEachStorage(addr, func(key, value common.Hash) bool {\n\t\t\t\treturn checkeq("GetState("+key.Hex()+")", state.GetState(addr, key), value)')
    path.write_text(text, encoding='utf-8', newline='\n')
