package restart

import (
	"fmt"
	"reflect"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/consensus/datong"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/state"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/params"
)

type inspectionChain struct {
	inspectionBackup
}

func (chain inspectionChain) Config() *params.ChainConfig  { return chain.config }
func (chain inspectionChain) CurrentHeader() *types.Header { return &chain.head }
func (chain inspectionChain) GetHeader(hash common.Hash, number uint64) *types.Header {
	return rawdb.ReadHeader(chain.db, hash, number)
}
func (chain inspectionChain) GetHeaderByNumber(number uint64) *types.Header {
	return chain.GetHeader(rawdb.ReadCanonicalHash(chain.db, number), number)
}
func (chain inspectionChain) GetHeaderByHash(hash common.Hash) *types.Header {
	number := rawdb.ReadHeaderNumber(chain.db, hash)
	if number == nil {
		return nil
	}
	return chain.GetHeader(hash, *number)
}
func (chain inspectionChain) GetBlock(hash common.Hash, number uint64) *types.Block {
	return rawdb.ReadBlock(chain.db, hash, number)
}

func TestPreservedTicketReconstruction(t *testing.T) {
	backup := openInspectionBackup(t)
	chain := inspectionChain{backup}
	engine := datong.New(backup.config.DaTong, backup.db)
	t.Cleanup(func() { requireNoError(t, engine.Close()) })
	end := backup.head.Number.Uint64()
	for number := end - 125; number <= end; number++ {
		depths := []uint64{1}
		if number == end {
			depths = append(depths, 16, 126)
		}
		for _, depth := range depths {
			t.Run(fmt.Sprintf("height_%d_missing_%d", number, depth), func(t *testing.T) {
				header := chain.GetHeaderByNumber(number)
				if header == nil {
					t.Fatal("missing preserved header")
				}
				parent := chain.GetHeaderByNumber(number - 1)
				if parent == nil {
					t.Fatal("missing preserved parent")
				}
				expected := types.CopyHeader(header)
				engine.SetStateCache(state.NewDatabase(backup.db))
				evictTicketCache(t, parent.MixDigest)
				requireNoError(t, engine.VerifyHeader(chain, expected, true))
				roots := make(map[common.Hash]bool)
				for missing := number - depth; missing < number; missing++ {
					ancestor := chain.GetHeaderByNumber(missing)
					if ancestor == nil {
						t.Fatalf("missing preserved ancestor %d", missing)
					}
					roots[ancestor.Root] = true
				}
				engine.SetStateCache(&missingStateDatabase{Database: state.NewDatabase(backup.db), roots: roots})
				evictTicketCache(t, parent.MixDigest)

				err := engine.VerifyHeader(chain, header, true)

				requireNoError(t, err)
				if header.Hash() != expected.Hash() || !reflect.DeepEqual(header.GetSelectedTicket(), expected.GetSelectedTicket()) || !reflect.DeepEqual(header.GetRetreatTickets(), expected.GetRetreatTickets()) {
					t.Fatal("reconstruction changed historical header validation or ticket selection")
				}
			})
		}
	}
}
