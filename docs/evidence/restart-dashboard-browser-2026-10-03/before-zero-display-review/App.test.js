import React from 'react';
import ReactDOM from 'react-dom';
import {act} from 'react-dom/test-utils';
import axios from 'axios';
import App from './App';

let container;
let requests;
let time;

function snapshot(ids, budget = '1000') {
    const observedAt = '2026-10-03T12:00:00.000Z';
    return {
        status: 200,
        headers: {'x-dashboard-observed-at': observedAt, 'x-dashboard-valid-for-ms': budget},
        data: ids.map((id, index) => ({
            id, utctime: observedAt,
            stats: JSON.stringify({
                id, info: {node: 'efsn/v5.0.0-local'}, geo: null,
                stats: {
                    active: index === 0, mining: true, syncing: false, peers: 1, pending: 0,
                    myTicketNumber: 0, uptime: 100, latency: 0,
                    block: {number: 42, hash: '0x' + '1'.repeat(64), received: 1791028799000, ticketNumber: 0}
                }
            })
        }))
    };
}

async function reply(index, value, failed = false) {
    await act(async () => {
        if (failed) {
            requests[index].reject(value);
        } else {
            requests[index].resolve(value);
        }
    });
}

function advance(milliseconds) {
    time += milliseconds;
    act(() => jest.advanceTimersByTime(milliseconds));
}

beforeEach(() => {
    jest.useFakeTimers();
    requests = [];
    time = 0;
    localStorage.clear();
    jest.spyOn(performance, 'now').mockImplementation(() => time);
    jest.spyOn(axios, 'get').mockImplementation((url, options) => new Promise((resolve, reject) => {
        requests.push({url, options, resolve, reject});
    }));
    container = document.createElement('div');
    document.body.appendChild(container);
    act(() => { ReactDOM.render(<App/>, container); });
});

afterEach(() => {
    act(() => { ReactDOM.unmountComponentAtNode(container); });
    container.remove();
    jest.clearAllTimers();
    jest.restoreAllMocks();
    jest.useRealTimers();
});

it('replaces rows and summary values with an explicit empty snapshot', async () => {
    expect(container.textContent).toContain('Loading dashboard');
    await reply(0, snapshot(['alpha', 'beta']));
    expect(container.querySelectorAll('tbody tr')).toHaveLength(2);
    expect(container.textContent).toContain('Connected Nodes 1/2');
    expect(container.textContent).toContain('Tickets0');
    expect(container.textContent).not.toContain('12.99');
    advance(100);
    await reply(1, snapshot([]));
    expect(container.querySelectorAll('tbody tr')).toHaveLength(0);
    expect(container.textContent).toContain('No nodes reported.');
    expect(container.textContent).toContain('Connected Nodes 0/0');
    expect(container.textContent).not.toContain('# 42');
    expect(requests.map(request => request.url)).toEqual(['/stats-api/nodes', '/stats-api/nodes']);
});

it('removes old rows on HTTP failure, shows last observation and recovers automatically', async () => {
    await reply(0, snapshot(['alpha']));
    advance(100);
    await reply(1, new Error('HTTP 503'), true);
    expect(container.querySelectorAll('tbody tr')).toHaveLength(0);
    expect(container.textContent).toContain('Dashboard data unavailable or expired. Retrying automatically.');
    expect(container.textContent).toContain('Last snapshot: 2026-10-03T12:00:00.000Z');
    expect(container.textContent).not.toContain('# 42');
    advance(100);
    await reply(2, snapshot(['beta']));
    expect(container.textContent).toContain('beta');
    expect(container.textContent).not.toContain('alpha');
    expect(container.textContent).not.toContain('Retrying automatically');
});

it('expires visible rows while the next request is pending and cancels on unmount', async () => {
    await reply(0, snapshot(['alpha'], '120'));
    advance(100);
    advance(20);
    expect(container.querySelectorAll('tbody tr')).toHaveLength(0);
    expect(container.textContent).toContain('Dashboard data unavailable or expired');
    act(() => { ReactDOM.unmountComponentAtNode(container); });
    expect(requests[1].options.cancelToken.reason).toBeDefined();
    await reply(1, snapshot(['late']));
    advance(10000);
    expect(container.textContent).toBe('');
    expect(requests).toHaveLength(2);
});

it('retries a timed-out initial request and rejects malformed successful JSON', async () => {
    advance(50);
    expect(requests[0].options.cancelToken.reason).toBeDefined();
    expect(container.textContent).toContain('Dashboard data unavailable or expired');
    advance(100);
    await reply(1, {status: 200, headers: {}, data: []});
    expect(container.textContent).toContain('Dashboard data unavailable or expired');
    advance(100);
    await reply(2, snapshot(['recovered']));
    expect(container.textContent).toContain('recovered');
});

it('requires a fresh request after returning to a visible tab', async () => {
    await reply(0, snapshot(['alpha']));
    Object.defineProperty(document, 'visibilityState', {configurable: true, value: 'visible'});
    act(() => { document.dispatchEvent(new Event('visibilitychange')); });
    expect(container.querySelectorAll('tbody tr')).toHaveLength(0);
    expect(requests).toHaveLength(2);
    await reply(1, snapshot(['beta']));
    expect(container.textContent).toContain('beta');
    delete document.visibilityState;
});
