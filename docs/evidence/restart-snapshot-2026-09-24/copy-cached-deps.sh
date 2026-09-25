#!/bin/bash
set -euo pipefail
module_source=/home/rehearsal/go/pkg/mod/cache/download
module_target=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/tmp/restart-runtime/gopath/pkg/mod/cache/download
for module in github.com/golang-jwt/jwt/v4 github.com/rs/cors github.com/fjl/memsize github.com/mattn/go-colorable github.com/mattn/go-isatty github.com/urfave/cli/v2 github.com/cpuguy83/go-md2man/v2 github.com/xrash/smetrics github.com/russross/blackfriday/v2; do
    test -d "$module_source/$module/@v"
    mkdir -p "$module_target/$module/@v"
    cp --update=none "$module_source/$module/@v/"* "$module_target/$module/@v/"
done
