package restart

import (
	"encoding/json"
	"os"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/params"
	"golang.org/x/sys/unix"
)

func TestCompleteBackupStartupPreflight(t *testing.T) {
	directory := os.Getenv("FUSION_STARTUP_BACKUP_VIEW")
	if directory == "" {
		t.Skip("requires an explicit read-only backup mount")
	}
	var mount unix.Statfs_t
	requireNoError(t, unix.Statfs(directory, &mount))
	if mount.Flags&unix.ST_RDONLY == 0 {
		t.Fatal("read-only mount required")
	}
	db, err := rawdb.NewLevelDBDatabase(directory, 16, 16, "", true)
	requireNoError(t, err)
	defer db.Close()
	genesis := common.HexToHash("0xc2422b1d9d16331be2a5b207c0783027d4419498003f729f4b9e9c5c1838623a")
	head := common.HexToHash("0xe93ffded087a79097d4309c7831690161db6ed136f4b1a22c4c83a99db80f99f")
	if rawdb.ReadCanonicalHash(db, 0) != genesis || rawdb.ReadHeadBlockHash(db) != head || rawdb.ReadCanonicalHash(db, 15130080) != head {
		t.Fatal("preserved identity mismatch")
	}
	config := *params.MainnetChainConfig
	config.RestartAnchor = &params.RestartAnchor{GenesisHash: genesis, ChainID: 32659, Number: 15130080, Hash: head}
	previous := params.MainnetChainConfig
	params.MainnetChainConfig = &config
	t.Cleanup(func() { params.MainnetChainConfig = previous })
	requireNoError(t, core.CheckRestoredState(db, &config, genesis))
	header := rawdb.ReadHeader(db, head, 15130080)
	if header == nil {
		t.Fatal("head header missing")
	}
	blob, err := json.Marshal(map[string]interface{}{"genesis": genesis, "height": header.Number.Uint64(), "hash": header.Hash(), "root": header.Root, "tickets": header.MixDigest, "startup_check_passed": true, "read_only_mount": true, "test_anchor_only": true})
	requireNoError(t, err)
	t.Logf("BACKUPSTARTUP %s", blob)
}
