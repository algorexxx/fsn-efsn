import json
import re
from pathlib import Path

bundle = Path(__file__).resolve().parent
frontend = bundle.parents[2] / 'tmp/fsn-stats-auth/react-frontend'
rules = json.loads((bundle / 'cra-rules.json').read_text(encoding='utf-8'))
known = json.loads((bundle / 'oxlint-schema.json').read_text(encoding='utf-8'))['definitions']['DummyRuleMap']['properties']
aliases = {'react-hooks/exhaustive-deps': 'react/exhaustive-deps', 'react-hooks/rules-of-hooks': 'react/rules-of-hooks', 'no-new-object': 'no-object-constructor', 'no-new-symbol': 'no-new-native-nonconstructor'}
omitted = {
    'react/jsx-uses-vars': 'Oxlint no-unused-vars accounts for JSX references without this ESLint bookkeeping rule.',
    'react/jsx-uses-react': 'Oxlint no-unused-vars accounts for the classic React JSX runtime.',
    'dot-location': 'Formatting-only rule not implemented by Oxlint; no formatter introduced in this migration.',
    'new-parens': 'Formatting-only rule not implemented by Oxlint.',
    'no-dupe-args': 'Strict/module parser rejects duplicate parameters.',
    'no-mixed-operators': 'Parenthesization style check not implemented by Oxlint; existing expressions unchanged.',
    'no-octal': 'Strict/module parser rejects legacy octal literals.',
    'no-octal-escape': 'Strict/module parser rejects octal escapes.',
    'no-restricted-syntax': 'CRA restricts only WithStatement, rejected by the strict/module parser.',
    'no-whitespace-before-property': 'Formatting-only rule not implemented by Oxlint.',
    'rest-spread-spacing': 'Formatting-only rule not implemented by Oxlint.',
    'strict': 'Module parsing already uses strict semantics; redundant-directive style check omitted.',
    'react/forbid-foreign-prop-types': 'No direct replacement; retain as a documented lint coverage limitation.',
    'react/no-typos': 'No direct replacement; retain as a documented lint coverage limitation.',
    'flowtype/define-flow-type': 'No Flow source remains after removing the orphan localization annotation.',
    'flowtype/require-valid-file-annotation': 'No Flow source remains.',
    'flowtype/use-flow-type': 'No Flow source remains.',
}
translated = {}
for name, value in rules.items():
    target = aliases.get(name, name)
    if target in known:
        translated[target] = value
    else:
        assert name in omitted, name
record = {'before': len(rules), 'retained': len(translated), 'renamed': aliases, 'omitted': omitted}
(bundle / 'lint-migration.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
config = {'$schema': './node_modules/oxlint/configuration_schema.json', 'plugins': ['react', 'jsx-a11y', 'import'], 'categories': {'correctness': 'off'}, 'env': {'browser': True, 'commonjs': True, 'es6': True, 'jest': True, 'node': True}, 'settings': {'react': {'version': '16.10.2'}}, 'rules': translated}
(frontend / '.oxlintrc.json').write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8')
(frontend / 'rsbuild.config.mjs').write_text('''import {defineConfig, loadEnv} from '@rsbuild/core';
import {pluginReact} from '@rsbuild/plugin-react';
import loadApiPath from './src/config.js';

const {publicVars} = loadEnv({prefixes: ['REACT_APP_']});
loadApiPath(process.env.REACT_APP_STATS_API_PATH);
loadApiPath.loadPollingConfig(process.env.REACT_APP_STATS_POLL_INTERVAL_MS, process.env.REACT_APP_STATS_REQUEST_TIMEOUT_MS);

export default defineConfig({
    plugins: [pluginReact({swcReactOptions: {runtime: 'classic'}})],
    source: {define: {...publicVars, 'process.env.PUBLIC_URL': JSON.stringify('')}},
    html: {template: './public/index.html'},
    output: {distPath: {root: process.env.BUILD_PATH || 'build'}, sourceMap: true}
});
''', encoding='utf-8')
(frontend / 'jest.config.cjs').write_text('''module.exports = {
    testEnvironment: 'jsdom',
    roots: ['<rootDir>/src'],
    transform: {'^.+\\\\.[jt]sx?$': ['@swc/jest', {jsc: {parser: {syntax: 'ecmascript', jsx: true}, transform: {react: {runtime: 'classic'}}}}]},
    moduleNameMapper: {
        '\\\\.css$': '<rootDir>/test/style-mock.cjs',
        '\\\\.(png|jpe?g|gif|svg|ico)$': '<rootDir>/test/file-mock.cjs'
    }
};
''', encoding='utf-8')
(frontend / 'test').mkdir(exist_ok=True)
(frontend / 'test/style-mock.cjs').write_text('module.exports = {};\n', encoding='utf-8')
(frontend / 'test/file-mock.cjs').write_text("module.exports = 'test-file';\n", encoding='utf-8')
html = frontend / 'public/index.html'
value = html.read_text(encoding='utf-8').replace('%PUBLIC_URL%', '<%= assetPrefix %>')
value = re.sub(r'    <!--[\s\S]*?-->\n', '', value)
html.write_text(value, encoding='utf-8', newline='\n')
localization = frontend / 'src/Components/timeAgo/customStrings.js'
value = localization.read_bytes()
start = value.index(b'const strings: L10nsStrings = {')
value = value[start:].replace(b'const strings: L10nsStrings = {', b'const strings = {', 1)
localization.write_bytes(value)
notice = frontend / 'LINT-LICENSE.txt'
notice.write_bytes((bundle / 'inputs/cra-eslint-LICENSE').read_bytes())
print(json.dumps(record, indent=2))
