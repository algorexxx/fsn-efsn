package observe

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/rpc"
)

type readClient struct {
	client *rpc.Client
}

func (reader readClient) call(ctx context.Context, result interface{}, method string, args ...interface{}) error {
	switch method {
	case "web3_clientVersion", "net_version", "eth_chainId", "eth_getBlockByNumber", "eth_syncing", "eth_mining", "fsn_isAutoBuyTicket", "eth_coinbase", "net_peerCount", "eth_getTransactionCount", "fsn_getBalance", "fsn_getRawTimeLockBalance", "fsn_allTicketsByAddress", "txpool_content", "eth_getTransactionReceipt", "eth_getRawTransactionByBlockHashAndIndex":
		return reader.client.CallContext(ctx, result, method, args...)
	default:
		return fmt.Errorf("method not allowed by observer")
	}
}

func dial(ctx context.Context, endpoint string) (*rpc.Client, error) {
	if strings.HasPrefix(endpoint, "http://") || strings.HasPrefix(endpoint, "https://") {
		client := &http.Client{Transport: boundedTransport{}, CheckRedirect: func(*http.Request, []*http.Request) error { return fmt.Errorf("redirect refused") }}
		return rpc.DialHTTPWithClient(endpoint, client)
	}
	return rpc.DialIPC(ctx, endpoint)
}

type boundedTransport struct{}

func (boundedTransport) RoundTrip(request *http.Request) (*http.Response, error) {
	response, err := http.DefaultTransport.RoundTrip(request)
	if err != nil {
		return nil, err
	}
	response.Body = &boundedBody{Reader: io.LimitedReader{R: response.Body, N: 8*1024*1024 + 1}, body: response.Body}
	return response, nil
}

type boundedBody struct {
	Reader io.LimitedReader
	body   io.ReadCloser
}

func (body *boundedBody) Read(buffer []byte) (int, error) {
	n, err := body.Reader.Read(buffer)
	if body.Reader.N <= 0 {
		return 0, fmt.Errorf("RPC response exceeds 8 MiB")
	}
	return n, err
}

func (body *boundedBody) Close() error { return body.body.Close() }

func (reader readClient) block(ctx context.Context, number string) (*Block, error) {
	var raw json.RawMessage
	if err := reader.call(ctx, &raw, "eth_getBlockByNumber", number, false); err != nil {
		return nil, err
	}
	var header *types.Header
	var fields struct {
		Hash            common.Hash
		TotalDifficulty *hexutil.Big
	}
	if json.Unmarshal(raw, &header) != nil || header == nil || json.Unmarshal(raw, &fields) != nil || header.Number == nil || !header.Number.IsUint64() || fields.Hash == (common.Hash{}) || header.Hash() != fields.Hash {
		return nil, fmt.Errorf("missing or inconsistent block")
	}
	if number != "latest" && number != hexutil.EncodeUint64(header.Number.Uint64()) {
		return nil, fmt.Errorf("wrong block height")
	}
	return &Block{Header: header, Hash: fields.Hash, TotalDifficulty: fields.TotalDifficulty}, nil
}
