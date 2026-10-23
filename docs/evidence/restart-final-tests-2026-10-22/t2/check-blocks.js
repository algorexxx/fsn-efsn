// Usage: efsn attach IPC --exec "var FROM=N, TO=M; loadScript('check-blocks.js')"
var FSNCALL = "0xffffffffffffffffffffffffffffffffffffffff";
var miners = {}, buyers = {}, withoutBuy = [], failed = 0, total = 0;
for (var n = FROM; n <= TO; n++) {
  var b = eth.getBlock(n, true);
  if (b == null) { break; }
  total++;
  miners[b.miner] = (miners[b.miner] || 0) + 1;
  var buys = 0;
  for (var i = 0; i < b.transactions.length; i++) {
    var tx = b.transactions[i];
    if (tx.to && tx.to.toLowerCase() == FSNCALL) {
      var r = eth.getTransactionReceipt(tx.hash);
      var ok = r.status == "0x1" || r.status == 1;
      var nativeErr = false;
      for (var k = 0; k < r.logs.length; k++) { if (web3.toAscii(r.logs[k].data).indexOf('"Error"') >= 0) nativeErr = true; }
      if (ok && !nativeErr) { buys++; buyers[tx.from] = (buyers[tx.from] || 0) + 1; } else { failed++; }
    }
  }
  if (buys == 0) withoutBuy.push(n);
}
console.log("blocks " + FROM + ".." + (FROM + total - 1) + " total=" + total + " miners=" + JSON.stringify(miners) + " buyers=" + JSON.stringify(buyers) + " failedCalls=" + failed + " blocksWithoutPurchase=" + JSON.stringify(withoutBuy));
