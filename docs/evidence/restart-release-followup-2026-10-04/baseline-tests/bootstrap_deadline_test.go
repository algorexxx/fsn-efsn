package discover

import (
	"context"
	"errors"
	"net"
	"testing"
	"time"
)

func TestRestartBootstrapLookupDeadlineAndCancellation(t *testing.T) {
	previous := net.DefaultResolver
	net.DefaultResolver = &net.Resolver{PreferGo: true, Dial: func(ctx context.Context, network, address string) (net.Conn, error) {
		<-ctx.Done()
		return nil, ctx.Err()
	}}
	defer func() { net.DefaultResolver = previous }()
	seed, err := ParseBootnode("enode://" + restartCacheNode(t, 1).ID.String() + "@blocked.restart.invalid:40408")
	if err != nil {
		t.Fatal(err)
	}
	for _, cancelEarly := range []bool{false, true} {
		ctx, cancel := context.WithCancel(context.Background())
		if cancelEarly {
			time.AfterFunc(50*time.Millisecond, cancel)
		}
		started := time.Now()
		err := new(Table).resolveBootstrap(ctx, seed)
		elapsed := time.Since(started)
		cancel()
		limit := 7 * time.Second
		if cancelEarly {
			limit = time.Second
		}
		if err == nil || elapsed > limit {
			t.Fatalf("blocked lookup: cancelEarly=%t elapsed=%s err=%v", cancelEarly, elapsed, err)
		}
		var dnsError *net.DNSError
		if !cancelEarly && (!errors.As(err, &dnsError) || !dnsError.IsTimeout || elapsed < 4*time.Second) {
			t.Fatalf("expected resolver deadline: elapsed=%s err=%v", elapsed, err)
		}
		t.Logf("cancelEarly=%t elapsed=%s err=%v", cancelEarly, elapsed, err)
	}
}
