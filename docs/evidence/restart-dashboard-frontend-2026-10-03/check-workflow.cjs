const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const frontend = path.resolve(__dirname, '../../../tmp/fsn-stats-auth/react-frontend');
const YAML = require(path.join(frontend, 'node_modules/yaml'));
const workflowPath = path.join(frontend, '../.github/workflows/validate.yml');
const source = fs.readFileSync(workflowPath, 'utf8');
const workflow = YAML.parse(source);
const actions = JSON.parse(fs.readFileSync(path.join(__dirname, 'actions.json'), 'utf8'));
const expectedCommands = [
    'npm install --global npm@10.9.0 --ignore-scripts --no-audit --no-fund',
    'npm ci --engine-strict --ignore-scripts --no-audit --no-fund',
    'npm test', 'npm run test:wire',
    'npm ci --engine-strict --ignore-scripts --no-audit --no-fund',
    'npm test -- --watchAll=false --runInBand', 'npm run build',
];
const job = workflow.jobs.validate;
const steps = job.steps;

assert.deepEqual(Object.keys(workflow.on), ['pull_request', 'workflow_dispatch']);
assert.deepEqual(workflow.permissions, { contents: 'read' });
assert.equal(job['runs-on'], 'ubuntu-24.04');
assert.equal(job['timeout-minutes'], 20);
assert.deepEqual(steps.filter(step => step.uses).map(step => step.uses), actions.map(action => action.repository + '@' + action.sha));
assert.deepEqual(steps[0].with, { 'persist-credentials': false });
assert.deepEqual(steps[1].with, { 'node-version': '24.21.0', 'package-manager-cache': false });
assert.deepEqual(steps.filter(step => step.run).map(step => step.run), expectedCommands);
assert.deepEqual(steps.slice(6).map(step => step['working-directory']), ['react-frontend', 'react-frontend', 'react-frontend']);
assert.equal(/AWS|s3:\/\/|secrets\.|pull_request_target|npm install$/.test(source), false);
assert.equal(fs.existsSync(path.join(frontend, '../.github/workflows/deploy.yml')), false);
fs.writeFileSync(path.join(__dirname, 'workflow-review.json'), JSON.stringify({ parsed: true, actions, commands: expectedCommands, deploymentRemoved: true, hostedRunPerformed: false }, null, 2) + '\n');
console.log('Validation workflow parses, uses pinned actions, and contains no deployment path');
