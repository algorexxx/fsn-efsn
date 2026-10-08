package main

import (
	"bytes"
	"compress/gzip"
	"encoding/json"
	"fmt"
	"io"
	"os"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/state"
	"github.com/FusionFoundation/efsn/v5/core/types"
)

type ticketObservation struct {
	Header     *types.Header
	Compressed []byte
	Payload    []byte
}

func main() {
	if err := runTicketProbe(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func runTicketProbe() error {
	db := rawdb.NewMemoryDatabase()
	defer db.Close()
	block := core.DefaultGenesisBlock().ToBlock(db)
	s, err := state.New(block.Root(), block.MixDigest(), state.NewDatabase(db))
	if err != nil {
		return err
	}
	compressed := s.GetCode(common.TicketKeyAddress)
	payload, err := unzipTickets(compressed)
	if err != nil {
		return err
	}
	header := block.Header()
	if len(os.Args) == 2 {
		replacement, err := os.ReadFile(os.Args[1])
		if err != nil {
			return err
		}
		decoded, err := unzipTickets(replacement)
		if err != nil {
			return err
		}
		if !bytes.Equal(payload, decoded) {
			return fmt.Errorf("replacement must encode the identical ticket RLP")
		}
		header.MixDigest = s.SetData(common.TicketKeyAddress, replacement)
		header.Root = s.IntermediateRoot(false)
		compressed = replacement
	}
	return json.NewEncoder(os.Stdout).Encode(ticketObservation{Header: header, Compressed: compressed, Payload: payload})
}

func unzipTickets(data []byte) ([]byte, error) {
	reader, err := gzip.NewReader(bytes.NewReader(data))
	if err != nil {
		return nil, err
	}
	defer reader.Close()
	return io.ReadAll(reader)
}
