package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"os"
	"os/signal"
	"time"

	"github.com/FusionFoundation/efsn/v5/internal/observe"
)

func main() {
	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt)
	defer cancel()
	if err := run(ctx, os.Args[1:], os.Stdout, os.Stderr); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func run(ctx context.Context, args []string, output, diagnostics io.Writer) error {
	flags := flag.NewFlagSet("fsn-observe", flag.ContinueOnError)
	flags.SetOutput(diagnostics)
	path := flags.String("config", "", "JSON with explicit identities, node roles/endpoints and optional signed transactions")
	timeout := flags.Duration("timeout", 0, "required positive deadline per node and comparison, e.g. 10s; not an alert threshold")
	historyPath := flags.String("history", "", "absolute initialized observer history directory; never a node datadir")
	initialize := flags.Bool("init-history", false, "create a new history directory from --config without contacting nodes")
	budget := flags.Int64("history-budget", 0, "required logical byte budget for --init-history; no automatic pruning")
	statusOnly := flags.Bool("history-status", false, "reconstruct history status without contacting nodes")
	export := flags.Bool("history-export", false, "export metadata and original events as JSON Lines without contacting nodes")
	action := flags.String("history-action", "", "record an operator review: acknowledge or resolve")
	incident := flags.String("incident", "", "incident ID to review")
	sequence := flags.Uint64("at-sequence", 0, "expected current history sequence for review")
	reason := flags.String("reason", "", "explicit operator review reason; not a notification")
	backfillNode := flags.String("backfill-node", "", "collect complete block/receipt evidence for this configured node into --history")
	backfillBlocks := flags.Uint64("backfill-blocks", 0, "required backfill batch bound, from 1 through 128; requires --backfill-node")
	ticketNode := flags.String("ticket-timeline", "", "derive an offline ticket timeline for this history node's wallet")
	ticketFrom := flags.Uint64("ticket-from", 0, "first timeline event height; defaults to anchor plus one; earlier inventory is replayed")
	ticketBlocks := flags.Uint64("ticket-blocks", 0, "required timeline range bound, 1 through 128 blocks")
	anchorNode := flags.String("anchor-inventory", "", "collect historical anchor tickets for this configured node into --history")
	if err := flags.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	operations := 0
	for _, selected := range []bool{*initialize, *statusOnly, *export, *action != "", *ticketNode != ""} {
		if selected {
			operations++
		}
	}
	if flags.NArg() != 0 || *budget != 0 && !*initialize || (*incident != "" || *sequence != 0 || *reason != "") && *action == "" {
		return fmt.Errorf("invalid observer/history argument combination")
	}
	if (*ticketFrom != 0 || *ticketBlocks != 0) && *ticketNode == "" || *ticketNode != "" && (*ticketBlocks == 0 || *ticketBlocks > 128) {
		return fmt.Errorf("ticket timeline requires --ticket-timeline and --ticket-blocks from 1 through 128")
	}
	if (*backfillNode != "" || *backfillBlocks != 0) && (operations != 0 || *historyPath == "" || *backfillNode == "" || *backfillBlocks == 0 || *backfillBlocks > 128) {
		return fmt.Errorf("backfill requires --history, --backfill-node and --backfill-blocks from 1 through 128; offline history operations are separate")
	}
	if *anchorNode != "" && (operations != 0 || *historyPath == "" || *backfillNode != "" || *backfillBlocks != 0) {
		return fmt.Errorf("anchor inventory requires --history and separate collection flags")
	}
	if operations > 0 {
		if operations != 1 || *historyPath == "" || *timeout != 0 || !*initialize && *path != "" {
			return fmt.Errorf("select one history operation with --history; collection flags are separate")
		}
		var history *observe.History
		var err error
		if *initialize {
			config, readErr := readConfig(*path)
			if readErr != nil {
				return readErr
			}
			history, err = observe.CreateHistory(*historyPath, config, *budget)
		} else {
			history, err = observe.OpenHistory(*historyPath)
		}
		if err != nil {
			return err
		}
		defer history.Close()
		if *export {
			return history.Export(output)
		}
		if *ticketNode != "" {
			timeline, err := history.TicketTimeline(*ticketNode, *ticketFrom, *ticketBlocks)
			if err != nil {
				return err
			}
			return writeJSON(output, timeline)
		}
		var state observe.HistoryStatus
		if *action != "" {
			if *sequence == 0 {
				return fmt.Errorf("review requires an explicit positive --at-sequence")
			}
			state, err = history.Review(observe.Review{Action: *action, Incident: *incident, Reason: *reason}, *sequence, time.Now())
		} else {
			state, err = history.Status()
		}
		if err != nil {
			return err
		}
		return writeJSON(output, state)
	}
	if *path == "" || *timeout <= 0 {
		return fmt.Errorf("--config and positive --timeout are required; no positional arguments")
	}
	config, err := readConfig(*path)
	if err != nil {
		return err
	}
	var history *observe.History
	if *historyPath != "" {
		history, err = observe.OpenHistory(*historyPath)
		if err != nil {
			return err
		}
		defer history.Close()
		if err := history.CheckConfig(config); err != nil {
			return err
		}
	}
	if *backfillNode != "" {
		state, err := history.Backfill(ctx, config, *backfillNode, *backfillBlocks, *timeout, time.Now)
		if err != nil {
			return err
		}
		return writeJSON(output, state)
	}
	if *anchorNode != "" {
		report, err := history.CollectAnchorInventory(ctx, config, *anchorNode, *timeout, time.Now)
		if err != nil {
			return err
		}
		return writeJSON(output, report)
	}
	report, err := observe.Collect(ctx, config, *timeout, time.Now)
	if err != nil {
		return err
	}
	if history != nil {
		state, err := history.Record(config, report)
		if err != nil {
			return err
		}
		return writeJSON(output, struct {
			observe.Report
			History observe.HistoryStatus
		}{report, state})
	}
	return writeJSON(output, report)
}

func readConfig(path string) (observe.Config, error) {
	file, err := os.Open(path)
	if err != nil {
		return observe.Config{}, fmt.Errorf("cannot open observer config")
	}
	defer file.Close()
	return observe.ReadConfig(file)
}

func writeJSON(output io.Writer, value interface{}) error {
	encoder := json.NewEncoder(output)
	encoder.SetIndent("", "  ")
	return encoder.Encode(value)
}
