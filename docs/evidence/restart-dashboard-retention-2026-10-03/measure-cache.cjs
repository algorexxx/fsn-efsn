const assert = require('node:assert/strict');
const { writeFileSync } = require('node:fs');
const { resolve } = require('node:path');
const History = require('../../../tmp/fsn-stats-auth/lib/history');
const { block } = require('../../../tmp/fsn-stats-auth/test/fixtures/telemetry-report.cjs');

function measure(transactionsPerBlock) {
    global.gc();
    const before = process.memoryUsage();
    const history = new History(() => 1000);
    const transactions = Array.from({ length: transactionsPerBlock }, (_, index) => ({ hash: '0x' + (index + 1).toString(16).padStart(64, '0') }));
    const started = performance.now();
    for (let height = 2000; height >= 1; height--) {
        history.add({ ...block(height), transactions }, 'node-0', false, true);
        for (let fork = 1; fork <= 8; fork++) {
            history.add({ ...block(height, fork), transactions }, 'node-' + (fork - 1), false, true);
        }
    }
    const elapsedMs = performance.now() - started;
    global.gc();
    const retained = process.memoryUsage();
    assert.equal(history._items.length, 2000);
    assert.equal(history._items.every(item => item.forks.length === 9 && item.propagTimes.length === 8), true);
    assert.equal(history._items.every(item => item.forks.every(fork => fork.transactions === undefined && fork.uncles === undefined && fork.transactionCount === transactionsPerBlock)), true);
    const result = { transactionsPerBlock, heights: 2000, identities: 8, forksPerHeight: 9, retainedForks: 18000, elapsedMs, before, retained, heapDeltaBytes: retained.heapUsed - before.heapUsed, serializedCacheBytes: Buffer.byteLength(JSON.stringify(history._items)), serializedVariantBytes: Buffer.byteLength(JSON.stringify(history._items[0].block)) };
    history.add({ ...block(4001), transactions }, 'node-0', false);
    global.gc();
    assert.deepEqual(history._items.map(item => item.height), [4001]);
    result.afterEviction = process.memoryUsage();
    return result;
}

assert.equal(typeof global.gc, 'function');
const rows = [measure(1), measure(714)];
assert.equal(rows[1].serializedCacheBytes - rows[0].serializedCacheBytes, 40000);
const result = { scope: 'Offline synthetic dashboard reports, not signed blocks. Fixed 2,000 heights, 8 identities and 9 retained variants per height. Heap samples after explicit GC; not peak RSS or a deployment limit. Transaction arrays reused by the generator but never retained by the cache.', node: process.version, rows };
writeFileSync(resolve(__dirname, 'cache-measurement.json'), JSON.stringify(result, null, 2) + '\n', 'utf8');
process.stdout.write(JSON.stringify(result, null, 2) + '\n');
