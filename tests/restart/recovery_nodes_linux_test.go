package restart

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/internal/recovery"
	"github.com/FusionFoundation/efsn/v5/p2p"
	"github.com/FusionFoundation/efsn/v5/params"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

func TestFullStateRecoveryNodes(t *testing.T) {
	root := os.Getenv("FUSION_RESTART_NODE_COPIES")
	if root == "" {
		t.Skip("requires three guarded construction artifacts and two fresh prepared full-state copies")
	}
	if !filepath.IsAbs(root) || os.Getenv("FUSION_RESTART_NODE_REHEARSAL") != "1" || os.Getenv("FUSION_RESTART_CHAINDATA") != "" {
		t.Fatal("absolute disposable root and isolated node rehearsal required")
	}
	interfaces, err := net.Interfaces()
	requireNoError(t, err)
	if len(interfaces) != 1 || interfaces[0].Flags&net.FlagLoopback == 0 || interfaces[0].Flags&net.FlagUp == 0 {
		t.Fatal("private enabled-loopback-only namespace required")
	}
	if uint64(time.Now().Unix()) >= ticketEnd {
		t.Fatal("test tickets have expired")
	}
	constructed := filepath.Join(root, "guarded-recovery-blocks")
	artifacts := filepath.Join(root, "guarded-recovery-node-blocks")
	requireNoError(t, os.Mkdir(artifacts, 0700))
	blocks := make([]*types.Block, 3)
	for i := range blocks {
		data, err := os.ReadFile(filepath.Join(constructed, fmt.Sprintf("block-%02d.rlp", i+1)))
		requireNoError(t, err)
		requireNoError(t, rlp.DecodeBytes(data, &blocks[i]))
	}
	backupData, donationData := filepath.Join(root, "guarded-recovery-backup"), filepath.Join(root, "guarded-recovery-donation")
	backupPath := seedFullStateRecoveryNode(t, backupData, blocks[2], 1)
	donationPath := seedFullStateRecoveryNode(t, donationData, blocks[2], 2)
	backup := startRehearsalNode(t, backupPath)
	donation := startRehearsalNode(t, donationPath)
	connectRehearsalPeer(t, donation, backup)
	for i, expected := range blocks {
		var plan recovery.Plan
		prefix := filepath.Join(constructed, fmt.Sprintf("recovery-%02d", i+1))
		readHandoverJSON(t, prefix+"-plan.json", &plan)
		purchase, err := os.ReadFile(prefix + "-purchase.rlp")
		requireNoError(t, err)
		producer, receiver := donation, backup
		if i == 0 {
			producer, receiver = backup, donation
		}
		before := producer.status(t)
		bad := plan
		bad.NextTimestamp = bad.Purchase.End + 1
		requireErrorContains(t, producer.call(t, nil, "lab_construct", bad, hexutil.Bytes(purchase)), "remain usable")
		if actual := producer.status(t); actual.Hash != before.Hash || actual.Signatures != before.Signatures {
			t.Fatal("rejected plan signed or advanced a block")
		}
		var hash common.Hash
		requireNoError(t, producer.call(t, &hash, "lab_construct", plan, hexutil.Bytes(purchase)))
		if hash != expected.Hash() {
			t.Fatal("Linux service construction differs from Windows read-only reviewed candidate")
		}
		requireRehearsalHead(t, producer.status(t), expected)
		awaitRehearsal(t, 15*time.Second, func() bool { return receiver.status(t).Hash == expected.Hash() })
		requireRehearsalHead(t, receiver.status(t), expected)
		if status := backup.status(t); status.Signatures != 1 || status.AutoBuy || status.Mining {
			t.Fatal("backup signed more than once or enabled unattended operation")
		}
		t.Logf("controlled stage=%d hash=%s root=%s; rejected unsafe plan before signing; peer imported identical block", i+1, expected.Hash().Hex(), expected.Root().Hex())
	}
	var syncing json.RawMessage
	requireNoError(t, donation.call(t, &syncing, "eth_syncing"))
	if string(syncing) != "false" {
		t.Fatal("donation service is not ready after anchor")
	}
	startRecoveryAutoMiner(t, donation)
	awaitRehearsal(t, 55*time.Second, func() bool { return donation.status(t).Number >= blocks[2].NumberU64()+2 })
	requireNoError(t, donation.call(t, nil, "miner_stopAutoBuyTicket"))
	requireNoError(t, donation.call(t, nil, "miner_stop"))
	fifth := readRecoveryNodeBlock(t, donation, blocks[2].NumberU64()+2)
	requireRehearsalHead(t, donation.status(t), fifth)
	syncRecoveryNode(t, backup, donation, fifth)
	var config nodeRehearsalConfig
	readHandoverJSON(t, filepath.Join(donationPath, "lab.json"), &config)
	config.AutoBuy = true
	var info p2p.NodeInfo
	requireNoError(t, donation.call(t, &info, "admin_nodeInfo"))
	config.ListenAddr = fmt.Sprintf("127.0.0.1:%d", info.Ports.Listener)
	configJSON, err := json.MarshalIndent(config, "", "  ")
	requireNoError(t, err)
	requireNoError(t, os.WriteFile(filepath.Join(donationPath, "lab.json"), configJSON, 0600))
	donation.stop(t, true)
	donation = startRehearsalNode(t, donationPath)
	requireRehearsalHead(t, donation.status(t), fifth)
	requireNoError(t, donation.call(t, nil, "miner_start", 1))
	awaitRehearsal(t, 35*time.Second, func() bool { return donation.status(t).Number > fifth.NumberU64() })
	requireNoError(t, donation.call(t, nil, "miner_stopAutoBuyTicket"))
	requireNoError(t, donation.call(t, nil, "miner_stop"))
	sixth := readRecoveryNodeBlock(t, donation, fifth.NumberU64()+1)
	requireRehearsalHead(t, donation.status(t), sixth)
	syncRecoveryNode(t, backup, donation, sixth)
	if status := backup.status(t); status.Signatures != 1 || status.AutoBuy || status.Mining {
		t.Fatal("retired backup operation changed")
	}
	backup.stop(t, false)
	donation.stop(t, false)
	for i, directory := range []string{backupData, donationData} {
		t.Run(fmt.Sprintf("cold-ledger-%d", i), func(t *testing.T) {
			f, _, funding := openFullStateHandover(t, directory)
			if f.chain.CurrentBlock().Hash() != sixth.Hash() {
				t.Fatal("cold node head mismatch")
			}
			for j := uint64(1); j <= 6; j++ {
				block := f.chain.GetBlockByNumber(funding.Parent.Number.Uint64() + j)
				if block == nil {
					t.Fatal("cold canonical block missing")
				}
				if i == 0 {
					recordFullStateHandoverBlock(t, f, artifacts, funding.Parent.Number.Uint64(), block)
					continue
				}
				parent := f.chain.GetHeader(block.ParentHash(), block.NumberU64()-1)
				ledger := captureFullStateBlock(t, f, parent.Root, block)
				actual, err := json.MarshalIndent(ledger, "", "  ")
				requireNoError(t, err)
				expected, err := os.ReadFile(filepath.Join(artifacts, fmt.Sprintf("block-%02d.json", j)))
				requireNoError(t, err)
				if !bytes.Equal(bytes.TrimSpace(expected), actual) {
					t.Fatal("node receipts, tickets or complete account differences diverged")
				}
			}
		})
	}
	auditFullStateHandover(t, backupData, artifacts, 6)
	t.Logf("two real full-state services: backup signed exactly one controlled block; donation signed jump/cleanup then three ordinary worker blocks, including one after SIGKILL/reopen; final=%s root=%s", sixth.Hash().Hex(), sixth.Root().Hex())
}

