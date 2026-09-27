package eth

import (
	"bytes"
	"net"
	"os"
	"path/filepath"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/consensus/datong"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/core/vm"
	"github.com/FusionFoundation/efsn/v5/log"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

func TestRestartManualPurchasePeerRetry(t *testing.T) {
	root := os.Getenv("FUSION_RESTART_MANUAL_RETRY")
	if root == "" {
		t.Skip("requires fresh verified disposable copy and private network namespace")
	}
	if !filepath.IsAbs(root) || filepath.Base(root) != "manual-purchase-protocol-2026-09-27-attempt-02" || os.Getenv("FUSION_RESTART_CHAINDATA") != "" {
		t.Fatal("explicit disposable manual-retry root and no original backup required")
	}
	interfaces, err := net.Interfaces()
	retryRequire(t, err)
	if len(interfaces) != 1 || interfaces[0].Flags&net.FlagLoopback == 0 {
		t.Fatal("private loopback-only network namespace required")
	}
	var proof struct {
		Files int
		Bytes int64
	}
	retryReadJSON(t, filepath.Join(root, "copy-capacity.json"), &proof)
	if proof.Files != 300 || proof.Bytes != 574033058 {
		t.Fatal("unexpected disposable source copy")
	}
	log.Root().SetHandler(log.LvlFilterHandler(log.LvlDebug, log.StreamHandler(os.Stderr, log.TerminalFormat(false))))
	datong.InitCheckPoints("")
	evidence := "../docs/evidence/restart-live-funded-partition-2026-09-27"
	encoded, err := os.ReadFile(filepath.Join(evidence, "repair", "original-16.rlp"))
	retryRequire(t, err)
	var tx types.Transaction
	retryRequire(t, tx.UnmarshalBinary(encoded))
	if tx.Nonce() != 16 || tx.Hash() != common.HexToHash("0xb48486a5a0d79ba11ed9c67107e7e83aa886c3309fbb9785fc7cbe21fd9b0e61") {
		t.Fatal("unexpected original manual predecessor")
	}
	blockBytes, err := os.ReadFile(filepath.Join(evidence, "blocks-producer", "block-41.rlp"))
	retryRequire(t, err)
	var block *types.Block
	retryRequire(t, rlp.DecodeBytes(blockBytes, &block))
	if block.NumberU64() != 15130121 || block.Hash() != common.HexToHash("0xf1747659a6150c0def9045519a97f17525b058a20136e17e7c88d768839a1947") {
		t.Fatal("unexpected retained selection block")
	}
	db, err := rawdb.NewLevelDBDatabase(filepath.Join(root, "verifier", "chaindata"), 128, 64, "manual-retry", false)
	retryRequire(t, err)
	defer db.Close()
	config := rawdb.ReadChainConfig(db, rawdb.ReadCanonicalHash(db, 0))
	engine := datong.New(config.DaTong, db)
	chain, err := core.NewBlockChain(db, &core.CacheConfig{TrieDirtyDisabled: true}, config, engine, vm.Config{}, nil)
	retryRequire(t, err)
	defer chain.Stop()
	if chain.CurrentBlock().Hash() != common.HexToHash("0x93ccd33c56bcdff1a572b381887f99eb0ca349af63b63ecffa63858b7cffef77") {
		t.Fatal("copy differs from failed live run")
	}
	fixture := retryPurchaseCase{block, &tx, encoded, 29, "insufficient balance"}
	for _, mode := range []string{"same-peer-resend", "ready-reconnect"} {
		if !t.Run(mode, func(t *testing.T) {
			retryRequire(t, chain.SetHead(block.NumberU64()-1))
			if chain.CurrentBlock().Hash() != block.ParentHash() {
				t.Fatal("disposable rewind missed retained selection parent")
			}
			retryRequire(t, chain.CheckRestartReady())
			rehearseRetryMessages(t, root, mode, chain, db, engine, fixture)
		}) {
			t.Fatal("manual peer retry failed; retain diagnostic state")
		}
	}
	actual, err := rlp.EncodeToBytes(chain.CurrentBlock())
	retryRequire(t, err)
	if !bytes.Equal(actual, blockBytes) {
		t.Fatal("peer-imported block differs from retained selection")
	}
}
