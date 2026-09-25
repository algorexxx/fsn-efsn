package discover

import (
	"context"
	"errors"
	"fmt"
	"net"
	"net/url"
	"strings"
	"time"

	"github.com/FusionFoundation/efsn/v5/log"
)

const (
	bootstrapLookupTimeout   = 5 * time.Second
	bootstrapRetryInterval   = 10 * time.Second
	bootstrapRefreshInterval = 30 * time.Second
	bootstrapMaxRetry        = 5 * time.Minute
)

type BootstrapNodes []*Node

func (nodes *BootstrapNodes) UnmarshalTOML(decode func(interface{}) error) error {
	var urls []string
	if err := decode(&urls); err != nil {
		return err
	}
	parsed := make(BootstrapNodes, 0, len(urls))
	for _, raw := range urls {
		n, err := ParseBootnode(raw)
		if err != nil {
			return err
		}
		parsed = append(parsed, n)
	}
	*nodes = parsed
	return nil
}

func ParseBootnode(raw string) (*Node, error) {
	n, err := parseNodeEndpoint(raw)
	if err != nil {
		return nil, err
	}
	u, err := url.Parse(raw)
	if err != nil {
		return nil, err
	}
	query, err := url.ParseQuery(u.RawQuery)
	if err != nil || u.Path != "" || u.Fragment != "" || u.ForceQuery || len(query) > 1 || (len(query) == 1 && len(query["discport"]) != 1) || (len(query) == 1 && query.Get("discport") == "") {
		return nil, errors.New("invalid bootstrap URL suffix")
	}
	if err := n.validateBootstrap(); err != nil {
		return nil, err
	}
	return n, nil
}

func (n *Node) validateBootstrap() error {
	if n == nil || n.UDP == 0 {
		return errors.New("missing bootstrap UDP port")
	}
	if _, err := n.ID.Pubkey(); err != nil {
		return err
	}
	if n.hostname != "" {
		name := strings.TrimSuffix(n.hostname, ".")
		if len(name) == 0 || len(name) > 253 {
			return errors.New("invalid bootstrap hostname")
		}
		for _, label := range strings.Split(name, ".") {
			if len(label) == 0 || len(label) > 63 || label[0] == '-' || label[len(label)-1] == '-' {
				return errors.New("invalid bootstrap hostname")
			}
			for _, c := range label {
				if !(c >= 'a' && c <= 'z' || c >= 'A' && c <= 'Z' || c >= '0' && c <= '9' || c == '-') {
					return errors.New("invalid bootstrap hostname")
				}
			}
		}
		return nil
	}
	if n.IP.To16() == nil || n.IP.IsMulticast() || n.IP.IsUnspecified() {
		return errors.New("invalid bootstrap IP")
	}
	return nil
}

func (tab *Table) resolveBootstrap(ctx context.Context, seed *Node) error {
	lookupCtx, cancel := context.WithTimeout(ctx, bootstrapLookupTimeout)
	defer cancel()
	addresses, err := net.DefaultResolver.LookupIPAddr(lookupCtx, seed.hostname)
	if err != nil {
		return err
	}
	if len(addresses) > bucketSize {
		addresses = addresses[:bucketSize]
	}
	for _, address := range addresses {
		if ctx.Err() != nil {
			return ctx.Err()
		}
		n := NewNode(seed.ID, address.IP, seed.UDP, seed.TCP)
		if n.validateBootstrap() != nil || address.Zone != "" || (tab.netrestrict != nil && !tab.netrestrict.Contains(n.IP)) || n.ID == tab.self.ID {
			continue
		}
		if tab.net.ping(n.ID, n.addr()) != nil {
			continue
		}
		tab.add(n)
		select {
		case tab.refreshReq <- make(chan struct{}):
		case <-ctx.Done():
			return ctx.Err()
		}
		return nil
	}
	return fmt.Errorf("no reachable allowed address for %s", seed.hostname)
}

func (tab *Table) bootstrapLoop(ctx context.Context, seed *Node) {
	delay := bootstrapRetryInterval
	failed := false
	for ctx.Err() == nil {
		err := tab.resolveBootstrap(ctx, seed)
		if ctx.Err() != nil {
			return
		}
		wait := bootstrapRefreshInterval
		if err != nil {
			if !failed {
				log.Warn("Bootstrap contact unavailable; retrying", "host", seed.hostname, "id", seed.ID, "err", err)
			}
			wait = delay
			delay *= 2
			if delay > bootstrapMaxRetry {
				delay = bootstrapMaxRetry
			}
		} else {
			if failed {
				log.Info("Bootstrap contact recovered", "host", seed.hostname, "id", seed.ID)
			}
			delay = bootstrapRetryInterval
		}
		failed = err != nil
		timer := time.NewTimer(wait)
		select {
		case <-timer.C:
		case <-ctx.Done():
			timer.Stop()
			return
		}
	}
}
