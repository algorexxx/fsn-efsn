package restart

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/accounts"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/internal/recovery"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

func TestFullStateRecoveryConstruction(t *testing.T) {
	directory := os.Getenv("FUSION_RESTART_HANDOVER_DIR")
	if directory == "" {
		t.Skip("requires a verified disposable full-state handover copy")
	}
	requireFullStateCopy(t, directory)
	artifacts := os.Getenv("FUSION_RESTART_HANDOVER_BLOCKS")
	if !filepath.IsAbs(artifacts) {
		t.Fatal("absolute artifact directory required")
	}
	f, _, funding := openFullStateHandover(t, directory)
	index := f.chain.CurrentBlock().NumberU64() - funding.Parent.Number.Uint64()
	if index > 2 {
		t.Fatal("construction only covers the three controlled recovery blocks")
	}
	successor := *f
	selectHandoverSuccessor(t, &successor, funding)
	signer := f
	if index > 0 {
		signer = &successor
	}
	parent := f.chain.CurrentBlock()
	timestamp, next := parent.Time()+120, jumpTime
	if index > 0 {
		timestamp, next = jumpTime+(index-1)*120, jumpTime+index*120
	}
	if index == 2 {
		next = uint64(time.Now().Unix()) + 3600
	}
	prefix := filepath.Join(artifacts, fmt.Sprintf("recovery-%02d", index+1))
	if os.Getenv("FUSION_RESTART_HANDOVER_MODE") == "plan" {
		tx := successor.signPurchase(t, parent.Time(), ticketEnd)
		plan := recoveryPlan(t, signer, &successor, timestamp, next, tx)
		requireNoError(t, writeStateExportJSON(prefix+"-plan.json", plan))
		encoded, err := rlp.EncodeToBytes(tx)
		requireNoError(t, err)
		requireNoError(t, os.WriteFile(prefix+"-purchase.rlp", encoded, 0600))
		return
	}
	if os.Getenv("FUSION_RESTART_HANDOVER_MODE") != "produce" {
		t.Fatal("mode must be plan or produce")
	}
	var plan recovery.Plan
	readHandoverJSON(t, prefix+"-plan.json", &plan)
	encoded, err := os.ReadFile(prefix + "-purchase.rlp")
	requireNoError(t, err)
	var tx types.Transaction
	requireNoError(t, rlp.DecodeBytes(encoded, &tx))
	candidate, err := recovery.Build(f.chain, plan, types.Transactions{&tx})
	requireNoError(t, err)
	var report struct{ UnsignedBlock hexutil.Bytes }
	reportData, err := os.ReadFile(prefix + "-report.json")
	requireNoError(t, err)
	requireNoError(t, json.Unmarshal(reportData, &report))
	actual, err := rlp.EncodeToBytes(candidate.Block)
	requireNoError(t, err)
	if !bytes.Equal(actual, report.UnsignedBlock) {
		t.Fatal("read-only command and live-chain builder differ")
	}
	f.engine.Authorize(signer.owner, func(_ accounts.Account, _ string, payload []byte) ([]byte, error) {
		return crypto.Sign(crypto.Keccak256(payload), signer.key)
	})
	sealed := make(chan *types.Block, 1)
	stop := make(chan struct{})
	defer close(stop)
	requireNoError(t, f.engine.Seal(f.chain, candidate.Block, sealed, stop))
	select {
	case block := <-sealed:
		f.importBlock(t, block)
		recordFullStateHandoverBlock(t, f, artifacts, funding.Parent.Number.Uint64(), block)
	case <-time.After(5 * time.Second):
		t.Fatal("historical guarded block was not sealed")
	}
}