func seedFullStateRecoveryNode(t *testing.T, directory string, anchor *types.Block, key byte) string {
	t.Helper()
	requireFullStateCopy(t, directory)
	var funding fullStateHandoverFunding
	readHandoverJSON(t, filepath.Join(directory, "handover.json"), &funding)
	path := t.TempDir()
	requireNoError(t, os.Mkdir(filepath.Join(path, "anchor-lab"), 0700))
	requireNoError(t, os.Symlink(filepath.Join(directory, "chaindata"), filepath.Join(path, "anchor-lab", "chaindata")))
	config := nodeRehearsalConfig{MainnetGenesis: true, TestKey: key, GasLimit: funding.Parent.GasLimit, Anchor: &params.RestartAnchor{GenesisHash: params.MainnetGenesisHash, ChainID: 32659, Number: anchor.NumberU64(), Hash: anchor.Hash()}}
	requireNoError(t, writeStateExportJSON(filepath.Join(path, "lab.json"), config))
	return path
}

func syncRecoveryNode(t *testing.T, local, remote *rehearsalNode, block *types.Block) {
	t.Helper()
	id := connectRehearsalPeer(t, local, remote)
	if local.status(t).Hash != block.Hash() {
		head := remote.status(t)
		requireNoError(t, local.call(t, nil, "lab_sync", id, head.Hash, head.TD))
	}
	requireRehearsalHead(t, local.status(t), block)
}

func startRecoveryAutoMiner(t *testing.T, node *rehearsalNode) {
	t.Helper()
	requireNoError(t, node.call(t, nil, "miner_start", 1))
	awaitRehearsal(t, 5*time.Second, func() bool { return node.status(t).Mining })
	requireNoError(t, node.call(t, nil, "miner_startAutoBuyTicket"))
}

func readRecoveryNodeBlock(t *testing.T, node *rehearsalNode, number uint64) *types.Block {
	t.Helper()
	var data hexutil.Bytes
	requireNoError(t, node.call(t, &data, "lab_block", number))
	var block *types.Block
	requireNoError(t, rlp.DecodeBytes(data, &block))
	return block
}
