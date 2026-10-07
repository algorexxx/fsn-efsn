package main

import (
	"bytes"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"

	"golang.org/x/crypto/sha3"
)

func hash(data []byte) []byte {
	h := sha3.NewLegacyKeccak256()
	h.Write(data)
	return h.Sum(nil)
}

func prefix(size int, short, long byte) []byte {
	if size < 56 {
		return []byte{short + byte(size)}
	}
	var length []byte
	for n := size; n > 0; n >>= 8 {
		length = append([]byte{byte(n)}, length...)
	}
	return append([]byte{long + byte(len(length))}, length...)
}

func encode(value interface{}) []byte {
	switch v := value.(type) {
	case []byte:
		if len(v) == 1 && v[0] < 128 {
			return v
		}
		return append(prefix(len(v), 128, 183), v...)
	case []interface{}:
		var payload []byte
		for _, item := range v {
			payload = append(payload, encode(item)...)
		}
		return append(prefix(len(payload), 192, 247), payload...)
	default:
		panic("unsupported fixture value")
	}
}

func main() {
	emptyCode := hash(nil)
	emptyTrie := hash(encode([]byte{}))
	if hex.EncodeToString(emptyCode) != "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470" || hex.EncodeToString(emptyTrie) != "56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421" {
		panic("known Keccak vectors failed")
	}
	accounts := make(map[string]interface{})
	roots := make(map[string]string)
	for _, schema := range []string{"ethereum", "fusion"} {
		branch := make([]interface{}, 17)
		for i := range branch {
			branch[i] = []byte{}
		}
		for i, suffix := range [][]byte{{1}, {2}, {1, 2}} {
			address := append(make([]byte, 20-len(suffix)), suffix...)
			key := hash(address)
			code := []byte{}
			balance := []byte{byte(22 * (i + 1))}
			if i == 2 {
				code = bytes.Repeat([]byte{3}, 7)
				balance = []byte{}
			}
			codeHash := hash(code)
			account := []interface{}{[]byte{}, balance, emptyTrie, codeHash}
			if schema == "fusion" {
				assetHashes, assetValues := []interface{}{}, []interface{}{}
				balances := make(map[string]int)
				if len(balance) != 0 {
					asset := bytes.Repeat([]byte{255}, 32)
					assetHashes = append(assetHashes, asset)
					assetValues = append(assetValues, balance)
					balances["0x"+hex.EncodeToString(asset)] = int(balance[0])
				}
				account = []interface{}{[]byte{}, []byte{}, assetHashes, assetValues, []interface{}{}, []interface{}{}, emptyTrie, codeHash}
				dump := map[string]interface{}{"balance": balances, "timelock": map[string]interface{}{}, "nonce": 0,
					"root": "0x" + hex.EncodeToString(emptyTrie), "codeHash": "0x" + hex.EncodeToString(codeHash), "key": "0x" + hex.EncodeToString(key)}
				if len(code) != 0 {
					dump["code"] = "0x" + hex.EncodeToString(code)
				}
				accounts["0x"+hex.EncodeToString(address)] = dump
			}
			nibble := key[0] >> 4
			if len(branch[nibble].([]byte)) != 0 {
				panic("fixture requires distinct first nibbles")
			}
			path := append([]byte{0x30 | key[0]&15}, key[1:]...)
			leaf := encode([]interface{}{path, encode(account)})
			if len(leaf) < 32 {
				panic("fixture requires hashed leaves")
			}
			branch[nibble] = hash(leaf)
		}
		roots[schema] = hex.EncodeToString(hash(encode(branch)))
	}
	if roots["ethereum"] != "71edff0130dd2385947095001c73d9e28d862fc286fca2b922ca6f6f3cddfdd2" {
		panic("original Ethereum fixture root mismatch: " + roots["ethereum"])
	}
	fmt.Fprintln(os.Stderr, "Verified original Ethereum root:", roots["ethereum"])
	encoder := json.NewEncoder(os.Stdout)
	encoder.SetIndent("", "    ")
	if err := encoder.Encode(map[string]interface{}{"root": roots["fusion"], "accounts": accounts}); err != nil {
		panic(err)
	}
}
