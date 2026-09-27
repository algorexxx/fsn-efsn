package observe

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"sort"
	"strings"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/types"
)

type HistoryStatus struct {
	Version       int
	Scope         HistoryScope
	Sequence      uint64
	LastEventUTC  time.Time
	LastReportUTC time.Time
	LogicalBytes  int64
	MaxBytes      int64
	Coverage      string
	Incidents     []Incident
	Limitations   []string
	Blocks        []BlockCoverage `json:",omitempty"`
}

type Incident struct {
	ID                 string
	Node               string
	Transaction        common.Hash
	Kind               string
	Status             string
	Observation        string
	Details            []string
	FirstSequence      uint64
	LastSequence       uint64
	FirstUTC           time.Time
	LastSeenUTC        time.Time
	Occurrences        uint64
	LastReview         *Review
	LastReviewSequence uint64
}

type receiptLocation struct {
	Block common.Hash
	Index uint
}

type incidentCondition struct {
	Node        string
	Transaction common.Hash
	Kind        string
	Observation string
	Details     []string
}

type incidentHistory struct {
	HistoryStatus
	incidents map[string]*Incident
	receipts  map[string]receiptLocation
	paths     map[string][]common.Hash
	coverage  map[string]BlockCoverage
}

func newIncidentHistory(meta historyMetadata) *incidentHistory {
	return &incidentHistory{HistoryStatus: HistoryStatus{Version: 1, Scope: meta.Scope, MaxBytes: meta.MaxBytes, Coverage: "snapshots_only_no_block_backfill", Limitations: []string{
		"observed conditions, not timed alerts or a health verdict; saved intent remains unknown",
		"operator acknowledgement is not resolution; resolution is a recorded review, not automatic verification of recovery",
		"missing data or untracked transactions leave prior incidents unknown rather than clearing them",
		"reports are retained snapshots; blocks between observations and complete mining/selection history are not backfilled",
	}}, incidents: make(map[string]*Incident), receipts: make(map[string]receiptLocation), paths: make(map[string][]common.Hash), coverage: make(map[string]BlockCoverage)}
}

func (state *incidentHistory) apply(event historyEvent) error {
	kinds := 0
	for _, present := range []bool{event.Report != nil, event.Review != nil, event.Backfill != nil} {
		if present {
			kinds++
		}
	}
	if event.Sequence != state.Sequence+1 || event.TimeUTC.IsZero() || event.TimeUTC.Before(state.LastEventUTC) || kinds != 1 {
		return fmt.Errorf("invalid history event sequence, time or kind")
	}
	if event.Report != nil {
		if err := validateHistoryReport(state.Scope, event.Report); err != nil {
			return err
		}
		if !event.TimeUTC.Equal(event.Report.FinishedUTC) || event.Report.StartedUTC.Before(state.LastEventUTC) {
			return fmt.Errorf("observation precedes previous event; inspect clock/order")
		}
		state.observe(event.Report, event.Sequence)
		state.invalidateBlockCoverage(event.Report)
		state.LastReportUTC = event.Report.FinishedUTC
	} else if event.Backfill != nil {
		if !event.TimeUTC.Equal(event.Backfill.FinishedUTC) || event.Backfill.StartedUTC.Before(state.LastEventUTC) {
			return fmt.Errorf("backfill precedes previous event; inspect clock/order")
		}
		if err := state.applyBackfill(event.Backfill, event.Sequence); err != nil {
			return err
		}
	} else {
		review := event.Review
		incident := state.incidents[review.Incident]
		if incident == nil || len(review.Reason) > 2048 || strings.TrimSpace(review.Reason) == "" || (review.Action != "acknowledge" && review.Action != "resolve") {
			return fmt.Errorf("existing incident, acknowledge/resolve action and explicit reason up to 2048 bytes required")
		}
		if incident.Status == "resolved" || review.Action == "acknowledge" && incident.Status == "acknowledged" {
			return fmt.Errorf("incident is already reviewed in that state")
		}
		incident.Status = "acknowledged"
		if review.Action == "resolve" {
			incident.Status = "resolved"
		}
		copy := *review
		incident.LastReview = &copy
		incident.LastReviewSequence = event.Sequence
	}
	state.Sequence, state.LastEventUTC = event.Sequence, event.TimeUTC
	return nil
}

