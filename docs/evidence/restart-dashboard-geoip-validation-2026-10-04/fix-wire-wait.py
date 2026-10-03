from pathlib import Path

bundle = Path(__file__).resolve().parent
file = bundle.parents[2] / 'tmp/fsn-stats-auth/test/collector-output-wire.test.cjs'
data = file.read_bytes()
replacements = {
    b'async function waitForWrites(server, port, expected)': b'async function waitForQueuedBytes(server, port, expected)',
    b'if (state.writes >= expected)': b'if (state.queued >= expected || state.destroyed)',
    b'Expected bounded fixture writes did not arrive': b'Expected bounded fixture bytes did not arrive',
    b'waitForWrites(server, port, 1)': b'waitForQueuedBytes(server, port, 129)',
    b'waitForWrites(server, port, fitting)': b'waitForQueuedBytes(server, port, fitting * first.queued)',
    b'waitForWrites(server, port, 4)': b'waitForQueuedBytes(server, port, protocol.queued + 381)',
}
assert data.count(b'waitForWrites(server, port, 1)') == 2
for old, new in replacements.items():
    assert old in data
    data = data.replace(old, new)
old = b'const protocol = await waitForQueuedBytes(server, port, 129);'
assert data.count(old) == 1
data = data.replace(old, b'const protocol = await waitForQueuedBytes(server, port, 3);')
file.write_bytes(data)
