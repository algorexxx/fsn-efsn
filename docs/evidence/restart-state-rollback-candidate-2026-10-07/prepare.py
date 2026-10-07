from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
SELECTION = Path('/home/rehearsal/results/restart-release-jwt-2026-10-04')
FILES = [
    'params/config.go', 'core/genesis.go', 'core/state/statedb.go',
    'core/vm/interface.go', 'core/vm/noop.go', 'core/vm/instructions.go',
    'internal/recovery/chain.go', 'core/state/statedb_test.go',
]


def replace_once(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new)


def edit(path, text):
    if path == 'params/config.go':
        text = replace_once(text, '\tRestartAnchor *RestartAnchor', '\tSuicideTimeLockFixBlock *big.Int `json:"suicideTimeLockFixBlock,omitempty"`\n\n\tRestartAnchor *RestartAnchor')
        for name in ['AllEthashProtocolChanges', 'AllCliqueProtocolChanges', 'TestChainConfig']:
            lines = text.splitlines(keepends=True)
            found = [i for i, line in enumerate(lines) if line.startswith('\t' + name + ' = &ChainConfig{')]
            assert len(found) == 1, name
            i = found[0]
            lines[i] = lines[i].rstrip('\n')[:-1] + ', nil}\n'
            text = ''.join(lines)
        text = replace_once(text, '\tif c.EcoBlock != nil {', '\tif c.SuicideTimeLockFixBlock != nil {\n\t\tbanner += fmt.Sprintf(" - Suicide time-lock rollback fix: %v\\n", c.SuicideTimeLockFixBlock)\n\t}\n\tif c.EcoBlock != nil {')
        text = replace_once(text, 'func (c *ChainConfig) checkCompatible(newcfg *ChainConfig, head *big.Int) *ConfigCompatError {', 'func (c *ChainConfig) checkCompatible(newcfg *ChainConfig, head *big.Int) *ConfigCompatError {\n\tif err := c.CheckSuicideTimeLockFixCompatible(newcfg, head.Uint64()); err != nil {\n\t\treturn err\n\t}')
        text = replace_once(text, 'type Rules struct {', 'type Rules struct {\n\tIsSuicideTimeLockFix bool')
        text = replace_once(text, '\treturn Rules{', '\treturn Rules{\n\t\tIsSuicideTimeLockFix: c.IsSuicideTimeLockFix(num),')
    elif path == 'core/state/statedb.go':
        text = replace_once(text, 'func (s *StateDB) Suicide(addr common.Address) bool {', 'func (s *StateDB) Suicide(addr common.Address, fixTimeLockJournal bool) bool {')
        text = replace_once(text, '\t\t\tprevTimeLockBalance: new(common.TimeLock).Set(v),', '\t\t\tprevTimeLockBalance: new(common.TimeLock).Set(v),\n\t\t\tisTimeLock:          fixTimeLockJournal,')
    elif path == 'core/vm/interface.go':
        text = replace_once(text, 'Suicide(common.Address) bool', 'Suicide(common.Address, bool) bool')
    elif path == 'core/vm/noop.go':
        text = replace_once(text, 'Suicide(common.Address) bool', 'Suicide(common.Address, bool) bool')
    elif path == 'core/vm/instructions.go':
        text = replace_once(text, 'StateDB.Suicide(scope.Contract.Address())', 'StateDB.Suicide(scope.Contract.Address(), interpreter.evm.chainRules.IsSuicideTimeLockFix)')
    elif path == 'core/state/statedb_test.go':
        text = replace_once(text, 's.Suicide(addr)', 's.Suicide(addr, false)')
    elif path == 'internal/recovery/chain.go':
        text = replace_once(text, '\tcache := state.NewDatabase(db)', '\tconfig, err := params.ResolveSuicideTimeLockFix(config, rawdb.ReadCanonicalHash(db, 0), *number)\n\tif err != nil {\n\t\treturn nil, err\n\t}\n\tcache := state.NewDatabase(db)')
    elif path == 'core/genesis.go':
        text = replace_once(text, '\t\tblock, err := genesis.Commit(db)', '\t\tconfig, err := params.ResolveSuicideTimeLockFix(genesis.Config, genesis.ToBlock(nil).Hash(), 0)\n\t\tif err != nil {\n\t\t\treturn genesis.Config, common.Hash{}, err\n\t\t}\n\t\tcopy := *genesis\n\t\tcopy.Config = config\n\t\tgenesis = &copy\n\t\tblock, err := genesis.Commit(db)')
        height = '\theight := rawdb.ReadHeaderNumber(db, rawdb.ReadHeadHeaderHash(db))\n\tif height == nil {\n\t\treturn newcfg, stored, fmt.Errorf("missing block number for head header hash")\n\t}\n'
        text = replace_once(text, height, '')
        text = replace_once(text, '\tstoredcfg := rawdb.ReadChainConfig(db, stored)', height + '\tresolved, err := params.ResolveSuicideTimeLockFix(newcfg, stored, *height)\n\tif err != nil {\n\t\treturn newcfg, stored, err\n\t}\n\tnewcfg = resolved\n\tstoredcfg := rawdb.ReadChainConfig(db, stored)')
        text = replace_once(text, '\tif storedcfg == nil {', '\tif storedcfg == nil {\n\t\tif newcfg.IsSuicideTimeLockFix(new(big.Int).SetUint64(*height)) {\n\t\t\treturn newcfg, stored, fmt.Errorf("suicide time-lock fix: missing configuration after activation")\n\t\t}')
        text = replace_once(text, '\t// Special case: don\'t change', '\tstoredcfg, err = params.ResolveSuicideTimeLockFix(storedcfg, stored, *height)\n\tif err != nil {\n\t\treturn newcfg, stored, err\n\t}\n\t// Special case: don\'t change')
        text = replace_once(text, '\tcompatErr := storedcfg.CheckCompatible(newcfg, *height)', '\tif err := storedcfg.CheckSuicideTimeLockFixCompatible(newcfg, *height); err != nil {\n\t\treturn newcfg, stored, fmt.Errorf("suicide time-lock fix: incompatible execution schedule: %v", err)\n\t}\n\tcompatErr := storedcfg.CheckCompatible(newcfg, *height)')
    return text


if __name__ == '__main__':
    manifest_path = HERE / 'base-inputs.json'
    assert not manifest_path.exists(), 'Existing preparation is immutable; use a new evidence directory.'
    manifest = {'selection': 'P1-P17+B1+D1', 'trees': {}, 'files': {}}
    for name in FILES:
        sources = {label: SELECTION / label / name for label in ['node', 'recovery'] if (SELECTION / label / name).is_file()}
        assert sources, name
        data = next(iter(sources.values())).read_bytes()
        assert all(p.read_bytes() == data for p in sources.values()), name
        manifest['files'][name] = {'sha256': hashlib.sha256(data).hexdigest(), 'trees': list(sources)}
        dest = HERE / 'inputs' / name
        assert not dest.exists(), dest
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(edit(name, data.decode('utf-8')), encoding='utf-8', newline='\n')
    for label in ['node', 'recovery']:
        manifest['trees'][label] = {'path': str(SELECTION / label), 'go.mod': hashlib.sha256((SELECTION / label / 'go.mod').read_bytes()).hexdigest(), 'go.sum': hashlib.sha256((SELECTION / label / 'go.sum').read_bytes()).hexdigest()}
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print('Prepared', len(manifest['files']), 'candidate inputs from the selected source trees.')
