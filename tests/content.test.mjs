import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
class Node {
  children = []; textContent = '';
  setAttribute() {}
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children = nodes; }
}
test('public content refreshes code edits and project removals without a cached request', async () => {
  const nodes = new Map(); const calls = [];
  let data = {expertise:[{title:'Backend Development',technologies:'TypeScript · Node.js',description:'Build services'}],bio:'New owner bio',headline:'New headline',skills:'Rust',education:'Student',projects:[{title:'Weather App',preview:'Live weather',url:'https://example.com'}],posts:[{title:'First post',date:'2026-10-20',body:'Published text'}]};
  const context = vm.createContext({URL,Date,location:{href:'https://example.com/'},window:{addEventListener(){}},document:{body:{dataset:{contentUrl:'/content.json'}},addEventListener(){},createElement:()=>new Node(),querySelector(selector){if(!nodes.has(selector)) nodes.set(selector,new Node());return nodes.get(selector);}},fetch:async(url,options)=>{calls.push({url,options});return {ok:true,json:async()=>data};}});
  vm.runInContext(readFileSync('content.js','utf8'),context);
  await vm.runInContext('loadPortfolio()',context);
  assert.equal(nodes.get('#portfolio-bio').textContent,'New owner bio');
  assert.equal(nodes.get('#profile-expertise').children[0].children[1].textContent,'Backend Development');
  assert.equal(nodes.get('#project-list').children[0].children[0].children[0].textContent,'Weather App');
  assert.equal(nodes.get('#project-list').children[0].children[0].children[0].href,'https://example.com');
  assert.equal(calls[0].options.cache,'no-store');
  assert.ok(new URL(calls[0].url).searchParams.has('v'));
  data = {...data,bio:'Edited again',projects:[],posts:[]};
  await vm.runInContext('loadPortfolio()',context);
  assert.equal(nodes.get('#portfolio-bio').textContent,'Edited again');
  assert.equal(nodes.get('#project-count').textContent,'[0]');
});
