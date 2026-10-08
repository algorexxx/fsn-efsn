package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/state"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/rlp"
	"math/big"
	"os"
	"path/filepath"
)

type historicalVector struct {
	Height    uint64
	Available bool
	Header    *types.Header
}

type expiryVector struct {
	Name          string
	Timestamp     uint64
	Input         []byte
	Expected      []byte
	ExpectedError string
}

type stateObservation struct {
	Name                string
	CacheInitiallyEmpty bool
	Before              []byte
	After               []byte
	Hash                common.Hash
	Root                common.Hash
	Error               string
	CacheError          string
}

type historyObservation struct {
	Genesis *types.Header
	Vectors []stateObservation
}

func main() {
	if err := runProbe(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func runProbe() error {
	if len(os.Args) != 4 {
		return fmt.Errorf("usage: probe payloads|tickets|expiry INPUT OUTPUT")
	}
	if err := os.Mkdir(os.Args[3], 0755); err != nil {
		return err
	}
	switch os.Args[1] {
	case "payloads":
		return checkPayloads(os.Args[2], os.Args[3])
	case "tickets":
		return observeTickets(os.Args[2], os.Args[3])
	case "expiry":
		return observeExpiry(os.Args[2], os.Args[3])
	}
	return fmt.Errorf("unknown mode")
}

func readJSON(path string, result interface{}) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	return json.Unmarshal(data, result)
}

func checkPayloads(input, output string) error {
	var names []string
	if err := readJSON(filepath.Join(input, "index.json"), &names); err != nil {
		return err
	}
	for _, name := range names {
		payload, err := os.ReadFile(filepath.Join(input, name+".bin"))
		if err != nil {
			return err
		}
		encoded, err := encode(payload)
		if err != nil {
			return err
		}
		again, err := encode(payload)
		if err != nil {
			return err
		}
		if !bytes.Equal(encoded, again) {
			return fmt.Errorf("non-deterministic encoding: %s", name)
		}
		completed := make(chan error, 4)
		for i := 0; i < 4; i++ {
			go func() {
				data, err := encode(payload)
				if err == nil && !bytes.Equal(encoded, data) {
					err = fmt.Errorf("concurrent encoding differs: %s", name)
				}
				completed <- err
			}()
		}
		for i := 0; i < 4; i++ {
			if err := <-completed; err != nil {
				return err
			}
		}
		if err := os.WriteFile(filepath.Join(output, name+".gz"), encoded, 0644); err != nil {
			return err
		}
	}
	return json.NewEncoder(os.Stdout).Encode(names)
}

func observeTickets(input, output string) error {
	var vectors []historicalVector
	if err := readJSON(filepath.Join(input, "index.json"), &vectors); err != nil {
		return err
	}
	var result historyObservation
	for _, v := range vectors {
		if !v.Available {
			continue
		}
		name := fmt.Sprint(v.Height)
		blob, err := os.ReadFile(filepath.Join(input, name+".gz"))
		if err != nil {
			return err
		}
		if crypto.Keccak256Hash(blob) != v.Header.MixDigest {
			return fmt.Errorf("historical commitment mismatch")
		}
		if state.GetCachedTickets(v.Header.MixDigest) != nil {
			return fmt.Errorf("expected cold ticket cache at %s", name)
		}
		db := rawdb.NewMemoryDatabase()
		s, err := state.New(common.Hash{}, v.Header.MixDigest, state.NewDatabase(db))
		if err != nil {
			db.Close()
			return err
		}
		s.SetData(common.TicketKeyAddress, blob)
		tickets, err := s.AllTickets()
		if err != nil {
			db.Close()
			return err
		}
		before, err := rlp.EncodeToBytes(&tickets)
		if err != nil {
			db.Close()
			return err
		}
		o, err := updateTickets(s, name, v.Height, 0, output)
		if err != nil {
			db.Close()
			return err
		}
		o.Before, o.CacheInitiallyEmpty = before, true
		if err := state.AddCachedTickets(v.Header.MixDigest, tickets); err != nil {
			o.CacheError = err.Error()
		}
		result.Vectors = append(result.Vectors, o)
		db.Close()
	}
	db := rawdb.NewMemoryDatabase()
	defer db.Close()
	result.Genesis = core.DefaultGenesisBlock().ToBlock(db).Header()
	return json.NewEncoder(os.Stdout).Encode(result)
}

func updateTickets(s *state.StateDB, name string, height, timestamp uint64, output string) (stateObservation, error) {
	o := stateObservation{Name: name}
	hash, err := s.UpdateTickets(new(big.Int).SetUint64(height), timestamp)
	o.Hash = hash
	if err != nil {
		o.Error = err.Error()
	}
	tickets, err := s.AllTickets()
	if err != nil {
		return o, err
	}
	o.After, err = rlp.EncodeToBytes(&tickets)
	if err != nil {
		return o, err
	}
	if err := os.WriteFile(filepath.Join(output, name+".gz"), s.GetData(common.TicketKeyAddress), 0644); err != nil {
		return o, err
	}
	o.Root = s.IntermediateRoot(false)
	return o, nil
}

func observeExpiry(input, output string) error {
	var vectors []expiryVector
	if err := readJSON(input, &vectors); err != nil {
		return err
	}
	var result []stateObservation
	for _, v := range vectors {
		var tickets common.TicketsDataSlice
		if err := rlp.DecodeBytes(v.Input, &tickets); err != nil {
			return err
		}
		db := rawdb.NewMemoryDatabase()
		s, err := state.New(common.Hash{}, common.Hash{}, state.NewDatabase(db))
		if err != nil {
			db.Close()
			return err
		}
		for _, owner := range tickets {
			for _, body := range owner.Tickets {
				if err := s.AddTicket(common.Ticket{Owner: owner.Owner, TicketBody: body}); err != nil {
					db.Close()
					return err
				}
			}
		}
		o, err := updateTickets(s, v.Name, 2, v.Timestamp, output)
		if err != nil {
			db.Close()
			return err
		}
		o.Before = v.Input
		if !bytes.Equal(o.After, v.Expected) || o.Error != v.ExpectedError {
			db.Close()
			return fmt.Errorf("independent expiry expectation failed: %s", v.Name)
		}
		if o.Error == "" {
			after, err := s.AllTickets()
			if err != nil {
				db.Close()
				return err
			}
			if err := state.AddCachedTickets(o.Hash, after); err != nil {
				db.Close()
				return err
			}
		}
		result = append(result, o)
		db.Close()
	}
	return json.NewEncoder(os.Stdout).Encode(result)
}
