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
    remaining = ['node_modules/geoip-lite', 'node_modules/color-string']
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
outside = [row for row in changes if row['path'] not in old_closure | new_closure]
assert outside == [], outside
record = {'changed_paths': len(changes), 'old_dependency_paths': sorted(old_closure), 'new_dependency_paths': sorted(new_closure), 'outside_paths': outside, 'all_changes_accounted_for': True, 'new_paths': sum(row['before'] is None for row in changes), 'removed_paths': sum(row['after'] is None for row in changes), 'updated_paths': sum(row['before'] is not None and row['after'] is not None for row in changes)}
(bundle / 'lock-scope.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({name: value for name, value in record.items() if not isinstance(value, list)}))
