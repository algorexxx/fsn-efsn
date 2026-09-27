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
	if err := flags.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if *path == "" || *timeout <= 0 || flags.NArg() != 0 {
		return fmt.Errorf("--config and positive --timeout are required; no positional arguments")
	}
	file, err := os.Open(*path)
	if err != nil {
		return fmt.Errorf("cannot open observer config")
	}
	defer file.Close()
	config, err := observe.ReadConfig(file)
	if err != nil {
		return err
	}
	report, err := observe.Collect(ctx, config, *timeout, time.Now)
	if err != nil {
		return err
	}
	encoder := json.NewEncoder(output)
	encoder.SetIndent("", "  ")
	return encoder.Encode(report)
}
