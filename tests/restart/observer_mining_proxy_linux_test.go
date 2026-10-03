package restart

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"sync"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
)

type observerMiningWindow struct {
	GateMethod     string
	PinnedHeight   uint64
	PinnedHash     common.Hash
	AdvancedHeight uint64
	StartedUTC     time.Time
	FinishedUTC    time.Time
	Completed      bool
	Error          string
	Methods        []string
}

type observerMiningProxy struct {
	mu       sync.Mutex
	server   *httptest.Server
	node     *rehearsalNode
	endpoint string
	window   observerMiningWindow
	gate     func(context.Context, observerMiningWindow) (uint64, error)
}

func newObserverMiningProxy(t *testing.T, node *rehearsalNode, endpoint, method string) *observerMiningProxy {
	t.Helper()
	proxy := &observerMiningProxy{node: node, endpoint: endpoint, window: observerMiningWindow{GateMethod: method}}
	proxy.server = httptest.NewServer(proxy)
	t.Cleanup(proxy.server.Close)
	return proxy
}

func (proxy *observerMiningProxy) result() observerMiningWindow {
	proxy.mu.Lock()
	defer proxy.mu.Unlock()
	return proxy.window
}

func (proxy *observerMiningProxy) ServeHTTP(w http.ResponseWriter, request *http.Request) {
	proxy.mu.Lock()
	defer proxy.mu.Unlock()
	raw, err := io.ReadAll(io.LimitReader(request.Body, 1024*1024))
	var call struct {
		Method string
		Params []json.RawMessage
	}
	if err != nil || json.Unmarshal(raw, &call) != nil {
		proxy.window.Error = "invalid test proxy request"
		http.Error(w, proxy.window.Error, http.StatusBadRequest)
		return
	}
	proxy.window.Methods = append(proxy.window.Methods, call.Method)
	switch call.Method {
	case "web3_clientVersion", "net_version", "eth_chainId", "eth_getBlockByNumber", "eth_syncing", "eth_mining", "fsn_isAutoBuyTicket", "eth_coinbase", "net_peerCount", "eth_getTransactionCount", "fsn_getBalance", "fsn_getRawTimeLockBalance", "fsn_allTicketsByAddress", "txpool_content", "eth_getTransactionReceipt", "eth_getRawTransactionByBlockHashAndIndex":
	default:
		proxy.window.Error = "observer attempted a method outside the read allowlist"
		http.Error(w, proxy.window.Error, http.StatusForbidden)
		return
	}
	if call.Method == proxy.window.GateMethod && proxy.window.PinnedHeight != 0 && !proxy.window.Completed {
		proxy.window.StartedUTC = time.Now().UTC()
		if proxy.gate != nil {
			height, err := proxy.gate(request.Context(), proxy.window)
			if err != nil {
				proxy.window.Error = err.Error()
			} else {
				proxy.window.AdvancedHeight, proxy.window.Completed = height, true
			}
		}
		for proxy.gate == nil {
			var current hexutil.Uint64
			if err := proxy.node.client.CallContext(request.Context(), &current, "eth_blockNumber"); err != nil {
				proxy.window.Error = fmt.Sprintf("mining gate read failed: %v", err)
				break
			}
			if uint64(current) > proxy.window.PinnedHeight {
				proxy.window.AdvancedHeight, proxy.window.Completed = uint64(current), true
				break
			}
			select {
			case <-request.Context().Done():
				proxy.window.Error = "mining gate deadline expired"
			case <-time.After(100 * time.Millisecond):
			}
			if proxy.window.Error != "" {
				break
			}
		}
		proxy.window.FinishedUTC = time.Now().UTC()
		if proxy.window.Error != "" {
			http.Error(w, proxy.window.Error, http.StatusGatewayTimeout)
			return
		}
	}
	forward, err := http.NewRequestWithContext(request.Context(), http.MethodPost, proxy.endpoint, bytes.NewReader(raw))
	if err != nil {
		proxy.window.Error = err.Error()
		http.Error(w, proxy.window.Error, http.StatusBadGateway)
		return
	}
	forward.Header.Set("Content-Type", "application/json")
	response, err := http.DefaultClient.Do(forward)
	if err != nil {
		proxy.window.Error = err.Error()
		http.Error(w, proxy.window.Error, http.StatusBadGateway)
		return
	}
	defer response.Body.Close()
	body, err := io.ReadAll(io.LimitReader(response.Body, 32*1024*1024))
	if err != nil {
		proxy.window.Error = err.Error()
		http.Error(w, proxy.window.Error, http.StatusBadGateway)
		return
	}
	if call.Method == "eth_getBlockByNumber" && len(call.Params) > 0 && string(call.Params[0]) == `"latest"` && proxy.window.PinnedHeight == 0 {
		var result struct {
			Result struct {
				Number hexutil.Uint64
				Hash   common.Hash
			}
		}
		if err := json.Unmarshal(body, &result); err != nil {
			proxy.window.Error = err.Error()
		}
		proxy.window.PinnedHeight = uint64(result.Result.Number)
		proxy.window.PinnedHash = result.Result.Hash
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(response.StatusCode)
	_, _ = w.Write(body)
}
