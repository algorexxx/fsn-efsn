package observe

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"reflect"
	"sync"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/syndtr/goleveldb/leveldb"
	"github.com/syndtr/goleveldb/leveldb/opt"
)

const historyFormat = "fsn-observer-history-v1\n"
const maxHistoryEvent = 16 * 1024 * 1024

type HistoryScope struct {
	ChainID      string
	NetworkID    string
	Genesis      common.Hash
	AnchorNumber uint64
	AnchorHash   common.Hash
	Wallets      map[string]common.Address
}

type historyMetadata struct {
	Version  int
	Scope    HistoryScope
	MaxBytes int64
}

type historyEvent struct {
	Sequence uint64
	TimeUTC  time.Time
	Report   *Report `json:",omitempty"`
	Review   *Review `json:",omitempty"`
}

type Review struct {
	Action   string
	Incident string
	Reason   string
}

type History struct {
	mu   sync.Mutex
	db   *leveldb.DB
	meta historyMetadata
}

func CreateHistory(path string, config Config, maxBytes int64) (*History, error) {
	if err := ValidateConfig(config); err != nil {
		return nil, err
	}
	if !filepath.IsAbs(path) || maxBytes < 1024 || maxBytes > 1024*1024*1024 {
		return nil, fmt.Errorf("absolute new history directory and explicit byte budget from 1024 through 1073741824 required")
	}
	meta := historyMetadata{Version: 1, Scope: scopeFor(config), MaxBytes: maxBytes}
	encoded, err := json.Marshal(meta)
	if err != nil {
		return nil, err
	}
	if int64(len(encoded)+len("metadata")) > maxBytes {
		return nil, fmt.Errorf("history metadata exceeds its byte budget")
	}
	if err := os.Mkdir(path, 0700); err != nil {
		return nil, fmt.Errorf("history initialization requires a new directory: %w", err)
	}
	marker, err := os.OpenFile(filepath.Join(path, "FORMAT"), os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if err != nil {
		return nil, err
	}
	_, err = marker.WriteString(historyFormat)
	if err == nil {
		err = marker.Sync()
	}
	closeErr := marker.Close()
	if err != nil {
		return nil, err
	}
	if closeErr != nil {
		return nil, closeErr
	}
	db, err := leveldb.OpenFile(filepath.Join(path, "records"), &opt.Options{ErrorIfExist: true, Strict: opt.StrictAll})
	if err != nil {
		return nil, err
	}
	if err := db.Put([]byte("metadata"), encoded, &opt.WriteOptions{Sync: true}); err != nil {
		db.Close()
		return nil, err
	}
	return &History{db: db, meta: meta}, nil
}

func OpenHistory(path string) (*History, error) {
	if !filepath.IsAbs(path) {
		return nil, fmt.Errorf("absolute observer history directory required")
	}
	file, err := os.Open(filepath.Join(path, "FORMAT"))
	if err != nil {
		return nil, fmt.Errorf("not an initialized observer history")
	}
	marker, readErr := io.ReadAll(io.LimitReader(file, int64(len(historyFormat)+1)))
	file.Close()
	if readErr != nil || string(marker) != historyFormat {
		return nil, fmt.Errorf("unsupported observer history format")
	}
	db, err := leveldb.OpenFile(filepath.Join(path, "records"), &opt.Options{ErrorIfMissing: true, Strict: opt.StrictAll})
	if err != nil {
		return nil, fmt.Errorf("cannot open observer history exclusively: %w", err)
	}
	history := &History{db: db}
	raw, err := db.Get([]byte("metadata"), nil)
	if err == nil {
		err = decodeHistory(raw, &history.meta)
	}
	if err == nil && (history.meta.Version != 1 || history.meta.MaxBytes < 1024 || history.meta.MaxBytes > 1024*1024*1024) {
		err = fmt.Errorf("invalid history metadata")
	}
	if err == nil {
		err = validateHistoryScope(history.meta.Scope)
	}
	if err == nil {
		_, err = history.load()
	}
	if err != nil {
		db.Close()
		return nil, fmt.Errorf("history is incomplete or corrupt; no reset performed: %w", err)
	}
	return history, nil
}

func (history *History) Close() error {
	history.mu.Lock()
	defer history.mu.Unlock()
	return history.db.Close()
}

func (history *History) CheckConfig(config Config) error {
	if err := ValidateConfig(config); err != nil {
		return err
	}
	if !reflect.DeepEqual(scopeFor(config), history.meta.Scope) {
		return fmt.Errorf("history chain, anchor or named wallets differ; use the matching history")
	}
	return nil
}

func scopeFor(config Config) HistoryScope {
	scope := HistoryScope{ChainID: config.ChainID, NetworkID: config.NetworkID, Genesis: config.Genesis, AnchorNumber: config.AnchorNumber, AnchorHash: config.AnchorHash, Wallets: make(map[string]common.Address)}
	for _, node := range config.Nodes {
		scope.Wallets[node.Name] = node.Wallet
	}
	return scope
}

func validateHistoryScope(scope HistoryScope) error {
	config := Config{ChainID: scope.ChainID, NetworkID: scope.NetworkID, Genesis: scope.Genesis, AnchorNumber: scope.AnchorNumber, AnchorHash: scope.AnchorHash}
	for name, wallet := range scope.Wallets {
		config.Nodes = append(config.Nodes, NodeConfig{Name: name, Wallet: wallet, Role: "maintenance", Endpoint: fmt.Sprintf("http://history.invalid/%d", len(config.Nodes))})
	}
	return ValidateConfig(config)
}

func (history *History) Status() (HistoryStatus, error) {
	history.mu.Lock()
	defer history.mu.Unlock()
	state, err := history.load()
	if err != nil {
		return HistoryStatus{}, err
	}
	return state.status(), nil
}

func (history *History) Export(output io.Writer) error {
	history.mu.Lock()
	defer history.mu.Unlock()
	if _, err := history.load(); err != nil {
		return err
	}
	encoder := json.NewEncoder(output)
	if err := encoder.Encode(struct{ Metadata historyMetadata }{history.meta}); err != nil {
		return err
	}
	iterator := history.db.NewIterator(nil, nil)
	defer iterator.Release()
	for iterator.Next() {
		if string(iterator.Key()) != "metadata" {
			if err := encoder.Encode(json.RawMessage(iterator.Value())); err != nil {
				return err
			}
		}
	}
	return iterator.Error()
}

func (history *History) Record(config Config, report Report) (HistoryStatus, error) {
	history.mu.Lock()
	defer history.mu.Unlock()
	if err := history.CheckConfig(config); err != nil {
		return HistoryStatus{}, err
	}
	state, err := history.load()
	if err != nil {
		return HistoryStatus{}, err
	}
	return history.append(state, historyEvent{Sequence: state.Sequence + 1, TimeUTC: report.FinishedUTC, Report: &report})
}

func (history *History) Review(review Review, expectedSequence uint64, when time.Time) (HistoryStatus, error) {
	history.mu.Lock()
	defer history.mu.Unlock()
	state, err := history.load()
	if err != nil {
		return HistoryStatus{}, err
	}
	if state.Sequence != expectedSequence {
		return HistoryStatus{}, fmt.Errorf("history changed; inspect current status before review")
	}
	return history.append(state, historyEvent{Sequence: state.Sequence + 1, TimeUTC: when.UTC(), Review: &review})
}

func (history *History) append(state *incidentHistory, event historyEvent) (HistoryStatus, error) {
	raw, err := json.Marshal(event)
	if err != nil {
		return HistoryStatus{}, err
	}
	key := fmt.Sprintf("event/%020d", event.Sequence)
	if len(raw) > maxHistoryEvent || state.LogicalBytes+int64(len(key)+len(raw)) > history.meta.MaxBytes {
		return HistoryStatus{}, fmt.Errorf("history byte budget exhausted; evidence retained without pruning")
	}
	if err := state.apply(event); err != nil {
		return HistoryStatus{}, err
	}
	if err := history.db.Put([]byte(key), raw, &opt.WriteOptions{Sync: true}); err != nil {
		return HistoryStatus{}, fmt.Errorf("history write failed; inspect persisted status before retry: %w", err)
	}
	state.LogicalBytes += int64(len(key) + len(raw))
	return state.status(), nil
}

func (history *History) load() (*incidentHistory, error) {
	state := newIncidentHistory(history.meta)
	iterator := history.db.NewIterator(nil, nil)
	defer iterator.Release()
	metadataSeen := false
	for iterator.Next() {
		key, raw := string(iterator.Key()), iterator.Value()
		state.LogicalBytes += int64(len(key) + len(raw))
		if state.LogicalBytes > history.meta.MaxBytes || len(raw) > maxHistoryEvent {
			return nil, fmt.Errorf("history exceeds its declared bounds")
		}
		if key == "metadata" {
			var meta historyMetadata
			if err := decodeHistory(raw, &meta); err != nil || !reflect.DeepEqual(meta, history.meta) {
				return nil, fmt.Errorf("history metadata changed or is invalid")
			}
			metadataSeen = true
			continue
		}
		if key != fmt.Sprintf("event/%020d", state.Sequence+1) {
			return nil, fmt.Errorf("history sequence is missing or unsupported")
		}
		var event historyEvent
		if err := decodeHistory(raw, &event); err != nil {
			return nil, err
		}
		if err := state.apply(event); err != nil {
			return nil, err
		}
	}
	if err := iterator.Error(); err != nil {
		return nil, err
	}
	if !metadataSeen {
		return nil, fmt.Errorf("history metadata missing")
	}
	return state, nil
}

func decodeHistory(raw []byte, value interface{}) error {
	if len(raw) > maxHistoryEvent {
		return fmt.Errorf("history record too large")
	}
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(value); err != nil {
		return fmt.Errorf("invalid history record: %w", err)
	}
	if decoder.Decode(new(interface{})) != io.EOF {
		return fmt.Errorf("extra history record data")
	}
	return nil
}
