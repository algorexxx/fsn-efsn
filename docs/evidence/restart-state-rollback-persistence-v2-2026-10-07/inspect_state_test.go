package state

import (
	"encoding/hex"

	"github.com/FusionFoundation/efsn/v5/common"
)

type F11AccountObservation struct {
	Exists      bool
	BalanceIDs  []common.Hash
	Balances    []string
	TimeLockIDs []common.Hash
	TimeLocks   []*common.TimeLock
	Nonce       uint64
	Code        string
	Storage     common.Hash
}

type F11DirtyObservation struct {
	Journal bool
	Pending bool
	Dirty   bool
}

func F11InspectAccount(s *StateDB, address common.Address) F11AccountObservation {
	obj := s.getStateObject(address)
	if obj == nil {
		return F11AccountObservation{}
	}
	data := obj.data
	result := F11AccountObservation{Exists: true, BalanceIDs: data.BalancesHash, TimeLockIDs: data.TimeLockBalancesHash, TimeLocks: data.TimeLockBalancesVal, Nonce: data.Nonce, Code: hex.EncodeToString(s.GetCode(address)), Storage: s.GetState(address, common.Hash{8})}
	for _, balance := range data.BalancesVal {
		value := "<nil>"
		if balance != nil {
			value = balance.String()
		}
		result.Balances = append(result.Balances, value)
	}
	return result
}

func F11InspectDirty(s *StateDB, address common.Address) F11DirtyObservation {
	_, journal := s.journal.dirties[address]
	_, pending := s.stateObjectsPending[address]
	_, dirty := s.stateObjectsDirty[address]
	return F11DirtyObservation{Journal: journal, Pending: pending, Dirty: dirty}
}
