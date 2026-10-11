package tracers

import (
	"context"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/internal/ethapi"
	"github.com/FusionFoundation/efsn/v5/rpc"
)

type TraceAPI struct {
	api *API
}

func (api *TraceAPI) TraceBlockByNumber(ctx context.Context, number rpc.BlockNumber, config *TraceConfig) ([]*txTraceResult, error) {
	return api.api.TraceBlockByNumber(ctx, number, config)
}

func (api *TraceAPI) TraceBlockByHash(ctx context.Context, hash common.Hash, config *TraceConfig) ([]*txTraceResult, error) {
	return api.api.TraceBlockByHash(ctx, hash, config)
}

func (api *TraceAPI) TraceTransaction(ctx context.Context, hash common.Hash, config *TraceConfig) (interface{}, error) {
	return api.api.TraceTransaction(ctx, hash, config)
}

func (api *TraceAPI) TraceCall(ctx context.Context, args ethapi.TransactionArgs, block rpc.BlockNumberOrHash, config *TraceCallConfig) (interface{}, error) {
	return api.api.TraceCall(ctx, args, block, config)
}

func (api *TraceAPI) TraceChain(ctx context.Context, start, end rpc.BlockNumber, config *TraceConfig) (*rpc.Subscription, error) {
	return api.api.TraceChain(ctx, start, end, config)
}
