const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
test('workspace script parses',()=>{new vm.Script(fs.readFileSync('app/workspace.js','utf8'))});
test('atlas navigation and dependency tree script parses',()=>{new vm.Script(fs.readFileSync('app/radar-atlas.js','utf8'))});
test('market refresh and scenario script parses',()=>{new vm.Script(fs.readFileSync('app/radar-markets.js','utf8'))});
test('directory has unique company IDs',()=>{const cs=JSON.parse(fs.readFileSync('data/company-directory.json','utf8'));assert.ok(cs.length>0);assert.equal(new Set(cs.map(c=>c.id)).size,cs.length);cs.forEach(c=>assert.ok(c.name&&c.sector))});
test('original analytics retained alongside workbench',()=>{const html=fs.readFileSync('index.html','utf8');assert.ok(html.includes('app/radar-workbench.js'));for(const id of ['companies','deepdive','models','scenarios','commodities','cockpit','calendar','cycles','methodology'])assert.ok(html.includes('id="tab-'+id+'"'));for(const match of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g))new vm.Script(match[1]);new vm.Script(fs.readFileSync('app/radar-workbench.js','utf8'))});