func validateHistoryReport(scope HistoryScope, report *Report) error {
	if report.Version != 1 || report.StartedUTC.IsZero() || report.FinishedUTC.Before(report.StartedUTC) || len(report.Nodes) != len(scope.Wallets) {
		return fmt.Errorf("invalid observation version, times or named nodes")
	}
	seen := make(map[string]bool)
	for _, node := range report.Nodes {
		wallet, ok := scope.Wallets[node.Name]
		if !ok || seen[node.Name] || node.Wallet != wallet || node.StartedUTC.Before(report.StartedUTC) || node.FinishedUTC.Before(node.StartedUTC) || node.FinishedUTC.After(report.FinishedUTC) {
			return fmt.Errorf("observation node identity or time differs from scope")
		}
		seen[node.Name] = true
		if node.Consistency == "stable" && node.Head == nil {
			return fmt.Errorf("stable observation has no head")
		}
		if node.Role != "producer" && node.Role != "verifier" && node.Role != "maintenance" && node.Role != "retired" {
			return fmt.Errorf("invalid observed role")
		}
		if node.Head != nil && (node.Head.Header == nil || node.Head.Header.Number == nil || !node.Head.Header.Number.IsUint64() || node.Head.Header.Hash() != node.Head.Hash) {
			return fmt.Errorf("invalid observed head")
		}
		if node.Identity == "matches" && (node.ChainID == nil || node.NetworkID == nil || node.Genesis == nil || node.Anchor == nil || node.ChainID.ToInt().String() != scope.ChainID || *node.NetworkID != scope.NetworkID || node.Genesis.Hash != scope.Genesis || node.Anchor.Hash != scope.AnchorHash) {
			return fmt.Errorf("matching observation does not match history identity")
		}
		hashes := make(map[common.Hash]bool)
		for _, tracked := range node.Tracked {
			var tx types.Transaction
			if hashes[tracked.Hash] || tx.UnmarshalBinary(tracked.Raw) != nil || tx.Hash() != tracked.Hash || tx.Nonce() != tracked.Nonce || tracked.Owner != wallet || tx.ChainId().String() != scope.ChainID {
				return fmt.Errorf("invalid tracked bytes or identity in observation")
			}
			owner, err := types.Sender(types.LatestSignerForChainID(tx.ChainId()), &tx)
			if err != nil || owner != wallet {
				return fmt.Errorf("tracked signature differs from monitored wallet")
			}
			hashes[tracked.Hash] = true
		}
	}
	return nil
}

func (state *incidentHistory) observe(report *Report, sequence uint64) {
	for _, incident := range state.incidents {
		incident.Observation = "unknown"
	}
	comparison := incidentCondition{Kind: "branch_divergence", Observation: "unknown"}
	if report.Comparison.Status == "same_at_common_height" {
		comparison.Observation = "not_observed"
	}
	if report.Comparison.Status == "divergent_at_common_height" {
		comparison.Observation = "present"
		comparison.Details = []string{fmt.Sprintf("different canonical hashes at height %d", report.Comparison.Height)}
	}
	state.update(comparison, sequence)
	for _, node := range report.Nodes {
		condition := incidentCondition{Node: node.Name, Kind: "node_observation", Observation: "unknown"}
		trusted := node.Identity == "matches" && node.Consistency == "stable"
		if node.Role != "retired" {
			if trusted {
				condition.Observation = "not_observed"
			}
			if len(node.Issues) > 0 {
				condition.Observation = "present"
				for _, issue := range node.Issues {
					condition.Details = append(condition.Details, issue.Field+":"+issue.Code)
				}
			}
		}
		state.update(condition, sequence)
		for _, tx := range node.Tracked {
			if tx.Purchase {
				state.update(purchaseCondition(node.Name, tx, trusted), sequence)
			}
			state.observeReceipt(node.Name, tx, trusted, sequence)
		}
	}
	state.dateIncidents(sequence, report.FinishedUTC)
}

func (state *incidentHistory) dateIncidents(sequence uint64, when time.Time) {
	for _, incident := range state.incidents {
		if incident.FirstSequence == sequence {
			incident.FirstUTC = when
		}
		if incident.LastSequence == sequence {
			incident.LastSeenUTC = when
		}
	}
}

