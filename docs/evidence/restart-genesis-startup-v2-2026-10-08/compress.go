package main

import (
	"compress/gzip"
	"io"
	"os"
)

func main() {
	input, err := os.Open(os.Args[1])
	if err != nil {
		panic(err)
	}
	defer input.Close()
	writer := gzip.NewWriter(os.Stdout)
	if _, err := io.Copy(writer, input); err != nil {
		panic(err)
	}
	if err := writer.Close(); err != nil {
		panic(err)
	}
}
