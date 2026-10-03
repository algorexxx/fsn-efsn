package observe

import (
	"encoding/json"
	"fmt"

	"github.com/FusionFoundation/efsn/v5/common"
)

func (state *incidentHistory) blockPath(node string) []common.Hash {
	if path := state.paths[node]; len(path) > 0 {
		return path
	}
	return []common.Hash{state.Scope.AnchorHash}
}

func (state *incidentHistory) applyBackfill(report *BackfillReport, sequence uint64) error {
	if _, ok := state.Scope.Wallets[report.Node]; !ok || report.StartedUTC.IsZero() || report.FinishedUTC.Before(report.StartedUTC) || report.MaxBlocks == 0 || report.MaxBlocks > maxBackfillBlocks || uint64(len(report.Blocks)) > report.MaxBlocks {
		return fmt.Errorf("invalid backfill scope, time or bounds")
	}
	path := state.blockPath(report.Node)
	oldTip := BlockReference{Number: state.Scope.AnchorNumber + uint64(len(path)) - 1, Hash: path[len(path)-1]}
	coverage := BlockCoverage{Node: report.Node, StoredThrough: oldTip, CheckedUTC: report.FinishedUTC, Status: report.Status}
	if report.Head != nil {
		if !validBackfillHeader(report.Head) {
			return fmt.Errorf("invalid backfill head")
		}
		coverage.ObservedHead = &BlockReference{Number: report.Head.Header.Number.Uint64(), Hash: report.Head.Hash}
	}
	change := incidentCondition{Node: report.Node, Kind: "canonical_history_change", Observation: "unknown"}
	gap := incidentCondition{Node: report.Node, Kind: "block_coverage", Observation: "present", Details: []string{report.Status}}
	if report.Base == nil {
		if len(report.Blocks) != 0 || (report.Status != "unavailable" && report.Status != "identity_mismatch" && report.Status != "unstable" && report.Status != "retired") {
			return fmt.Errorf("unverified backfill contains accepted blocks or status")
		}
		if report.Status == "retired" {
			gap.Observation = "unknown"
		}
	} else {
		if !historyIdentityMatches(state.Scope, report.ChainID, report.NetworkID, report.Genesis, report.Anchor) || coverage.ObservedHead == nil || report.Base.Number < state.Scope.AnchorNumber || report.Base.Number > oldTip.Number || report.Base.Number > coverage.ObservedHead.Number || path[report.Base.Number-state.Scope.AnchorNumber] != report.Base.Hash {
			return fmt.Errorf("backfill does not join retained anchor ancestry")
		}
		if report.Status != "complete_at_observation" && report.Status != "batch_limit" && report.Status != "data_limit" && report.Status != "block_unavailable_or_invalid" {
			return fmt.Errorf("unsupported accepted backfill status")
		}
		previous, bytesUsed := *report.Base, 0
		newHashes := make([]common.Hash, 0, len(report.Blocks))
		for _, evidence := range report.Blocks {
			block, err := validateBlockEvidence(evidence)
			if err != nil {
				return err
			}
			if previous.Number >= coverage.ObservedHead.Number || block.NumberU64() != previous.Number+1 || block.ParentHash() != previous.Hash {
				return fmt.Errorf("backfill block continuity mismatch")
			}
			encoded, err := json.Marshal(evidence)
			if err != nil {
				return err
			}
			bytesUsed += len(encoded)
			if bytesUsed > maxBackfillBytes {
				return fmt.Errorf("backfill evidence exceeds byte limit")
			}
			previous = BlockReference{Number: block.NumberU64(), Hash: block.Hash()}
			newHashes = append(newHashes, block.Hash())
		}
		complete := previous == *coverage.ObservedHead
		if complete != (report.Status == "complete_at_observation") || previous.Number == coverage.ObservedHead.Number && !complete || report.Status == "batch_limit" && uint64(len(report.Blocks)) != report.MaxBlocks {
			return fmt.Errorf("backfill coverage status differs from retained range")
		}
		if len(newHashes) > 0 && report.Base.Number < oldTip.Number && newHashes[0] == path[report.Base.Number-state.Scope.AnchorNumber+1] {
			return fmt.Errorf("backfill replaced an unchanged retained prefix")
		}
		change.Observation = "not_observed"
		if report.Base.Number < oldTip.Number {
			change.Observation = "present"
			change.Details = []string{fmt.Sprintf("previous tip %d:%s displaced after %d:%s", oldTip.Number, oldTip.Hash.Hex(), report.Base.Number, report.Base.Hash.Hex())}
		}
		path = append(path[:report.Base.Number-state.Scope.AnchorNumber+1], newHashes...)
		state.paths[report.Node] = path
		coverage.StoredThrough = previous
		if complete {
			gap.Observation, gap.Details = "not_observed", nil
		}
	}
	if len(state.coverage) == 0 {
		for node := range state.Scope.Wallets {
			state.coverage[node] = BlockCoverage{Node: node, StoredThrough: BlockReference{Number: state.Scope.AnchorNumber, Hash: state.Scope.AnchorHash}, Status: "not_requested"}
		}
	}
	state.Coverage = "bounded_block_history_see_nodes"
	state.Limitations[len(state.Limitations)-1] = "block coverage is per node since the anchor at recorded times; no state execution, finality or automatic native outcome/selection accounting"
	state.coverage[report.Node] = coverage
	state.update(gap, sequence)
	state.update(change, sequence)
	state.dateIncidents(sequence, report.FinishedUTC)
	return nil
}

func (state *incidentHistory) invalidateBlockCoverage(report *Report) {
	for _, node := range report.Nodes {
		coverage, exists := state.coverage[node.Name]
		if !exists {
			continue
		}
		coverage.Status = "not_rechecked"
		state.coverage[node.Name] = coverage
	}
}
