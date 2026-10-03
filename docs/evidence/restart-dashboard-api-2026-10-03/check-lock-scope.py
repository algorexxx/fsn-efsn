import json
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'


def flatten(dependencies, prefix=''):
    result = {}
    for name, item in dependencies.items():
        key = prefix + 'node_modules/' + name
        result[key] = item
        result.update(flatten(item.get('dependencies', {}), key + '/'))
    return result


def closure(entries):
    remaining = ['node_modules/express']
    seen = set()
    while remaining:
        path = remaining.pop()
        if path in seen:
            continue
        seen.add(path)
        for name in entries[path].get('requires', {}):
            parent = path
            candidate = parent + '/node_modules/' + name
            while candidate not in entries:
                parent = parent.rsplit('/node_modules/', 1)[0] if '/node_modules/' in parent else ''
                candidate = (parent + '/' if parent else '') + 'node_modules/' + name
                assert parent or candidate in entries, (path, name)
            remaining.append(candidate)
    return seen


before = json.loads((bundle / 'inputs/package-lock.json').read_text(encoding='utf-8'))
after = json.loads((dashboard / 'package-lock.json').read_text(encoding='utf-8'))
old_closure = closure(flatten(before['dependencies']))
new_closure = closure(flatten(after['dependencies']))
changes = json.loads((bundle / 'lock-diff.json').read_text(encoding='utf-8'))['changes']
shared_removals = [row for row in changes if row['path'] not in old_closure | new_closure]
assert len(shared_removals) == 1
assert shared_removals[0]['path'] == 'node_modules/debug/node_modules/ms'
assert shared_removals[0]['before']['version'] == '0.7.1' and shared_removals[0]['after'] is None
assert before['dependencies']['websocket']['requires']['debug'] == '^2.2.0'
assert before['dependencies']['debug']['version'] == '2.2.0'
assert after['dependencies']['debug']['version'] == '2.6.9'
assert after['dependencies']['debug']['requires']['ms'] == '2.0.0'
assert after['dependencies']['ms']['version'] == '2.0.0'
record = {'changed_paths': len(changes), 'old_express_dependency_paths': sorted(old_closure), 'new_express_dependency_paths': sorted(new_closure), 'shared_dependency_removals': shared_removals, 'shared_dependency_reason': 'websocket accepts debug ^2.2.0; Express pins 2.6.9, so npm shares debug 2.6.9 and removes its former private ms 0.7.1', 'all_changes_accounted_for': True, 'new_paths': sum(row['before'] is None for row in changes), 'removed_paths': sum(row['after'] is None for row in changes), 'updated_paths': sum(row['before'] is not None and row['after'] is not None for row in changes)}
(bundle / 'lock-scope.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({name: value for name, value in record.items() if not isinstance(value, list)}))
