from pathlib import Path
import base64
import hashlib
import json


def rlp(value):
    if isinstance(value, int):
        return rlp(value.to_bytes((value.bit_length()+7)//8, 'big'))
    if isinstance(value, list):
        body = b''.join(rlp(x) for x in value)
        return prefix(len(body), 0xc0) + body
    if len(value) == 1 and value[0] < 0x80:
        return value
    return prefix(len(value), 0x80) + value


def prefix(length, offset):
    if length < 56:
        return bytes([offset + length])
    encoded = length.to_bytes((length.bit_length()+7)//8, 'big')
    return bytes([offset + 55 + len(encoded)]) + encoded


def create(directory):
    directory.mkdir()
    payloads = directory / 'payloads'
    payloads.mkdir()
    values = {'empty': b''}
    sizes = [1, 2, 255, 256, 257, 258, 259, 16383, 16384, 16385, 32767, 32768, 32769, 65534, 65535, 65536, 65537, 131072]
    stream = b''.join(hashlib.sha256(i.to_bytes(8, 'big')).digest() for i in range(4096))
    pattern = b'Fusion ticket encoding: owner/id/height/start/expiry;'
    for size in sizes:
        values['zeros-'+str(size)] = bytes(size)
        values['structured-'+str(size)] = (pattern*((size+len(pattern)-1)//len(pattern)))[:size]
        values['counter-'+str(size)] = stream[:size]
    for name, value in values.items():
        (payloads / (name + '.bin')).write_bytes(value)
    (payloads / 'index.json').write_text(json.dumps(list(values), indent=2) + '\n', encoding='utf-8')
    a, b = bytes.fromhex('11'*20), bytes.fromhex('22'*20)
    tickets = {i: [bytes([i])*32, 1, 0, expiry] for i, expiry in [(1,100), (2,101), (3,200)]}
    inventory = [[a, [tickets[1], tickets[2]]], [b, [tickets[3]]]]
    cases = [(99,[1,2,3],False), (100,[2,3],False), (101,[3],False), (199,[3],False), (200,[1,2,3],True), (201,[1,2,3],True)]
    vectors = []
    for timestamp, ids, error in cases:
        survivors = [[owner, [t for t in rows if t[0][0] in ids]] for owner, rows in inventory]
        survivors = [[owner, rows] for owner, rows in survivors if rows]
        vectors.append({'Name': 'expiry-'+str(timestamp), 'Timestamp': timestamp, 'Input': base64.b64encode(rlp(inventory)).decode('ascii'), 'Expected': base64.b64encode(rlp(survivors)).decode('ascii'), 'ExpectedIDs': ids, 'ExpectedError': 'UpdateTickets: Next block have no ticket, wait buy ticket.' if error else ''})
    (directory / 'expiry.json').write_text(json.dumps(vectors, indent=2) + '\n', encoding='utf-8')
