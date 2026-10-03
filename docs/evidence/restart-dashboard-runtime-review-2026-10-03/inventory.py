import hashlib
import json
import re
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def flatten(dependencies, prefix=''):
    result = []
    for name, value in dependencies.items():
        path = prefix + 'node_modules/' + name
        result.append({'name': name, 'version': value['version'], 'path': path, 'dev': value.get('dev', False), 'optional': value.get('optional', False)})
        result.extend(flatten(value.get('dependencies', {}), path + '/'))
    return result


result = {'locks': {}, 'browser': {}, 'source_sha256': {}, 'build_sha256': {}}
for label, directory in [('backend', dashboard), ('frontend', dashboard / 'react-frontend'), ('legacy-api', dashboard / 'api-server')]:
    package = read(directory / 'package.json')
    lock = read(directory / 'package-lock.json')
    audit = read(bundle / (label + '-audit.json'))
    entries = flatten(lock['dependencies'])
    result['locks'][label] = {'entries': entries, 'direct': [], 'audit_counts': audit['metadata']['vulnerabilities']}
    for name, constraint in package['dependencies'].items():
        installed = directory / 'node_modules' / name / 'package.json'
        advisory = audit['vulnerabilities'].get(name, {})
        result['locks'][label]['direct'].append({'name': name, 'constraint': constraint, 'locked': lock['dependencies'][name]['version'], 'installed': read(installed)['version'] if installed.exists() else None, 'severity': advisory.get('severity'), 'via': advisory.get('via', []), 'fixAvailable': advisory.get('fixAvailable')})
build = dashboard / 'react-frontend/build'
sources = set()
for path in (build / 'static/js').glob('*.map'):
    for source in read(path)['sources']:
        if 'node_modules/' in source:
            sources.add(source)
packages = {}
for source in sorted(sources):
    tail = source.rsplit('node_modules/', 1)[1]
    match = re.match(r'(@[^/]+/[^/]+|[^/]+)', tail)
    if match:
        packages.setdefault(match[1], []).append(source)
result['browser']['mapped_packages'] = packages
result['browser']['audited_packages_in_maps'] = sorted(set(packages) & set(read(bundle / 'frontend-audit.json')['vulnerabilities']))
names = subprocess.check_output(['git', '-C', str(dashboard), '-c', 'core.autocrlf=false', 'ls-files']).decode().splitlines()
result['source_sha256'] = {name: digest(dashboard / name) for name in names if not name.endswith('.md')}
result['build_sha256'] = {path.relative_to(build).as_posix(): digest(path) for path in build.rglob('*') if path.is_file()}
backend_sources = [name for name in names if name.endswith('.js') and not name.startswith(('react-frontend/', 'test/'))]
result['backend_external_imports'] = {}
for name in backend_sources:
    code = (dashboard / name).read_text(encoding='utf-8')
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.S)
    imports = sorted(set(re.findall(r'require\([\'"]([^\'"]+)[\'"]\)', code)))
    imports = [value for value in imports if not value.startswith('.')]
    if imports:
        result['backend_external_imports'][name] = imports
(bundle / 'inventory.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'locked_entries': {name: len(value['entries']) for name, value in result['locks'].items()}, 'browser_packages': len(packages), 'browser_audited_packages': result['browser']['audited_packages_in_maps'], 'backend_imports': result['backend_external_imports']}, indent=2))
