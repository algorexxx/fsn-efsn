package tracing

import (
	"context"
	"reflect"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/node"
	"github.com/FusionFoundation/efsn/v5/rpc"
	"github.com/stretchr/testify/require"
)

func TestGatewayTraceEndpoints(t *testing.T) {
	producer := newTracingNode(t)
	blocks := makeTracingBlocks(t, producer, 4)
	reader, stack := newTracingBackend(t, &node.Config{
		HTTPHost: "127.0.0.1", HTTPModules: []string{"eth", "net", "web3", "fsn", "debug"},
		HTTPVirtualHosts: []string{"localhost"},
		WSHost:           "127.0.0.1", WSModules: []string{"debug"},
	})
	copyTracingHistory(reader, blocks)
	_, apis := stack.GetAPIs()
	var methods []string
	for _, api := range apis {
		if api.Namespace == "debug" {
			service := reflect.TypeOf(api.Service)
			for i := 0; i < service.NumMethod(); i++ {
				methods = append(methods, service.Method(i).Name)
			}
		}
	}
	require.ElementsMatch(t, []string{"TraceBlockByNumber", "TraceBlockByHash", "TraceTransaction", "TraceCall", "TraceChain"}, methods)
	config := map[string]interface{}{"tracer": "callTracer", "reexec": 4}
	expected := []callFrame{{Type: "CALL", From: common.Address{19: 0x11}, To: common.Address{19: 0x22}, Value: "0x7"}}
	for _, endpoint := range []string{stack.HTTPEndpoint(), stack.WSEndpoint()} {
		t.Run(endpoint, func(t *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
			defer cancel()
			client, err := rpc.DialContext(ctx, endpoint)
			require.NoError(t, err)
			defer client.Close()
			modules, err := client.SupportedModules()
			require.NoError(t, err)
			require.Contains(t, modules, "debug")
			require.NotContains(t, modules, "debugadmin")
			for _, method := range []string{
				"debug_setHead", "debug_getBlockRlp", "debug_verbosity", "debug_startCPUProfile",
				"debug_writeBlockProfile", "debug_writeMemProfile", "debug_dumpBlock", "debug_chaindbCompact",
				"debug_traceBlock", "debug_traceBlockFromFile", "debug_standardTraceBlockToFile",
				"debug_standardTraceBadBlockToFile", "debug_traceBadBlock", "debug_intermediateRoots",
				"debugadmin_setHead", "debugadmin_verbosity", "debugadmin_dumpBlock",
			} {
				err := client.CallContext(ctx, nil, method)
				require.Error(t, err, method)
				rpcError, ok := err.(rpc.Error)
				require.True(t, ok, method)
				require.Equal(t, -32601, rpcError.ErrorCode(), method)
			}
			var byNumber, byHash []traceResult
			require.NoError(t, client.CallContext(ctx, &byNumber, "debug_traceBlockByNumber", "0x4", config))
			require.NoError(t, client.CallContext(ctx, &byHash, "debug_traceBlockByHash", blocks[3].Hash(), config))
			require.Equal(t, byNumber, byHash)
			require.Len(t, byNumber, 1)
			require.Empty(t, byNumber[0].Error)
			require.Empty(t, byNumber[0].Result.Error)
			require.Equal(t, expected, byNumber[0].Result.Calls)
			var transaction, call callFrame
			require.NoError(t, client.CallContext(ctx, &transaction, "debug_traceTransaction", blocks[3].Transactions()[0].Hash(), config))
			require.Equal(t, byNumber[0].Result, transaction)
			args := map[string]interface{}{"from": crypto.PubkeyToAddress(tracingKey(t).PublicKey), "to": common.Address{19: 0x11}, "gas": "0x186a0"}
			require.NoError(t, client.CallContext(ctx, &call, "debug_traceCall", args, "0x4", config))
			require.Empty(t, call.Error)
			require.Equal(t, expected, call.Calls)
			for _, tracer := range []string{"callTracerLegacy", "{result: function(){return {};}, fault: function(){}, step: function(){}}"} {
				err := client.CallContext(ctx, nil, "debug_traceTransaction", blocks[3].Transactions()[0].Hash(), map[string]interface{}{"tracer": tracer, "reexec": 4})
				require.EqualError(t, err, "tracer not found")
			}
			if endpoint == stack.WSEndpoint() {
				results := make(chan chainTraceResult, 4)
				subscription, err := client.Subscribe(ctx, "debug", results, "traceChain", "0x0", "0x4", config)
				require.NoError(t, err)
				defer subscription.Unsubscribe()
				for i := 0; i < 4; i++ {
					select {
					case result := <-results:
						require.Equal(t, blocks[i].Hash(), result.Hash)
						require.Len(t, result.Traces, 1)
						require.Empty(t, result.Traces[0].Error)
						require.Empty(t, result.Traces[0].Result.Error)
						require.Equal(t, expected, result.Traces[0].Result.Calls)
					case <-ctx.Done():
						t.Fatal("WebSocket traceChain did not return all blocks")
					}
				}
			}
			require.Equal(t, reader.BlockChain().Genesis().Hash(), reader.BlockChain().CurrentBlock().Hash())
		})
	}
}
