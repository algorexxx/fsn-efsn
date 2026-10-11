package utils

import (
	"flag"
	"testing"

	"github.com/FusionFoundation/efsn/v5/p2p"
	"github.com/urfave/cli/v2"
)

func TestExplicitEmptyBootstrapNodes(t *testing.T) {
	for _, name := range []string{BootnodesFlag.Name, BootnodesV4Flag.Name} {
		t.Run(name, func(t *testing.T) {
			set := flag.NewFlagSet("test", flag.ContinueOnError)
			set.String(name, "", "")
			if err := set.Parse([]string{"--" + name, ""}); err != nil {
				t.Fatal(err)
			}
			ctx := cli.NewContext(cli.NewApp(), set, nil)
			if !ctx.IsSet(name) {
				t.Fatal("empty bootstrap option must be explicitly set")
			}
			cfg := new(p2p.Config)
			setBootstrapNodes(ctx, cfg)
			if cfg.BootstrapNodes == nil || len(cfg.BootstrapNodes) != 0 {
				t.Fatalf("expected an explicitly empty bootstrap list, got %v", cfg.BootstrapNodes)
			}
			if name == BootnodesFlag.Name {
				setBootstrapNodesV5(ctx, cfg)
				if cfg.BootstrapNodesV5 == nil || len(cfg.BootstrapNodesV5) != 0 {
					t.Fatalf("expected an explicitly empty v5 bootstrap list, got %v", cfg.BootstrapNodesV5)
				}
			}
		})
	}
}
