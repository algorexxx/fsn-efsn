const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const { chromium } = require('playwright');

const evidence = __dirname;
const started = JSON.parse(fs.readFileSync(path.join(evidence, 'browser.stdout.txt'), 'utf8').split('\n')[0]);
const python = 'C:/Users/Peter/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe';
const results = [];
const errors = [];
const failedRequests = [];
const foreignRequests = [];
const responses = [];

function scenario(mode, nodeId) {
    execFileSync(python, [path.join(evidence, 'set-browser-scenario.py'), mode, nodeId || 'synthetic-alpha']);
}

async function record(page, name) {
    const snapshot = await page.locator('[aria-live="polite"]').innerText();
    const rows = await page.locator('tbody tr').allTextContents();
    results.push({ name, snapshot, rows });
}

async function main() {
    const browser = await chromium.launch({ channel: 'msedge', headless: true, chromiumSandbox: true });
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    const page = await context.newPage();
    page.on('pageerror', error => errors.push(error.message));
    page.on('requestfailed', request => failedRequests.push({ url: request.url(), error: request.failure().errorText }));
    page.on('response', response => responses.push({ url: response.url(), status: response.status() }));
    await context.route('**/*', route => {
        if (new URL(route.request().url()).origin !== started.url) {
            foreignRequests.push(route.request().url());
            return route.abort();
        }
        return route.continue();
    });
    try {
        await page.goto(started.url, { waitUntil: 'domcontentloaded' });
        await page.getByRole('button', { name: 'Pin synthetic-alpha', exact: true }).waitFor();
        assert.equal(await page.locator('tbody tr').count(), 2);
        assert.match(await page.locator('body').innerText(), /Connected Nodes 1\/2/i);
        assert.match(await page.locator('body').innerText(), /# 42/);
        await record(page, 'populated');
        await page.screenshot({ path: path.join(evidence, 'browser-populated.png'), fullPage: true });
        await page.getByRole('button', { name: 'Pin synthetic-alpha', exact: true }).focus();
        await page.keyboard.press('Space');
        await page.getByRole('button', { name: 'Unpin synthetic-alpha', exact: true }).waitFor();
        await record(page, 'keyboard-pin');
        await page.getByRole('button', { name: 'Unpin synthetic-alpha', exact: true }).click();
        await page.getByRole('button', { name: /^view map$/i }).click();
        await page.locator('.modal svg.datamap').waitFor();
        await page.locator('.modal circle.datamaps-bubble').first().waitFor();
        assert.equal(await page.locator('.modal circle.datamaps-bubble').count(), 2);
        await page.screenshot({ path: path.join(evidence, 'browser-map.png'), fullPage: true });
        await page.getByRole('dialog', { name: 'Geo Map', exact: true }).waitFor();
        results.push({ name: 'map', rendered: true, accessible: true, reportedNodeMarkers: 2 });
        const modalControls = await page.locator('.modal button').evaluateAll(elements => elements.map(element => {
            const ancestors = [];
            for (let parent = element; parent; parent = parent.parentElement) {
                ancestors.push({tag: parent.tagName, role: parent.getAttribute('role'), hidden: parent.getAttribute('aria-hidden')});
            }
            return {html: element.outerHTML, ancestors};
        }));
        assert.equal(modalControls.length, 2);
        assert.equal(modalControls.some(control => control.ancestors.some(ancestor => ancestor.hidden === 'true')), false);
        fs.writeFileSync(path.join(evidence, 'modal-controls.json'), JSON.stringify(modalControls, null, 2));
        await page.getByRole('button', { name: /^close$/i }).last().click();
        scenario('empty');
        await page.getByText('No nodes reported.', { exact: false }).waitFor();
        assert.equal(await page.locator('tbody tr').count(), 0);
        assert.match(await page.locator('body').innerText(), /Connected Nodes 0\/0/i);
        await record(page, 'empty');
        scenario('ready', 'synthetic-beta');
        await page.getByRole('button', { name: 'Pin synthetic-beta', exact: true }).waitFor();
        scenario('unavailable');
        await page.getByText('Dashboard data unavailable or expired.', { exact: false }).waitFor();
        assert.equal(await page.locator('tbody tr').count(), 0);
        await record(page, 'storage-failure');
        await page.screenshot({ path: path.join(evidence, 'browser-unavailable.png'), fullPage: true });
        scenario('ready', 'synthetic-recovered');
        await page.getByRole('button', { name: 'Pin synthetic-recovered', exact: true }).waitFor();
        await record(page, 'recovered');
        scenario('expired');
        await page.getByText('Dashboard data unavailable or expired.', { exact: false }).waitFor();
        assert.equal(await page.locator('tbody tr').count(), 0);
        await record(page, 'expired-storage');
        scenario('ready', 'synthetic-before-timeout');
        await page.getByRole('button', { name: 'Pin synthetic-before-timeout', exact: true }).waitFor();
        scenario('hanging');
        await page.getByText('Dashboard data unavailable or expired.', { exact: false }).waitFor();
        assert.equal(await page.locator('tbody tr').count(), 0);
        await record(page, 'request-timeout');
        scenario('ready', 'synthetic-final');
        await page.getByRole('button', { name: 'Pin synthetic-final', exact: true }).waitFor();
        await record(page, 'timeout-recovery');
        assert.deepEqual(errors, []);
        assert.deepEqual(foreignRequests, []);
        assert.equal(responses.some(response => response.status === 404), false);
        fs.writeFileSync(path.join(evidence, 'browser-result.json'), JSON.stringify({
            passed: true, browser: browser.version(), playwright: require('playwright/package.json').version,
            url: started.url, results, errors, failedRequests, foreignRequests, responses,
        }, null, 2) + '\n');
    } catch (error) {
        await page.screenshot({ path: path.join(evidence, 'browser-failure.png'), fullPage: true });
        fs.writeFileSync(path.join(evidence, 'browser-failure.json'), JSON.stringify({ error: error.message, results, errors, failedRequests, foreignRequests, responses }, null, 2) + '\n');
        throw error;
    } finally {
        await browser.close();
    }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
