package observe

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"math/big"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/rlp"
	"github.com/FusionFoundation/efsn/v5/rpc"
)

var donation = common.HexToAddress("0x2b5ad5c4795c026514f8317c7a215e218dccd6cf")

type retainedRPC struct {
	mu               sync.Mutex
	methods          []string
	blocks           map[uint64]map[string]interface{}
	tickets          map[uint64]map[common.Hash]common.TicketDisplay
	receipts         map[common.Hash]*types.Receipt
	raw              map[string]hexutil.Bytes
	head             *types.Header
	nonce            uint64
	liquid           string
	locks            common.TimeLock
	fail             string
	null             string
	changeRead       int
	headReads        int
	pool             interface{}
	nativeError      bool
	nilLog           bool
	missingStatus    bool
	wrongRaw         bool
	wrongReceiptHash bool
	delay            time.Duration
	chainID          string
	networkID        string
}

func loadRetained(t *testing.T, directory string) *retainedRPC {
	return loadRetainedRole(t, directory, "producer", "audit-")
}

func loadRetainedRole(t *testing.T, directory, role, prefix string) *retainedRPC {
	t.Helper()
	root := filepath.Join("..", "..", "docs", "evidence", directory)
	var inventory struct {
		Header   *types.Header
		Accounts map[common.Address]struct {
			Nonce     uint64
			LiquidWei string
			TimeLocks common.TimeLock
		}
	}
	readFixture(t, filepath.Join(root, "cold-"+role+".json"), &inventory)
	account := inventory.Accounts[donation]
	f := &retainedRPC{blocks: make(map[uint64]map[string]interface{}), tickets: make(map[uint64]map[common.Hash]common.TicketDisplay), receipts: make(map[common.Hash]*types.Receipt), raw: make(map[string]hexutil.Bytes), head: inventory.Header, nonce: account.Nonce, liquid: account.LiquidWei, locks: account.TimeLocks, pool: map[string]interface{}{"pending": map[string]interface{}{}, "queued": map[string]interface{}{}}}
	files, err := filepath.Glob(filepath.Join(root, prefix+role, "block-*.json"))
	if err != nil || len(files) == 0 {
		t.Fatal("retained ledger missing", err)
	}
	for _, file := range files {
		var entry struct {
			Header   *types.Header
			Receipts []*types.Receipt
			Tickets  map[common.Hash]common.TicketDisplay
		}
		readFixture(t, file, &entry)
		f.blocks[entry.Header.Number.Uint64()] = headerResponse(t, entry.Header)
		f.tickets[entry.Header.Number.Uint64()] = entry.Tickets
		data, err := os.ReadFile(strings.TrimSuffix(file, ".json") + ".rlp")
		if err != nil {
			t.Fatal(err)
		}
		var block *types.Block
		if err := rlp.DecodeBytes(data, &block); err != nil {
			t.Fatal(err)
		}
		for i, receipt := range entry.Receipts {
			f.receipts[receipt.TxHash] = receipt
			raw, err := block.Transactions()[i].MarshalBinary()
			if err != nil {
				t.Fatal(err)
			}
			f.raw[receipt.BlockHash.Hex()+":"+hexutil.EncodeUint64(uint64(i))] = raw
		}
	}
	genesis := types.CopyHeader(inventory.Header)
	genesis.Number = new(big.Int)
	genesis.ParentHash = common.Hash{}
	f.blocks[0] = headerResponse(t, genesis)
	return f
}

func headerResponse(t *testing.T, header *types.Header) map[string]interface{} {
	t.Helper()
	raw, err := json.Marshal(header)
	if err != nil {
		t.Fatal(err)
	}
	var result map[string]interface{}
	if err := json.Unmarshal(raw, &result); err != nil {
		t.Fatal(err)
	}
	result["totalDifficulty"] = "0xec12d5178"
	return result
}

func readFixture(t *testing.T, path string, result interface{}) {
	t.Helper()
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if err := json.Unmarshal(raw, result); err != nil {
		t.Fatal(err)
	}
}

