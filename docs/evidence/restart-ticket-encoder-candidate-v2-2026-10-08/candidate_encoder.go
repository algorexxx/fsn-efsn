package main

import "github.com/FusionFoundation/efsn/v5/internal/ticketgzip"

func encode(payload []byte) ([]byte, error) {
	return ticketgzip.Encode(payload)
}