func purchaseCondition(node string, tx TransactionObservation, trusted bool) incidentCondition {
	condition := incidentCondition{Node: node, Transaction: tx.Hash, Kind: "purchase_attention", Observation: "unknown"}
	if !trusted {
		return condition
	}
	if tx.Inclusion == "canonical_native_success" {
		condition.Observation = "not_observed"
		return condition
	}
	for _, check := range []struct {
		present bool
		detail  string
	}{
		{tx.NonceRelation == "ahead", "tracked_transaction_nonce_gap"},
		{tx.Pool == "conflicting_nonce", "conflicting_pool_nonce"},
		{tx.Payload == "invalid" || tx.Payload == "below_base_fee", "payload_not_currently_usable"},
		{tx.Funding == "insufficient_estimate" && (tx.NonceRelation == "current" || tx.NonceRelation == "ahead"), "insufficient_free_backing_estimate"},
		{tx.NonceRelation == "consumed" && tx.Inclusion != "unknown", "nonce_consumed_without_confirmed_purchase"},
		{tx.Inclusion == "native_failed" || tx.Inclusion == "canonical_failed", "purchase_failed"},
		{tx.Inclusion == "native_success_unverified", "native_outcome_unverified"},
	} {
		if check.present {
			condition.Details = append(condition.Details, check.detail)
		}
	}
	if len(condition.Details) > 0 {
		condition.Observation = "present"
	} else if tx.Inclusion != "unknown" && tx.NonceRelation != "unknown" && tx.Pool != "unknown" && tx.Payload != "unknown" && tx.Funding != "unknown" {
		condition.Observation = "not_observed"
	}
	return condition
}

func (state *incidentHistory) observeReceipt(node string, tx TransactionObservation, trusted bool, sequence uint64) {
	condition := incidentCondition{Node: node, Transaction: tx.Hash, Kind: "receipt_change", Observation: "unknown"}
	id := conditionID(condition)
	previous, known := state.receipts[id]
	if trusted {
		if (tx.Inclusion == "canonical_native_success" || tx.Inclusion == "canonical_ordinary_success") && tx.Receipt != nil {
			current := receiptLocation{Block: tx.Receipt.BlockHash, Index: tx.Receipt.TransactionIndex}
			condition.Observation = "not_observed"
			if known && previous != current {
				condition.Observation, condition.Details = "present", []string{"canonical_receipt_location_changed"}
			}
			state.receipts[id] = current
		} else if known && (tx.Inclusion == "absent" || tx.Inclusion == "noncanonical" || tx.Inclusion == "native_failed" || tx.Inclusion == "canonical_failed") {
			condition.Observation, condition.Details = "present", []string{"previous_canonical_success_not_confirmed"}
		}
	}
	state.update(condition, sequence)
}

func (state *incidentHistory) update(condition incidentCondition, sequence uint64) {
	id := conditionID(condition)
	incident := state.incidents[id]
	if incident == nil {
		if condition.Observation != "present" {
			return
		}
		incident = &Incident{ID: id, Node: condition.Node, Transaction: condition.Transaction, Kind: condition.Kind, Status: "open", FirstSequence: sequence, Occurrences: 1}
		state.incidents[id] = incident
	}
	incident.Observation = condition.Observation
	if condition.Observation == "present" {
		if incident.Status == "resolved" {
			incident.Status = "open"
			incident.Occurrences++
		}
		incident.LastSequence, incident.Details = sequence, condition.Details
	}
}

func conditionID(condition incidentCondition) string {
	raw := fmt.Sprintf("%d:%s|%s|%s", len(condition.Node), condition.Node, condition.Kind, condition.Transaction.Hex())
	hash := sha256.Sum256([]byte(raw))
	return hex.EncodeToString(hash[:])
}

func (state *incidentHistory) status() HistoryStatus {
	result := state.HistoryStatus
	result.Scope.Wallets = make(map[string]common.Address, len(state.Scope.Wallets))
	for name, wallet := range state.Scope.Wallets {
		result.Scope.Wallets[name] = wallet
	}
	result.Incidents = make([]Incident, 0, len(state.incidents))
	for _, incident := range state.incidents {
		result.Incidents = append(result.Incidents, *incident)
	}
	sort.Slice(result.Incidents, func(i, j int) bool { return result.Incidents[i].ID < result.Incidents[j].ID })
	for _, coverage := range state.coverage {
		if coverage.ObservedHead != nil {
			head := *coverage.ObservedHead
			coverage.ObservedHead = &head
		}
		result.Blocks = append(result.Blocks, coverage)
	}
	sort.Slice(result.Blocks, func(i, j int) bool { return result.Blocks[i].Node < result.Blocks[j].Node })
	return result
}
