package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"syscall"
	"time"

	"github.com/syndtr/goleveldb/leveldb"
	"github.com/syndtr/goleveldb/leveldb/opt"
	"github.com/syndtr/goleveldb/leveldb/util"
)

func must(err error) {
	if err != nil {
		panic(err)
	}
}

func value(i int) []byte {
	seed := make([]byte, 8)
	binary.LittleEndian.PutUint64(seed, uint64(i))
	h := sha256.Sum256(seed)
	return bytes.Repeat(h[:], 128)
}

func main() {
	mode, path := os.Args[1], os.Args[2]
	options := &opt.Options{WriteBuffer: 2 * opt.MiB, OpenFilesCacheCapacity: 32}
	if mode == "contend" {
		db, err := leveldb.OpenFile(path, options)
		if err == nil {
			db.Close()
			panic("second writable open was accepted")
		}
		if !errors.Is(err, syscall.EWOULDBLOCK) && !errors.Is(err, syscall.EAGAIN) {
			panic(fmt.Sprintf("unexpected second-open error: %v", err))
		}
		fmt.Printf("second-open-refused: %v\n", err)
		return
	}
	db, err := leveldb.OpenFile(path, options)
	must(err)
	if mode == "exit-without-close" {
		must(db.Put([]byte("sync-marker"), []byte("committed-before-process-exit"), &opt.WriteOptions{Sync: true}))
		os.Exit(0)
	}
	start := time.Now()
	checks := map[string]interface{}{}
	out, err := exec.Command(os.Args[0], "contend", path).CombinedOutput()
	must(err)
	checks["second_writer"] = string(out)
	for offset := 0; offset < 8192; offset += 64 {
		batch := new(leveldb.Batch)
		for i := offset; i < offset+64; i++ {
			batch.Put([]byte(fmt.Sprintf("key-%08d", i)), value(i))
		}
		must(db.Write(batch, &opt.WriteOptions{Sync: true}))
	}
	checks["sync_write_32MiB_seconds"] = time.Since(start).Seconds()
	start = time.Now()
	must(db.CompactRange(util.Range{}))
	checks["compact_seconds"] = time.Since(start).Seconds()
	must(db.Close())
	out, err = exec.Command(os.Args[0], "exit-without-close", path).CombinedOutput()
	if err != nil {
		panic(fmt.Sprintf("process exit check: %s: %v", out, err))
	}
	options.ReadOnly = true
	db, err = leveldb.OpenFile(path, options)
	must(err)
	start = time.Now()
	for i := 0; i < 8192; i++ {
		actual, err := db.Get([]byte(fmt.Sprintf("key-%08d", i)), nil)
		must(err)
		if !bytes.Equal(actual, value(i)) {
			panic(fmt.Sprintf("data mismatch at %d", i))
		}
	}
	actual, err := db.Get([]byte("sync-marker"), nil)
	must(err)
	if string(actual) != "committed-before-process-exit" {
		panic("synchronous marker missing after process exit")
	}
	checks["read_verify_seconds"] = time.Since(start).Seconds()
	checks["values_verified"] = 8192
	checks["sync_marker_after_process_exit"] = true
	must(db.Close())
	checks["status"] = "pass"
	must(json.NewEncoder(os.Stdout).Encode(checks))
}
