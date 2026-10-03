const { createRequire } = require('node:module');
const { resolve } = require('node:path');
const requireDashboard = createRequire(resolve(process.argv[2], 'package.json'));
const Collection = requireDashboard('./lib/collection');
const History = requireDashboard('./lib/history');

function block(number) {
    return { number, hash: `0x${number.toString(16).padStart(64, '0')}`, parentHash: '0x' + '0'.repeat(64), difficulty: '1', totalDifficulty: '1', timestamp: 1704067200, gasLimit: 1000000, gasUsed: 0, transactions: [], uncles: [], miner: '0x' + '0'.repeat(40) };
}

const ascending = new History();
ascending.add(block(100), 'synthetic-node', false);
ascending.add(block(101), 'synthetic-node', false);
console.log(JSON.stringify({ scenario: 'new head while chart cache is partially filled', storedHeights: ascending._items.map(item => item.height) }));

const collection = new Collection({ write() {} });
collection.add({ id: 'synthetic-node', info: {}, ip: '127.0.0.1', spark: 'synthetic-session' }, () => {});
collection.addBlock('synthetic-node', block(100), () => {});
collection.setChartsCallback((error, charts) => {
    console.log(JSON.stringify({ scenario: 'head 100 followed by 50-block history', error, storedHeights: collection.getHistory()._items.map(item => item.height), chartHeights: charts.height }));
});
collection.addHistory('synthetic-node', Array.from({ length: 50 }, (_, index) => block(100 - index)), () => {});
