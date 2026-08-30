const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");

test("every inline script parses", () => {
  const scripts = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/gi)].map((match) => match[1]).filter((source) => source.trim());
  assert.ok(scripts.length > 0);
  scripts.forEach((source, index) => assert.doesNotThrow(() => new vm.Script(source, { filename: `index-inline-${index}.js` })));
});

test("public HTML excludes confidential and misleading legacy paths", () => {
  const blocked = ["adv:{buyer:", "breachProb30d", "First talking point", "tab-pipeline", "clientbtn", "renderPipeline()", "live breaches"];
  blocked.forEach((token) => assert.equal(html.toLowerCase().includes(token.toLowerCase()), false, token));
});

test("navigation is reduced to four workspaces", () => {
  const workspaces = [...html.matchAll(/data-workspace="([^"]+)"/g)].map((match) => match[1]);
  assert.deepEqual(workspaces, ["radar", "explore", "scenarios", "trust"]);
});

test("dialogs declare modality and core models load before the app", () => {
  assert.match(html, /id="cmdk"[^>]*aria-modal="true"/);
  assert.match(html, /id="drawer"[^>]*aria-modal="true"/);
  assert.match(html, /id="briefmodal"[^>]*aria-modal="true"/);
  assert.ok(html.indexOf('src="app/models/core.js"') < html.indexOf("const DATA ="));
});
