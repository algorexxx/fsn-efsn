package observe

import (
	"context"
	"encoding/json"
	"fmt"
	"math/big"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
)

type AnchorInventory struct {
	Node        string
	Wallet      common.Address
	StartedUTC  time.Time
	FinishedUTC time.Time
	ChainID     *hexutil.Big
	NetworkID   *string
	Genesis     *Block
	Anchor      *Block
	AnchorAfter *Block
	Tickets     map[common.Hash]common.TicketDisplay
	Status      string
}

func (history *History) CollectAnchorInventory(ctx context.Context, config Config, nodeName string, timeout time.Duration, now func() time.Time) (AnchorInventory, error) {
	history.mu.Lock()
	defer history.mu.Unlock()
	if err := history.CheckConfig(config); err != nil {
		return AnchorInventory{}, err
	}
	var selected *NodeConfig
	for i := range config.Nodes {
		if config.Nodes[i].Name == nodeName {
			selected = &config.Nodes[i]
		}
	}
	if selected == nil || timeout <= 0 {
		return AnchorInventory{}, fmt.Errorf("anchor inventory requires a configured node and positive timeout")
	}
	state, err := history.load()
	if err != nil {
		return AnchorInventory{}, err
	}
	readContext, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()
	report := collectAnchorInventory(readContext, config, *selected, now)
	_, err = history.append(state, historyEvent{Sequence: state.Sequence + 1, TimeUTC: report.FinishedUTC, AnchorInventory: &report})
	return report, err
}

func collectAnchorInventory(ctx context.Context, config Config, node NodeConfig, now func() time.Time) (report AnchorInventory) {
	report = AnchorInventory{Node: node.Name, Wallet: node.Wallet, StartedUTC: now().UTC(), Status: "unavailable"}
	defer func() {
		report.FinishedUTC = now().UTC()
		if report.Status == "ready" {
			encoded, err := json.Marshal(report)
			if err != nil || len(encoded) > maxBackfillBytes {
				report.Tickets, report.Status = nil, "data_limit"
			}
		}
	}()
	if node.Role == "retired" {
		report.Status = "retired"
		return
	}
	client, err := dial(ctx, node.Endpoint)
	if err != nil {
		return
	}
	defer client.Close()
	reader := readClient{client: client}
	if reader.call(ctx, &report.ChainID, "eth_chainId") != nil || reader.call(ctx, &report.NetworkID, "net_version") != nil {
		return
	}
	report.Genesis, err = reader.block(ctx, "0x0")
	if err != nil {
		return
	}
	number := hexutil.EncodeUint64(config.AnchorNumber)
	report.Anchor, err = reader.block(ctx, number)
	if err != nil {
		return
	}
	if !historyIdentityMatches(scopeFor(config), report.ChainID, report.NetworkID, report.Genesis, report.Anchor) {
		report.Status = "identity_mismatch"
		return
	}
	var tickets map[common.Hash]common.TicketDisplay
	if reader.call(ctx, &tickets, "fsn_allTicketsByAddress", node.Wallet, number) != nil {
		return
	}
	report.AnchorAfter, err = reader.block(ctx, number)
	if err != nil || report.AnchorAfter.Hash != report.Anchor.Hash {
		report.Status = "unstable"
		return
	}
	if tickets == nil {
		tickets = make(map[common.Hash]common.TicketDisplay)
	}
	if !validTicketInventory(tickets, node.Wallet, config.AnchorNumber) {
		report.Status = "invalid_inventory"
		return
	}
	report.Tickets, report.Status = tickets, "ready"
	return
}

func validateAnchorInventory(scope HistoryScope, report *AnchorInventory) error {
	wallet, exists := scope.Wallets[report.Node]
	if !exists || report.Wallet != wallet || report.StartedUTC.IsZero() || report.FinishedUTC.Before(report.StartedUTC) {
		return fmt.Errorf("invalid anchor inventory scope or time")
	}
	if report.Status == "ready" {
		if !historyIdentityMatches(scope, report.ChainID, report.NetworkID, report.Genesis, report.Anchor) || !validBackfillHeader(report.AnchorAfter) || report.AnchorAfter.Hash != report.Anchor.Hash || !validTicketInventory(report.Tickets, wallet, scope.AnchorNumber) {
			return fmt.Errorf("invalid ready anchor inventory")
		}
		encoded, err := json.Marshal(report)
		if err != nil || len(encoded) > maxBackfillBytes {
			return fmt.Errorf("ready anchor inventory exceeds byte limit")
		}
		return nil
	}
	if report.Tickets != nil {
		return fmt.Errorf("unverified anchor inventory contains tickets")
	}
	switch report.Status {
	case "unavailable", "retired", "identity_mismatch", "unstable", "invalid_inventory", "data_limit":
		return nil
	default:
		return fmt.Errorf("unsupported anchor inventory status")
	}
}

func validTicketInventory(tickets map[common.Hash]common.TicketDisplay, wallet common.Address, height uint64) bool {
	if tickets == nil {
		return false
	}
	for id, ticket := range tickets {
		if id == (common.Hash{}) || ticket.Owner != wallet || ticket.Height > height || ticket.StartTime >= ticket.ExpireTime || ticket.Value == nil || ticket.Value.Cmp(common.TicketPrice(new(big.Int).SetUint64(ticket.Height))) != 0 {
			return false
		}
	}
	return true
}
