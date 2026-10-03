import hashlib
import json
import os
import selectors
import shutil
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
scratch = root / 'tmp/dashboard-geoip-operations-3'
runtime = root / 'tmp/dashboard-runtime-review/v24.21.0/node'
output = bundle / 'switch-1'
output.mkdir(exist_ok=False)
active = scratch / 'active-a'
candidate = scratch / 'retry-success'
selected = scratch / 'current'
record_sizes = {'geoip-country.dat': 10, 'geoip-country6.dat': 34, 'geoip-city-names.dat': 88, 'geoip-city.dat': 24, 'geoip-city6.dat': 48}


def hashes(directory):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.iterdir() if p.is_file()}


def completeness(directory):
    return {name: (directory / name).is_file() and (directory / name).stat().st_size > 0 and (directory / name).stat().st_size % size == 0 for name, size in record_sizes.items()}


def activate(directory):
    target = directory.resolve(strict=True)
    assert target.is_relative_to(scratch.resolve()) and target != scratch.resolve()
    assert all(completeness(target).values())
    temporary = scratch / 'next-link'
    assert not temporary.exists() and not temporary.is_symlink()
    temporary.symlink_to(target, target_is_directory=True)
    os.replace(temporary, selected)
    assert selected.resolve(strict=True) == target


def launch(watch=False):
    return subprocess.Popen([runtime, bundle / 'lookup.cjs'] + (['--watch'] if watch else []), env=dict(os.environ, GEODATADIR=str(selected)), stdin=subprocess.PIPE if watch else subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def read_line(child):
    with selectors.DefaultSelector() as selector:
        selector.register(child.stdout, selectors.EVENT_READ)
        assert selector.select(timeout=10), 'Lookup deadline exceeded'
    return json.loads(child.stdout.readline())


def fresh_lookup():
    child = launch()
    try:
        stdout, stderr = child.communicate(timeout=10)
        assert child.returncode == 0, stderr
        return json.loads(stdout)
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=5)


def location(value):
    return {'nodes': [None if node['geo'] is None else {key: node['geo'][key] for key in ['country', 'city', 'll']} for node in value['nodes']], 'map': [{key: point[key] for key in ['name', 'latitude', 'longitude']} for point in value['map']]}


expected_a = {'nodes': [{'country': 'SE', 'city': 'Fixture A', 'll': [59.3293, 18.0686]}] * 3 + [None], 'map': [{'name': 'fixture-0', 'latitude': 59.3293, 'longitude': 18.0686}, {'name': 'fixture-1', 'latitude': 59.3293, 'longitude': 18.0686}, {'name': 'fixture-2', 'latitude': 59.3293, 'longitude': 18.0686}]}
expected_b = {'nodes': [{'country': 'NO', 'city': 'Fixture B', 'll': [59.9139, 10.7522]}] * 3 + [None], 'map': [{'name': 'fixture-0', 'latitude': 59.9139, 'longitude': 10.7522}, {'name': 'fixture-1', 'latitude': 59.9139, 'longitude': 10.7522}, {'name': 'fixture-2', 'latitude': 59.9139, 'longitude': 10.7522}]}
before = {'active': hashes(active), 'candidate': hashes(candidate)}
activate(active)
child = launch(watch=True)
results = {}
try:
    results['initial'] = read_line(child)
    incomplete = scratch / 'incomplete-country-only'
    incomplete.mkdir()
    for name in ['geoip-country.dat', 'geoip-country6.dat']:
        shutil.copyfile(candidate / name, incomplete / name)
    rejected = completeness(incomplete)
    assert rejected == {'geoip-country.dat': True, 'geoip-country6.dat': True, 'geoip-city-names.dat': False, 'geoip-city.dat': False, 'geoip-city6.dat': False}
    probe = subprocess.run([runtime, bundle / 'lookup.cjs'], env=dict(os.environ, GEODATADIR=str(incomplete)), capture_output=True, text=True, timeout=10)
    results['incomplete_lookup'] = {'exit': probe.returncode, 'value': json.loads(probe.stdout) if probe.returncode == 0 else None, 'stderr': probe.stderr}
    assert selected.resolve() == active
    child.stdin.write('lookup\n')
    child.stdin.flush()
    results['after_rejected_candidate'] = read_line(child)
    activate(candidate)
    child.stdin.write('lookup\n')
    child.stdin.flush()
    results['running_after_switch'] = read_line(child)
    results['fresh_after_switch'] = fresh_lookup()
    activate(active)
    results['fresh_after_rollback'] = fresh_lookup()
    child.stdin.write('stop\n')
    child.stdin.flush()
    child.stdin.close()
    child.wait(timeout=10)
    results['reader_stderr'] = child.stderr.read()
finally:
    if child.poll() is None:
        child.kill()
        child.wait(timeout=5)
results['reader_stopped'] = child.poll() is not None
results['final_target'] = selected.resolve().name
results['datasets_unchanged'] = before == {'active': hashes(active), 'candidate': hashes(candidate)}
(output / 'result.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
assert location(results['initial']) == expected_a
assert location(results['after_rejected_candidate']) == expected_a
assert location(results['running_after_switch']) == expected_a
assert location(results['fresh_after_switch']) == expected_b
assert location(results['fresh_after_rollback']) == expected_a
assert child.returncode == 0 and results['reader_stderr'] == ''
assert results['reader_stopped'] and results['datasets_unchanged']
summary = {'passed': True, 'initial_and_rejected_candidate_preserved': True, 'running_reader_keeps_cached_dataset': True, 'new_reader_uses_new_dataset': True, 'rollback_reader_uses_previous_dataset': True, 'reader_stopped': True, 'datasets_unchanged': True, 'final_target': results['final_target']}
(output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary))
