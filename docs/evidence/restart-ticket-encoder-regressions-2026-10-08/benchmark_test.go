package encoderbench

import (
	"bytes"
	"compress/gzip"
	"io"
	"os"
	"path/filepath"
	"testing"
)

var retained []byte

func BenchmarkEncode(b *testing.B) {
	for _, height := range []string{"0", "15130080", "12000000"} {
		b.Run(height, func(b *testing.B) {
			payload, err := os.ReadFile(filepath.Join(os.Getenv("F12_VECTORS"), height+".rlp"))
			if err != nil {
				b.Fatal(err)
			}
			encoded, err := encode(payload)
			if err != nil {
				b.Fatal(err)
			}
			reader, err := gzip.NewReader(bytes.NewReader(encoded))
			if err != nil {
				b.Fatal(err)
			}
			decoded, err := io.ReadAll(reader)
			if err != nil {
				b.Fatal(err)
			}
			if err := reader.Close(); err != nil {
				b.Fatal(err)
			}
			if !bytes.Equal(decoded, payload) {
				b.Fatal("round trip differs")
			}
			if os.Getenv("F12_EXPECT_PRESERVED") == "1" {
				preserved, err := os.ReadFile(filepath.Join(os.Getenv("F12_VECTORS"), height+".gz"))
				if err != nil {
					b.Fatal(err)
				}
				if !bytes.Equal(encoded, preserved) {
					b.Fatal("output differs from preserved bytes")
				}
			}
			b.SetBytes(int64(len(payload)))
			b.ReportAllocs()
			b.ResetTimer()
			for i := 0; i < b.N; i++ {
				retained, err = encode(payload)
				if err != nil {
					b.Fatal(err)
				}
			}
		})
	}
}
