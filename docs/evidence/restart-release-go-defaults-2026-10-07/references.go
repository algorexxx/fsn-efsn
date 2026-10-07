package main

import (
	"encoding/json"
	"go/ast"
	"go/parser"
	"go/token"
	"io"
	"os"
	"path/filepath"
	"strconv"
)

type dependency struct {
	ImportPath string
	Dir        string
	GoFiles    []string
	CgoFiles   []string
}

type reference struct {
	Package string
	File    string
	Line    int
	Symbol  string
}

func main() {
	input, err := os.Open(os.Args[1])
	if err != nil {
		panic(err)
	}
	defer input.Close()
	decoder := json.NewDecoder(input)
	targets := map[string]map[string]bool{
		"math/rand":   {"Seed": true},
		"runtime":     {"GOMAXPROCS": true, "SetDefaultGOMAXPROCS": true},
		"net/http":    {"ServeMux": true, "NewServeMux": true, "Handle": true, "HandleFunc": true, "ServeContent": true, "ServeFile": true},
		"crypto/x509": {"CreateCertificate": true, "ParseCertificate": true, "ParsePKCS1PrivateKey": true},
	}
	var refs []reference
	for {
		var dep dependency
		if err := decoder.Decode(&dep); err == io.EOF {
			break
		} else if err != nil {
			panic(err)
		}
		for _, name := range append(dep.GoFiles, dep.CgoFiles...) {
			set := token.NewFileSet()
			file, err := parser.ParseFile(set, filepath.Join(dep.Dir, name), nil, 0)
			if err != nil {
				panic(err)
			}
			imports := make(map[string]string)
			for _, imp := range file.Imports {
				path, err := strconv.Unquote(imp.Path.Value)
				if err != nil {
					panic(err)
				}
				alias := filepath.Base(path)
				if imp.Name != nil {
					alias = imp.Name.Name
				}
				if targets[path] != nil && alias == "." {
					panic("target package imported with dot: " + dep.ImportPath)
				}
				imports[alias] = path
			}
			ast.Inspect(file, func(node ast.Node) bool {
				selector, ok := node.(*ast.SelectorExpr)
				if !ok {
					return true
				}
				alias, ok := selector.X.(*ast.Ident)
				if ok && targets[imports[alias.Name]][selector.Sel.Name] {
					refs = append(refs, reference{dep.ImportPath, name, set.Position(selector.Pos()).Line, imports[alias.Name] + "." + selector.Sel.Name})
				}
				return true
			})
		}
	}
	encoder := json.NewEncoder(os.Stdout)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(refs); err != nil {
		panic(err)
	}
}
