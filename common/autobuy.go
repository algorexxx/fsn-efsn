package common

import "sync/atomic"

var autoBuyTicketEnabled uint32

func IsAutoBuyTicketEnabled() bool {
	return atomic.LoadUint32(&autoBuyTicketEnabled) != 0
}

func SetAutoBuyTicketEnabled(enabled bool) {
	var value uint32
	if enabled {
		value = 1
	}
	atomic.StoreUint32(&autoBuyTicketEnabled, value)
	NotifyAutoBuyTicket()
}

func NotifyAutoBuyTicket() {
	select {
	case AutoBuyTicketChan <- 1:
	default:
	}
}
