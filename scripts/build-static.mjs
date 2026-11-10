import {cp, mkdir, readFile, rm, writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {Liquid} from 'liquidjs';

const root = resolve(import.meta.dirname, '..');
const output = resolve(root, '_site');
const liquid = new Liquid();
liquid.registerFilter('relative_url', value => value);

const portfolio = JSON.parse(await readFile(resolve(root, '_data/portfolio.json'), 'utf8'));
const template = await readFile(resolve(root, 'index.html'), 'utf8');
const html = await liquid.parseAndRender(
  template.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n/, ''),
  {site: {data: {portfolio}, time: new Date()}}
);

await rm(output, {recursive: true, force: true});
await mkdir(output, {recursive: true});
for (const file of ['assets', 'styles.css', 'app.js', 'content.js']) {
  await cp(resolve(root, file), resolve(output, file), {recursive: true});
}
await writeFile(resolve(output, 'index.html'), html);
await writeFile(resolve(output, 'content.json'), JSON.stringify(portfolio));
console.log('Static portfolio built in _site');