func (f *retainedRPC) ServeHTTP(w http.ResponseWriter, request *http.Request) {
	f.mu.Lock()
	defer f.mu.Unlock()
	var call struct {
		ID     json.RawMessage
		Method string
		Params []json.RawMessage
	}
	if err := json.NewDecoder(request.Body).Decode(&call); err != nil {
		panic(err)
	}
	f.methods = append(f.methods, call.Method)
	if f.delay > 0 {
		select {
		case <-request.Context().Done():
			return
		case <-time.After(f.delay):
		}
	}
	response := map[string]interface{}{"jsonrpc": "2.0", "id": call.ID}
	if call.Method == f.fail {
		response["error"] = map[string]interface{}{"code": -32000, "message": "fixture rejection"}
	} else if call.Method == f.null {
		response["result"] = nil
	} else {
		response["result"] = f.reply(call.Method, call.Params)
	}
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(response)
}

func (f *retainedRPC) reply(method string, params []json.RawMessage) interface{} {
	stringArg := func(index int) string { var value string; _ = json.Unmarshal(params[index], &value); return value }
	switch method {
	case "web3_clientVersion":
		return "retained-RPC-fixture"
	case "eth_chainId":
		if f.chainID != "" {
			return f.chainID
		}
		return "0x7f93"
	case "net_version":
		if f.networkID != "" {
			return f.networkID
		}
		return "32659"
	case "eth_syncing", "fsn_isAutoBuyTicket":
		return method == "fsn_isAutoBuyTicket"
	case "eth_mining":
		return true
	case "eth_coinbase":
		return donation
	case "net_peerCount":
		return "0x0"
	case "eth_getBlockByNumber":
		number := f.head.Number.Uint64()
		if stringArg(0) != "latest" {
			number, _ = hexutil.DecodeUint64(stringArg(0))
		}
		if number == f.head.Number.Uint64() {
			f.headReads++
			if f.changeRead > 0 && f.headReads >= f.changeRead {
				return nil
			}
		}
		return f.blocks[number]
	case "eth_getTransactionCount":
		return hexutil.EncodeUint64(f.nonce)
	case "fsn_getBalance":
		return f.liquid
	case "fsn_getRawTimeLockBalance":
		return f.locks
	case "fsn_allTicketsByAddress":
		number, _ := hexutil.DecodeUint64(stringArg(1))
		owner := common.HexToAddress(stringArg(0))
		var result map[common.Hash]common.TicketDisplay
		for hash, ticket := range f.tickets[number] {
			if ticket.Owner == owner {
				if result == nil {
					result = make(map[common.Hash]common.TicketDisplay)
				}
				result[hash] = ticket
			}
		}
		return result
	case "txpool_content":
		return f.pool
	case "eth_getTransactionReceipt":
		receipt := f.receipts[common.HexToHash(stringArg(0))]
		if receipt == nil {
			return nil
		}
		copy := *receipt
		if f.missingStatus {
			raw, _ := json.Marshal(&copy)
			var fields map[string]json.RawMessage
			_ = json.Unmarshal(raw, &fields)
			delete(fields, "status")
			return fields
		}
		if f.nilLog {
			copy.Logs = []*types.Log{nil}
		}
		if f.wrongReceiptHash {
			copy.BlockHash = common.HexToHash("0x1234")
		}
		if f.nativeError && len(copy.Logs) > 0 {
			log := *copy.Logs[0]
			log.Data = []byte(`{"Error":"not enough time lock or asset balance"}`)
			copy.Logs = []*types.Log{&log}
		}
		return &copy
	case "eth_getRawTransactionByBlockHashAndIndex":
		if f.wrongRaw {
			return hexutil.Bytes{1, 2}
		}
		return f.raw[stringArg(0)+":"+stringArg(1)]
	default:
		panic("unexpected or mutating RPC: " + method)
	}
}

