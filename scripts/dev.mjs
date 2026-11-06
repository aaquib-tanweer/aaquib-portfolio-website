import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {resolve, extname, sep} from 'node:path';
import {Liquid} from 'liquidjs';

const root = resolve(import.meta.dirname, '..');
const liquid = new Liquid();
liquid.registerFilter('relative_url', value => value);
const types = {'.html':'text/html', '.json':'application/json', '.js':'text/javascript', '.css':'text/css', '.jpeg':'image/jpeg', '.png':'image/png', '.ttf':'font/ttf'};
const server = createServer(async (req, res) => {
  try {
    const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    const file = resolve(root, '.' + (pathname === '/' ? '/index.html' : pathname));
    const relative = file.slice(root.length + 1);
    if (!file.startsWith(root + sep) || relative.split(sep).some(part => part.startsWith('.') || ['node_modules', '_data', 'scripts', 'tests', '_legacy'].includes(part))) {
      res.writeHead(404).end('Not found'); return;
    }
    let body;
    if (pathname === '/content.json') {
      body = await readFile(resolve(root, '_data/portfolio.json'));
    } else {
      body = await readFile(file);
      if (extname(file) === '.html') {
        const portfolio = JSON.parse(await readFile(resolve(root, '_data/portfolio.json'), 'utf8'));
        body = await liquid.parseAndRender(body.toString().replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n/, ''), {site: {data: {portfolio}, time: new Date()}});
      }
    }
    res.writeHead(200, {'Content-Type': types[extname(file)] || 'application/octet-stream', 'Cache-Control':'no-store'}).end(body);
  } catch (error) {
    res.writeHead(error.code === 'ENOENT' ? 404 : 500).end(error.code === 'ENOENT' ? 'Not found' : 'Unable to render portfolio');
    if (error.code !== 'ENOENT') console.error(error);
  }
});
server.on('error', error => { console.error(`Preview failed: ${error.message}`); process.exitCode = 1; });
server.listen(Number(process.env.PORT || 3000), '127.0.0.1', () => console.log(`Portfolio: http://127.0.0.1:${server.address().port}`));
