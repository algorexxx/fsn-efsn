package observe

import (
	"fmt"
	"time"
)

type HistoryCheck struct {
	Version      int
	CheckedUTC   time.Time
	MaxReportAge string
	MinFreeBytes int64
	Problems     []string
	History      HistoryStatus
}

func CheckHistory(status HistoryStatus, now time.Time, maxReportAge time.Duration, minFreeBytes int64) (HistoryCheck, error) {
	if now.IsZero() || maxReportAge <= 0 || minFreeBytes <= 0 || minFreeBytes > status.MaxBytes {
		return HistoryCheck{}, fmt.Errorf("history check requires a current time, positive maximum report age and minimum free bytes within its budget")
	}
	check := HistoryCheck{Version: 1, CheckedUTC: now.UTC(), MaxReportAge: maxReportAge.String(), MinFreeBytes: minFreeBytes, Problems: []string{}, History: status}
	if status.LastReportUTC.IsZero() {
		check.Problems = append(check.Problems, "collection_missing")
	} else if now.Sub(status.LastReportUTC) >= maxReportAge {
		check.Problems = append(check.Problems, "collection_stale")
	}
	if status.LastEventUTC.After(now) || status.LastReportUTC.After(now) {
		check.Problems = append(check.Problems, "history_time_in_future")
	}
	if status.MaxBytes-status.LogicalBytes < minFreeBytes {
		check.Problems = append(check.Problems, "history_headroom_low")
	}
	for _, incident := range status.Incidents {
		if incident.Status != "resolved" {
			check.Problems = append(check.Problems, "unresolved_incidents")
			break
		}
	}
	return check, nil
}
