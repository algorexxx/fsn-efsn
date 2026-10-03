const path = require('node:path');
const pg = require(path.join(process.cwd(), 'node_modules/pg'));
const version = require(path.join(process.cwd(), 'node_modules/pg/package.json')).version;
const client = new pg.Client({
    host: '127.0.0.1', port: Number(process.env.TEST_PG_PORT),
    user: 'dashboard_test_admin', database: 'postgres',
    password: process.env.TEST_PG_PASSWORD, connectionTimeoutMillis: 1500,
});

(async () => {
    try {
        await client.connect();
        const result = await client.query('SELECT 42::integer AS value');
        console.log(JSON.stringify({ node: process.version, pg: version, connected: true, rows: result.rows }));
    } catch (error) {
        console.log(JSON.stringify({ node: process.version, pg: version, connected: false, error: error.message }));
        process.exitCode = 1;
    } finally {
        await client.end();
    }
})();