func fixtureConfig(t *testing.T, f *retainedRPC) Config {
	t.Helper()
	server := httptest.NewServer(f)
	t.Cleanup(server.Close)
	return Config{ChainID: "32659", NetworkID: "32659", Genesis: common.HexToHash(f.blocks[0]["hash"].(string)), AnchorNumber: 15130083, AnchorHash: common.HexToHash(f.blocks[15130083]["hash"].(string)), Nodes: []NodeConfig{{Name: "donation", Endpoint: server.URL, Role: "producer", Wallet: donation}}}
}

func trackedSaved(t *testing.T) hexutil.Bytes {
	t.Helper()
	data, err := os.ReadFile(filepath.Join("..", "..", "docs", "evidence", "restart-live-abandonment-repair-2026-09-27", "repair", "saved.rlp"))
	if err != nil {
		t.Fatal(err)
	}
	return data
}

func runFixture(t *testing.T, f *retainedRPC, config Config) Report {
	t.Helper()
	now := func() time.Time { return time.Unix(int64(f.head.Time)+1, 0) }
	report, err := Collect(context.Background(), config, 2*time.Second, now)
	if err != nil {
		t.Fatal(err)
	}
	if directory := os.Getenv("FUSION_OBSERVE_EVIDENCE"); directory != "" {
		file, err := os.OpenFile(filepath.Join(directory, strings.ReplaceAll(t.Name(), "/", "-")+".json"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
		if err != nil {
			t.Fatal(err)
		}
		encoder := json.NewEncoder(file)
		encoder.SetIndent("", "  ")
		if err := encoder.Encode(report); err != nil {
			t.Fatal(err)
		}
		if err := file.Close(); err != nil {
			t.Fatal(err)
		}
	}
	return report
}

func TestRetainedRecoveryReceiptsAndZeroPeers(t *testing.T) {
	f := loadRetained(t, "restart-live-abandonment-repair-2026-09-27")
	config := fixtureConfig(t, f)
	config.Tracked = []hexutil.Bytes{trackedSaved(t)}
	var automatic struct{ Raw hexutil.Bytes }
	readFixture(t, filepath.Join("..", "..", "docs", "evidence", "restart-live-abandonment-repair-2026-09-27", "automatic-reinclusion.json"), &automatic)
	config.Tracked = append(config.Tracked, automatic.Raw)
	report := runFixture(t, f, config)
	node := report.Nodes[0]
	if len(node.Issues) != 0 || node.Consistency != "stable" || node.Identity != "matches" || node.Peers == nil || *node.Peers != 0 || node.SavedIntent != "unknown" {
		t.Fatalf("unexpected snapshot: %+v", node)
	}
	if *node.Nonce != 46 || *node.LiquidWei != "23851700263999957552" || !node.TicketsKnown || len(node.Tickets) != 0 {
		t.Fatal("retained account changed")
	}
	if node.Tracked[0].Inclusion != "canonical_native_success" || node.Tracked[0].NonceRelation != "consumed" || node.Tracked[1].Inclusion != "canonical_ordinary_success" || node.Tracked[1].Purchase {
		t.Fatalf("wrong inclusion diagnosis: %+v", node.Tracked)
	}
	if report.Comparison.Status != "not_requested" {
		t.Fatal(report.Comparison)
	}
	t.Log("retained saved purchase 43 and zero-value abandonment 39 independently classified at final block 15130170; zero peers is not a fault")
}

func TestRetainedRollbackAndFundingFailure(t *testing.T) {
	for _, test := range []struct {
		directory string
		nonce     uint64
		funding   string
	}{
		{"restart-abandonment-reorg-2026-09-27", 39, "available_estimate"},
		{"restart-paused-purchases-2026-09-27", 8, "insufficient_estimate"},
	} {
		t.Run(test.directory, func(t *testing.T) {
			f := loadRetained(t, test.directory)
			config := fixtureConfig(t, f)
			config.Tracked = []hexutil.Bytes{trackedSaved(t)}
			node := runFixture(t, f, config).Nodes[0]
			if node.Nonce == nil || uint64(*node.Nonce) != test.nonce || node.Tracked[0].NonceRelation != "ahead" || node.Tracked[0].Inclusion != "absent" || node.Tracked[0].Funding != test.funding || node.SavedIntent != "unknown" {
				t.Fatalf("wrong retained gap/funding: %+v", node)
			}
		})
	}
}

func TestReceiptCannotGiveFalseSuccess(t *testing.T) {
	for _, name := range []string{"native_error", "nil_log", "missing_status", "wrong_raw", "noncanonical", "rpc_error", "snapshot_changed", "identity_mismatch"} {
		t.Run(name, func(t *testing.T) {
			f := loadRetained(t, "restart-live-abandonment-repair-2026-09-27")
			config := fixtureConfig(t, f)
			config.Tracked = []hexutil.Bytes{trackedSaved(t)}
			want := "unknown"
			switch name {
			case "missing_status":
				f.missingStatus = true
			case "nil_log":
				f.nilLog = true
				want = "native_success_unverified"
			case "native_error":
				f.nativeError = true
				want = "native_failed"
			case "wrong_raw":
				f.wrongRaw = true
			case "noncanonical":
				f.wrongReceiptHash = true
				want = "noncanonical"
			case "rpc_error":
				f.fail = "eth_getTransactionReceipt"
			case "snapshot_changed":
				f.changeRead = 2
			case "identity_mismatch":
				config.NetworkID = "1"
			}
			node := runFixture(t, f, config).Nodes[0]
			if node.Tracked[0].Inclusion != want {
				t.Fatalf("got %s, want %s", node.Tracked[0].Inclusion, want)
			}
		})
	}
}

func TestMalformedStateDoesNotPanicOrBecomeZero(t *testing.T) {
	for _, missingItem := range []bool{true, false} {
		f := loadRetained(t, "restart-abandonment-reorg-2026-09-27")
		config := fixtureConfig(t, f)
		config.Tracked = []hexutil.Bytes{trackedSaved(t)}
		if missingItem {
			f.locks.Items = []*common.TimeLockItem{nil}
		} else {
			f.locks.Items = []*common.TimeLockItem{{StartTime: 0, EndTime: 10}}
		}
		report, err := Collect(context.Background(), config, time.Second, func() time.Time { return time.Unix(int64(f.head.Time)+1, 0) })
		if err != nil || report.Nodes[0].TimeLocks != nil || report.Nodes[0].Tracked[0].Funding != "unknown" {
			t.Fatal("malformed funding accepted", err)
		}
	}
}

func TestNullStatusIsUnknown(t *testing.T) {
	for _, method := range []string{"eth_getTransactionCount", "fsn_getBalance", "fsn_getRawTimeLockBalance", "txpool_content", "eth_syncing", "eth_mining", "eth_chainId"} {
		t.Run(method, func(t *testing.T) {
			f := loadRetained(t, "restart-abandonment-reorg-2026-09-27")
			f.null = method
			node := runFixture(t, f, fixtureConfig(t, f)).Nodes[0]
			if len(node.Issues) == 0 {
				t.Fatal("missing status accepted as zero/healthy")
			}
		})
	}
}

func TestMissingDataIsUnknown(t *testing.T) {
	for _, method := range []string{"eth_getTransactionCount", "fsn_getBalance", "fsn_getRawTimeLockBalance", "fsn_allTicketsByAddress", "txpool_content", "eth_syncing", "eth_mining", "eth_chainId"} {
		t.Run(method, func(t *testing.T) {
			f := loadRetained(t, "restart-abandonment-reorg-2026-09-27")
			f.fail = method
			config := fixtureConfig(t, f)
			config.Tracked = []hexutil.Bytes{trackedSaved(t)}
			node := runFixture(t, f, config).Nodes[0]
			if len(node.Issues) == 0 {
				t.Fatal("RPC error hidden")
			}
			if method == "fsn_getBalance" && node.LiquidWei != nil || method == "fsn_getRawTimeLockBalance" && node.TimeLocks != nil || method == "txpool_content" && node.PoolKnown || method == "fsn_allTicketsByAddress" && node.TicketsKnown {
				t.Fatal("unknown was treated as available")
			}
		})
	}
}

func TestCommonHeightAndDivergence(t *testing.T) {
	for _, divergent := range []bool{false, true} {
		t.Run(fmt.Sprint(divergent), func(t *testing.T) {
			first := loadRetained(t, "restart-live-abandonment-repair-2026-09-27")
			second := loadRetained(t, "restart-abandonment-reorg-2026-09-27")
			config := fixtureConfig(t, first)
			other := fixtureConfig(t, second).Nodes[0]
			other.Name, other.Role = "verifier", "verifier"
			config.Nodes = append(config.Nodes, other)
			second.blocks[0] = first.blocks[0]
			if divergent {
				changed := types.CopyHeader(second.head)
				changed.Extra = append(changed.Extra, 1)
				second.blocks[changed.Number.Uint64()] = headerResponse(t, changed)
			}
			report := runFixture(t, first, config)
			want := "same_at_common_height"
			if divergent {
				want = "divergent_at_common_height"
			}
			if report.Comparison.Status != want || report.Comparison.Height != 15130148 {
				t.Fatal(report.Comparison)
			}
		})
	}
}

func TestAllowlistRejectsWritesBeforeTransport(t *testing.T) {
	for _, method := range []string{"eth_sendRawTransaction", "eth_signTransaction", "miner_start", "miner_stop", "miner_startAutoBuyTicket", "admin_addPeer", "personal_unlockAccount", "lab_sync", "lab_purchaseState"} {
		if (readClient{}).call(context.Background(), nil, method) == nil {
			t.Fatal("write/test method allowed", method)
		}
	}
}

func TestDeadlineAndRetiredRole(t *testing.T) {
	f := loadRetained(t, "restart-abandonment-reorg-2026-09-27")
	config := fixtureConfig(t, f)
	f.delay = time.Second
	started := time.Now()
	report, err := Collect(context.Background(), config, 30*time.Millisecond, time.Now)
	if err != nil || time.Since(started) > time.Second || report.Nodes[0].Head != nil || len(report.Nodes[0].Issues) == 0 {
		t.Fatal("deadline did not bound failed observation", err)
	}
	config.Nodes[0].Role = "retired"
	report, err = Collect(context.Background(), config, time.Second, time.Now)
	if err != nil || report.Nodes[0].Consistency != "not_applicable" || len(report.Nodes[0].Issues) != 0 {
		t.Fatal("retired role incorrectly faulted", err)
	}
}

func TestConfigAndResponseBounds(t *testing.T) {
	for _, input := range []string{`{}`, `{"Unknown":1}`, strings.Repeat(" ", 1048577), `{} {}`} {
		if _, err := ReadConfig(strings.NewReader(input)); err == nil {
			t.Fatal("invalid config accepted")
		}
	}
	body := &boundedBody{Reader: io.LimitedReader{R: strings.NewReader("123456"), N: 5}, body: io.NopCloser(strings.NewReader(""))}
	if _, err := io.ReadAll(body); err == nil {
		t.Fatal("response limit not enforced")
	}
	f := loadRetained(t, "restart-abandonment-reorg-2026-09-27")
	config := fixtureConfig(t, f)
	config.Nodes[0].Endpoint = "http://user:secret@example.invalid:1/private?token=hidden"
	config.Nodes[0].Role = "retired"
	report := runFixture(t, f, config)
	raw, _ := json.Marshal(report)
	if bytes.Contains(raw, []byte("secret")) || bytes.Contains(raw, []byte("hidden")) || bytes.Contains(raw, []byte("Endpoint")) {
		t.Fatal("endpoint credentials leaked")
	}
}

func TestRetainedEqualWeightFork(t *testing.T) {
	first := loadRetainedRole(t, "restart-equal-weight-fresh-2026-09-27", "producer", "blocks-")
	second := loadRetainedRole(t, "restart-equal-weight-fresh-2026-09-27", "verifier", "blocks-")
	config := fixtureConfig(t, first)
	other := fixtureConfig(t, second).Nodes[0]
	other.Name, other.Role = "verifier", "verifier"
	config.Nodes = append(config.Nodes, other)
	second.blocks[0] = first.blocks[0]
	first.blocks[15130119]["totalDifficulty"], second.blocks[15130119]["totalDifficulty"] = "0xec12d513e", "0xec12d513e"
	report := runFixture(t, first, config)
	if report.Comparison.Status != "divergent_at_common_height" || report.Comparison.Height != 15130119 || report.Comparison.Hashes[0] != common.HexToHash("0x0b7a9403295c31f79a3141da6510ae0437a6e600c2359b48e31eedfd1a784795") || report.Comparison.Hashes[1] != common.HexToHash("0x30c87783b92511a852750c9b49ac163db92b33a7fcb8c33ab70bf98e0a1b15f5") {
		t.Fatal(report.Comparison)
	}
}

func TestExpiredTrackedPurchase(t *testing.T) {
	f := loadRetained(t, "restart-abandonment-reorg-2026-09-27")
	config := fixtureConfig(t, f)
	config.Tracked = []hexutil.Bytes{trackedSaved(t)}
	changed := types.CopyHeader(f.head)
	changed.Time += 31 * 24 * 3600
	f.head = changed
	f.blocks[changed.Number.Uint64()] = headerResponse(t, changed)
	node := runFixture(t, f, config).Nodes[0]
	if node.Tracked[0].Payload != "invalid" || node.Tracked[0].Inclusion != "absent" || node.Tracked[0].Funding != "unknown" {
		t.Fatal(node.Tracked)
	}
}

func TestPartialLocksCannotCombineWithPartialLiquid(t *testing.T) {
	f := loadRetained(t, "restart-abandonment-reorg-2026-09-27")
	config := fixtureConfig(t, f)
	config.Tracked = []hexutil.Bytes{trackedSaved(t)}
	f.liquid = "2500000000000000000000"
	value, _ := new(big.Int).SetString("2500000000000000000000", 10)
	f.locks = *common.NewTimeLock(&common.TimeLockItem{StartTime: 0, EndTime: common.TimeLockForever, Value: value})
	node := runFixture(t, f, config).Nodes[0]
	if node.Tracked[0].Funding != "insufficient_estimate" || node.Tracked[0].RequiredLiquidWei != "5000000021224000021224" {
		t.Fatal(node.Tracked)
	}
}

func TestPendingTrackedTransaction(t *testing.T) {
	f := loadRetained(t, "restart-abandonment-reorg-2026-09-27")
	config := fixtureConfig(t, f)
	config.Tracked = []hexutil.Bytes{trackedSaved(t)}
	var tx types.Transaction
	if err := tx.UnmarshalBinary(config.Tracked[0]); err != nil {
		t.Fatal(err)
	}
	f.pool = map[string]interface{}{"pending": map[string]interface{}{}, "queued": map[common.Address]interface{}{donation: map[string]interface{}{"43": &tx}}}
	node := runFixture(t, f, config).Nodes[0]
	if !node.PoolKnown || node.Tracked[0].Pool != "queued" || node.Tracked[0].NonceRelation != "ahead" || node.Tracked[0].Inclusion != "absent" {
		t.Fatal(node.Tracked)
	}
}

type observerIPCAPI struct{}

func (*observerIPCAPI) Version() string { return "32659" }

func TestIPCReadTransport(t *testing.T) {
	endpoint := filepath.Join(t.TempDir(), "observe.ipc")
	if runtime.GOOS == "windows" {
		endpoint = fmt.Sprintf(`\\.\pipe\fsn-observe-test-%d`, os.Getpid())
	}
	listener, server, err := rpc.StartIPCEndpoint(endpoint, []rpc.API{{Namespace: "net", Service: &observerIPCAPI{}}})
	if err != nil {
		t.Fatal(err)
	}
	defer listener.Close()
	defer server.Stop()
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()
	client, err := dial(ctx, endpoint)
	if err != nil {
		t.Fatal(err)
	}
	defer client.Close()
	var network string
	if err := (readClient{client}).call(ctx, &network, "net_version"); err != nil || network != "32659" {
		t.Fatal(network, err)
	}
}
