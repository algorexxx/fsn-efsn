package main

var f11ConfigVectors = map[string]struct {
	JSON   string
	SHA256 string
}{
	"legacy":    {"{\"chainId\":32659,\"homesteadBlock\":0,\"eip150Hash\":\"0x0000000000000000000000000000000000000000000000000000000000000000\",\"eip155Block\":0,\"eip158Block\":0,\"byzantiumBlock\":0,\"datong\":{\"period\":15}}", "ff7b12b7a6cd99eb982e1319b6fe35a8239e55308f847cc80a6ed608958187ce"},
	"effective": {"{\"chainId\":32659,\"homesteadBlock\":0,\"eip150Hash\":\"0x0000000000000000000000000000000000000000000000000000000000000000\",\"eip155Block\":0,\"eip158Block\":0,\"byzantiumBlock\":0,\"datong\":{\"period\":15},\"suicideTimeLockFixBlock\":100}", "ce4a56f92966ad36746e15322735e08e673e45a184a9f8886822dc11f2be702b"},
	"different": {"{\"chainId\":32659,\"homesteadBlock\":0,\"eip150Hash\":\"0x0000000000000000000000000000000000000000000000000000000000000000\",\"eip155Block\":0,\"eip158Block\":0,\"byzantiumBlock\":0,\"datong\":{\"period\":15},\"suicideTimeLockFixBlock\":101}", "60ce83b686c4399d514738c69549429f855d84e975fe99a49cd6bafcbb73fd03"},
}
