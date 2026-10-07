package state

import "github.com/FusionFoundation/efsn/v5/common"

const f11RawCandidate = false

func f11Delete(s *StateDB, address common.Address, fix bool) bool {
	return s.Suicide(address)
}
