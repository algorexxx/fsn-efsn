package observe

import (
	"encoding/json"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core/types"
)

type Config struct {
	ChainID      string
	NetworkID    string
	Genesis      common.Hash
	AnchorNumber uint64
	AnchorHash   common.Hash
	Nodes        []NodeConfig
	Tracked      []hexutil.Bytes
}

type NodeConfig struct {
	Name     string
	Endpoint string
	Role     string
	Wallet   common.Address
}

type Report struct {
	Version     int
	StartedUTC  time.Time
	FinishedUTC time.Time
	Nodes       []Observation
	Comparison  Comparison
	Limitations []string
}

type Observation struct {
	Name          string
	Role          string
	Wallet        common.Address
	StartedUTC    time.Time
	FinishedUTC   time.Time
	ClientVersion *string
	ChainID       *hexutil.Big
	NetworkID     *string
	Head          *Block
	Genesis       *Block
	Anchor        *Block
	Identity      string
	Consistency   string
	Syncing       json.RawMessage
	Mining        *bool
	AutoBuy       *bool
	Coinbase      *common.Address
	Peers         *hexutil.Uint64
	Nonce         *hexutil.Uint64
	LiquidWei     *string
	TimeLocks     *common.TimeLock
	Tickets       map[common.Hash]common.TicketDisplay
	TicketsKnown  bool
	Pool          []PoolTransaction
	PoolKnown     bool
	Tracked       []TransactionObservation
	SavedIntent   string
	Issues        []Issue
}

type Block struct {
	Header          *types.Header
	Hash            common.Hash
	TotalDifficulty *hexutil.Big
}

type PoolTransaction struct {
	Queue       string
	Transaction *types.Transaction
}

type TransactionObservation struct {
	Hash              common.Hash
	Nonce             uint64
	Owner             common.Address
	Raw               hexutil.Bytes
	Pool              string
	Receipt           *types.Receipt
	Inclusion         string
	Purchase          bool
	Payload           string
	Funding           string
	Interval          *common.BuyTicketParam
	CoverageWei       string
	RequiredLiquidWei string
	NonceRelation     string
}

type Issue struct {
	Field string
	Code  string
}

type Comparison struct {
	Status string
	Height uint64
	Hashes []common.Hash
}
