const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require('playwright');

async function main() {
    const mode = process.argv[2];
    assert.ok(['baseline', 'final'].includes(mode));
    assert.match(process.argv[3], /^pins-(baseline|final)(-[1-9][0-9]*)?$/);
    const directory = path.join(__dirname, process.argv[3]);
    const started = JSON.parse(fs.readFileSync(path.join(directory, 'server.stdout.txt'), 'utf8').split('\n')[0]);
    const cases = [
        {name: 'malformed-json', stored: '{broken', pinned: false},
        {name: 'object-value', stored: '{"alpha":true}', pinned: false},
        {name: 'denied-access', denied: true, pinned: false, temporary: true},
        {name: 'missing-value', pinned: false},
        {name: 'mixed-values', stored: '["synthetic-alpha",17,null,"synthetic-alpha",""]', pinned: true},
        {name: 'quota-exceeded', quota: true, pinned: false, temporary: true},
        {name: 'saved-pin', stored: '["synthetic-alpha"]', pinned: true},
    ];
    const browser = await chromium.launch({channel: 'msedge', headless: true, chromiumSandbox: true});
    const results = [];
    try {
        for (const fixture of mode === 'baseline' ? cases.slice(0, 3) : cases) {
            const expectedRows = mode === 'baseline' ? 0 : 2;
            const context = await browser.newContext({viewport: {width: 1440, height: 1000}});
            const page = await context.newPage();
            const errors = [];
            const foreign = [];
            page.on('pageerror', error => errors.push(error.message));
            await context.route('**/*', route => {
                if (new URL(route.request().url()).origin !== started.url) {
                    foreign.push(route.request().url());
                    return route.abort();
                }
                return route.continue();
            });
            await page.addInitScript(value => {
                if (value.stored !== undefined) {
                    localStorage.setItem('pinnedNodes', value.stored);
                }
                if (value.denied) {
                    Object.defineProperty(window, 'localStorage', {get() { throw new DOMException('Storage disabled for local test', 'SecurityError'); }});
                }
                if (value.quota) {
                    Storage.prototype.setItem = function () { throw new DOMException('Storage full for local test', 'QuotaExceededError'); };
                }
            }, fixture);
            await page.goto(started.url, {waitUntil: 'load'});
            if (mode === 'baseline') {
                await page.waitForTimeout(750);
            } else {
                await page.getByRole('button', {name: (fixture.pinned ? 'Unpin ' : 'Pin ') + 'synthetic-alpha', exact: true}).waitFor();
            }
            const rows = await page.locator('tbody tr').count();
            assert.equal(rows, expectedRows, fixture.name);
            if (mode === 'baseline' && fixture.name !== 'object-value') {
                assert.ok(errors.length > 0, fixture.name);
            }
            assert.deepEqual(foreign, []);
            if (mode === 'final') {
                await page.getByRole('button', {name: (fixture.pinned ? 'Unpin ' : 'Pin ') + 'synthetic-alpha', exact: true}).click();
                await page.getByRole('button', {name: (fixture.pinned ? 'Pin ' : 'Unpin ') + 'synthetic-alpha', exact: true}).waitFor();
                if (fixture.temporary) {
                    await page.getByText('Pin changes cannot be saved in this browser. They will last until this page is reloaded.', {exact: true}).waitFor();
                } else {
                    const stored = await page.evaluate(() => JSON.parse(localStorage.getItem('pinnedNodes')));
                    assert.deepEqual(stored, fixture.pinned ? [] : ['synthetic-alpha']);
                }
                if (fixture.name === 'missing-value') {
                    await page.reload({waitUntil: 'load'});
                    await page.getByRole('button', {name: 'Unpin synthetic-alpha', exact: true}).waitFor();
                    await page.getByText('Hide non-pinned Nodes', {exact: false}).locator('.fe-square').click();
                    assert.equal(await page.locator('tbody tr').count(), 1);
                    await page.getByRole('button', {name: 'Unpin synthetic-alpha', exact: true}).click();
                    assert.equal(await page.locator('tbody tr').count(), 2);
                }
                assert.deepEqual(errors, [], fixture.name);
                await page.screenshot({path: path.join(directory, fixture.name + '.png')});
            }
            results.push({name: fixture.name, rows, errors, foreign});
            await context.close();
        }
        fs.writeFileSync(path.join(directory, 'result.json'), JSON.stringify({passed: true, mode, browser: browser.version(), results}, null, 2) + '\n');
    } finally {
        await browser.close();
    }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
