const fs = require('fs');
const path = require('path');
const frontend = path.resolve(__dirname, '../../../tmp/fsn-stats-auth/react-frontend');
const config = require(path.join(frontend, 'node_modules/eslint-config-react-app'));
const rules = {'react/jsx-uses-vars': 'warn', 'react/jsx-uses-react': 'warn', ...config.rules};
fs.writeFileSync(path.join(__dirname, 'cra-rules.json'), JSON.stringify(rules, null, 2) + '\n');
const schema = JSON.parse(fs.readFileSync(path.join(__dirname, 'oxlint-schema.json'), 'utf8'));
const known = schema.definitions.DummyRuleMap.properties;
console.log(Object.keys(rules).filter(name => !known[name]));
