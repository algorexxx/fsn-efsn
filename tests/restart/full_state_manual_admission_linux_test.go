package restart

import (
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
)

func TestFullStateManualGapHistoricalAdmission(t *testing.T) {
	rehearseHistoricalPurchaseAdmission(t, 15130120, 15130121, 16, common.HexToHash("0xb48486a5a0d79ba11ed9c67107e7e83aa886c3309fbb9785fc7cbe21fd9b0e61"), "insufficient balance")
}
