const { Writable } = require('node:stream');
const socket = new Writable({ write(chunk, encoding, callback) { callback(); } });
socket.cork();
const results = [socket.write(Buffer.alloc(8)), socket.write(Buffer.alloc(8))];
console.log(JSON.stringify({ writes: results, writableLength: socket.writableLength, destroyed: socket.destroyed, scope: 'Two eight-byte writes to an in-memory corked stream; no network traffic.' }));
socket.uncork();
socket.end();
