package restart

import (
	"crypto/sha256"
	"encoding/hex"
	"os"
	"testing"
)

func stateExportFileHash(t *testing.T, path string) string {
	t.Helper()
	data, err := os.ReadFile(path)
	requireNoError(t, err)
	digest := sha256.Sum256(data)
	return hex.EncodeToString(digest[:])
}
