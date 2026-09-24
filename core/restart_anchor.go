package core

import (
	"fmt"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/ethdb"
	"github.com/FusionFoundation/efsn/v5/params"
	lru "github.com/hashicorp/golang-lru"
)

type restartAnchor struct {
	rule   params.RestartAnchor
	db     ethdb.Database
	proven *lru.Cache
}

func newRestartAnchor(db ethdb.Database, config *params.ChainConfig) (*restartAnchor, error) {
	rule, err := config.RestartAnchorForGenesis(rawdb.ReadCanonicalHash(db, 0))
	if err != nil || rule == nil {
		return nil, err
	}
	cache, _ := lru.New(headerCacheLimit)
	return &restartAnchor{rule: *rule, db: db, proven: cache}, nil
}

func (a *restartAnchor) check(header *types.Header, parents map[common.Hash]*types.Header) error {
	if a == nil {
		return nil
	}
	if header == nil || header.Number == nil || !header.Number.IsUint64() {
		return fmt.Errorf("restart anchor: invalid header number")
	}
	if header.Number.Uint64() < a.rule.Number {
		if rawdb.ReadCanonicalHash(a.db, a.rule.Number) == a.rule.Hash && rawdb.ReadCanonicalHash(a.db, header.Number.Uint64()) != header.Hash() {
			return fmt.Errorf("restart anchor: header conflicts with anchored prefix at %d", header.Number.Uint64())
		}
		return nil
	}
	origin := header.Hash()
	for {
		hash, number := header.Hash(), header.Number.Uint64()
		if number == a.rule.Number {
			if hash != a.rule.Hash {
				return fmt.Errorf("restart anchor: hash mismatch at %d: have %s, want %s", number, hash.Hex(), a.rule.Hash.Hex())
			}
			break
		}
		if a.proven.Contains(hash) {
			break
		}
		parentHash := header.ParentHash
		parent := parents[parentHash]
		provedInBatch := parent != nil
		if parent == nil {
			parent = rawdb.ReadHeader(a.db, parentHash, number-1)
		}
		if parent == nil || parent.Number == nil || !parent.Number.IsUint64() || parent.Number.Uint64() != number-1 || parent.Hash() != parentHash {
			return fmt.Errorf("restart anchor: missing or corrupt ancestor %s at %d", parentHash.Hex(), number-1)
		}
		if provedInBatch {
			break
		}
		header = parent
	}
	if parents == nil {
		a.proven.Add(origin, struct{}{})
	}
	return nil
}

func (a *restartAnchor) checkHeaders(headers []*types.Header) (int, error) {
	if a == nil {
		return 0, nil
	}
	parents := make(map[common.Hash]*types.Header, len(headers))
	for i, header := range headers {
		if err := a.check(header, parents); err != nil {
			return i, err
		}
		parents[header.Hash()] = header
	}
	return 0, nil
}

func (a *restartAnchor) checkBlocks(blocks types.Blocks) (int, error) {
	if a == nil {
		return 0, nil
	}
	headers := make([]*types.Header, len(blocks))
	for i, block := range blocks {
		headers[i] = block.Header()
	}
	return a.checkHeaders(headers)
}

func (a *restartAnchor) checkHead(header, current *types.Header) error {
	if err := a.check(header, nil); err != nil {
		return err
	}
	if a != nil && header.Number.Uint64() < a.rule.Number && current.Number.Uint64() >= a.rule.Number {
		return fmt.Errorf("restart anchor: candidate head is below anchor %d", a.rule.Number)
	}
	return nil
}

func (a *restartAnchor) preflight() error {
	if a == nil {
		return nil
	}
	headHash := rawdb.ReadHeadHeaderHash(a.db)
	headNumber := rawdb.ReadHeaderNumber(a.db, headHash)
	if headNumber == nil {
		return fmt.Errorf("restart anchor: missing persisted header head %s", headHash.Hex())
	}
	for _, hash := range []common.Hash{rawdb.ReadHeadHeaderHash(a.db), rawdb.ReadHeadBlockHash(a.db), rawdb.ReadHeadFastBlockHash(a.db)} {
		number := rawdb.ReadHeaderNumber(a.db, hash)
		if number == nil {
			return fmt.Errorf("restart anchor: missing persisted head %s", hash.Hex())
		}
		if *number > *headNumber {
			return fmt.Errorf("restart anchor: block head %s is above header head", hash.Hex())
		}
		header := rawdb.ReadHeader(a.db, hash, *number)
		if header == nil || header.Hash() != hash || header.Number == nil || !header.Number.IsUint64() || header.Number.Uint64() != *number {
			return fmt.Errorf("restart anchor: corrupt persisted head %s", hash.Hex())
		}
		if err := a.check(header, nil); err != nil {
			return err
		}
	}
	for _, hash := range []common.Hash{rawdb.ReadHeadBlockHash(a.db), rawdb.ReadHeadFastBlockHash(a.db)} {
		number := rawdb.ReadHeaderNumber(a.db, hash)
		if rawdb.ReadBlock(a.db, hash, *number) == nil {
			return fmt.Errorf("restart anchor: missing or corrupt head block %s", hash.Hex())
		}
	}
	for height := *headNumber; height >= a.rule.Number; height-- {
		header := rawdb.ReadHeader(a.db, headHash, height)
		if header == nil || header.Hash() != headHash || rawdb.ReadCanonicalHash(a.db, height) != headHash {
			return fmt.Errorf("restart anchor: inconsistent canonical index at %d", height)
		}
		headHash = header.ParentHash
	}
	if canonical := rawdb.ReadCanonicalHash(a.db, a.rule.Number); canonical != (common.Hash{}) && canonical != a.rule.Hash {
		return fmt.Errorf("restart anchor: inconsistent canonical anchor at %d", a.rule.Number)
	}
	return nil
}

func (bc *BlockChain) CheckRestartReady() error {
	a := bc.hc.restartAnchor
	if a == nil {
		return nil
	}
	head := bc.CurrentBlock().Header()
	if head.Number.Uint64() < a.rule.Number {
		return fmt.Errorf("restart anchor: synchronization required through block %d before mining", a.rule.Number)
	}
	if head.Number.Uint64() > bc.CurrentHeader().Number.Uint64() {
		return fmt.Errorf("restart anchor: full head is above header head")
	}
	return a.check(head, nil)
}

func (hc *HeaderChain) HasRestartAnchor() bool {
	return hc.restartAnchor != nil
}

func (bc *BlockChain) RestartAnchorHeight() uint64 {
	if bc.hc.restartAnchor == nil {
		return 0
	}
	return bc.hc.restartAnchor.rule.Number
}
