package main

import (
	"encoding/hex"
	"encoding/json"
	"os"

	"github.com/FusionFoundation/efsn/v5/crypto"
)

type vector struct {
	Original string `json:"original"`
	Fusion   string `json:"fusion"`
}

func main() {
	input, err := os.ReadFile(os.Args[1])
	if err != nil {
		panic(err)
	}
	var originals []string
	if err := json.Unmarshal(input, &originals); err != nil {
		panic(err)
	}
	key, err := crypto.HexToECDSA("b71c71a67e1177ad4e901695e1b4b9ee17ae16c6668d313eac2f96dbcda3f291")
	if err != nil {
		panic(err)
	}
	var converted []vector
	for _, original := range originals {
		packet, err := hex.DecodeString(original)
		if err != nil || len(packet) < 99 || packet[97] < 1 || packet[97] > 4 {
			panic("invalid original vector")
		}
		packet[97] += 39
		signature, err := crypto.Sign(crypto.Keccak256(packet[97:]), key)
		if err != nil {
			panic(err)
		}
		copy(packet[32:97], signature)
		copy(packet[:32], crypto.Keccak256(packet[32:]))
		converted = append(converted, vector{Original: original, Fusion: hex.EncodeToString(packet)})
	}
	output, err := json.MarshalIndent(converted, "", "  ")
	if err != nil {
		panic(err)
	}
	if err := os.WriteFile(os.Args[2], append(output, '\n'), 0644); err != nil {
		panic(err)
	}
}
