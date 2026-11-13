#!/usr/bin/env python3
"""
Rebuilds the Commodity map tab in index.html.

Replaces:
  - the hand-placed 33-node mind map (MMPOS), which cannot scale to 97
    commodities and became unreadable spaghetti when it tried
  - the thin commodity detail panel (name, three ratings, two pill rows)

With:
  - a family-grouped periodic table, laid out automatically from the reference
    data, colourable by hedgeability / supply concentration / import dependence
  - a full fact sheet per commodity built from data/commodities.json:
    hedgeability verdict, how-it-trades terms, producer / use / importer shares,
    price drivers, key stats, and the existing dependency and exposure links
  - a local neighbourhood graph (inputs -> commodity -> consumers) in place of
    the global spaghetti map, which is readable at any universe size

The reference file is fetched same-origin. If it is unavailable the tab
degrades to the embedded scoring data - the risk models never depend on it.
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "index.html")

CSS = """
.ptbl{display:flex;flex-wrap:wrap;gap:4px;margin:6px 0 2px}
.ptile{width:64px;height:52px;border:none;border-radius:8px;background:var(--card2);color:var(--ink);
  cursor:pointer;padding:4px 3px;display:flex;flex-direction:column;align-items:center;justify-content:center;
  line-height:1.1;transition:transform .12s,box-shadow .12s;border-left:3px solid transparent}
.ptile:hover{transform:translateY(-2px);box-shadow:0 6px 18px -8px rgba(16,16,19,.35)}
.ptile.on{outline:2px solid var(--accent);outline-offset:1px}
.ptile b{font-size:13px;font-weight:600;font-family:'Spline Sans Mono',monospace}
.ptile span{font-size:8.5px;color:var(--ink3);text-align:center;overflow:hidden;max-height:20px;margin-top:2px}
.pfam{display:flex;align-items:baseline;gap:8px;margin:14px 0 2px}
.pfam h4{margin:0;font-size:12px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;color:var(--ink2)}
.pfam .n{font-size:11px;color:var(--ink3)}
.hbar{display:flex;height:20px;border-radius:5px;overflow:hidden;margin:4px 0 2px;max-width:520px}
.hbar span{display:block}
.sbar{display:flex;align-items:center;gap:8px;font-size:12px;margin:2px 0}
.sbar i{display:block;height:9px;border-radius:3px;background:var(--accent);opacity:.75;flex:none}
.sbar em{font-style:normal;color:var(--ink3);width:44px;text-align:right;font-family:'Spline Sans Mono',monospace}
.sbar u{text-decoration:none;flex:1;color:var(--ink2)}
.hedgecard{border-radius:10px;padding:12px 14px;margin:10px 0}
.tt{width:100%;border-collapse:collapse;font-size:12.5px}
.tt td{padding:5px 8px;border-top:1px solid var(--line);vertical-align:top}
.tt td:first-child{color:var(--ink3);white-space:nowrap;width:130px}
"""

MARKUP = """<div id="tab-commodities" style="display:none">
  <h2>Commodity map — 97 markets, 10 families</h2>
  <p class="sub" style="margin-bottom:10px">Every market an Indian corporate cost base touches, broken down the way a commodity handbook does it — what it is, who supplies it, how it trades — plus the layer a handbook leaves out: <b>whether an Indian client can hedge it at all</b>, on which venue, in which currency, and what basis they inherit if they try. Tap any tile for the full profile.</p>
  <div class="card">
    <div style="display:flex;gap:14px;align-items:center;flex-wrap:wrap;font-size:12.5px;margin-bottom:2px">
      <span class="lbl" style="margin:0">Colour tiles by</span>
      <label style="cursor:pointer"><input type="radio" name="ptmode" value="hedge" checked onchange="ptMode(this.value)"> hedgeability</label>
      <label style="cursor:pointer"><input type="radio" name="ptmode" value="conc" onchange="ptMode(this.value)"> supply concentration</label>
      <label style="cursor:pointer"><input type="radio" name="ptmode" value="dep" onchange="ptMode(this.value)"> India import dependence</label>
      <label style="cursor:pointer"><input type="radio" name="ptmode" value="exp" onchange="ptMode(this.value)"> exposed companies</label>
      <span style="flex:1"></span>
      <input type="search" id="pq" placeholder="Filter — copper, jet fuel, urea…" style="padding:6px 10px;border:none;border-radius:8px;background:var(--card2);color:var(--ink);font-size:12.5px;min-width:180px">
    </div>
    <div id="ptlegend" class="meta" style="margin:4px 0 0"></div>
    <div id="ptable"></div>
  </div>
  <div class="card" id="comdetail"></div>
  <h2 style="margin-top:22px">Deep-tier supply chain — sector pilot</h2>
  <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin:0 0 10px">
    <select id="sankeysel" style="min-width:260px;padding:8px 12px;border:none;border-radius:10px;background:var(--card);color:var(--ink);font-size:13.5px">
      <option value="chips">Semiconductors — machines that make the machines</option>
      <option value="steel">Steel — ore &amp; coking coal to construction</option>
      <option value="energy">Oil &amp; gas — crude sources to end demand</option>
      <option value="pharma">Pharma — China KSMs to global generics</option>
      <option value="battery">EV &amp; battery — mines to vehicles</option>
      <option value="gold">Gold &amp; jewellery — mines to weddings</option>
    </select>
    <span class="lab">six sectors · same template</span>
  </div>
  <div class="card" id="sankeybox" style="overflow-x:auto"></div>
  <div class="card" id="corrbox" style="overflow-x:auto"></div>
</div>"""

JS = r"""
// ---- Commodity reference sheet -------------------------------------------
// Structure follows the Commodities 101 fact-sheet breakdown (family, symbol,
// how-it-trades, producers / consumers / importers, uses, price drivers, key
// stats) with the India hedgeability layer added. Fetched same-origin; the
// scoring array above is embedded so the models never depend on this file.
let CREF = null, CFAM = null, CHEDGE = null;
const PT = { mode: 'hedge', sel: null, q: '' };

const HEDGE_LABEL = ['no financial hedge', 'OTC / index only', 'proxy hedge only', 'offshore USD only', 'onshore INR contract'];
const HEDGE_COL   = ['var(--red)', '#B4541F', 'var(--amber)', 'var(--accent)', 'var(--teal)'];

fetch('./data/commodities.json', { cache: 'no-store' })
  .then(r => r.ok ? r.json() : Promise.reject(r.status))
  .then(d => { CREF = d.commodities; CFAM = d.families; CHEDGE = d._meta.hedgeScale;
               renderPeriodic(); if (PT.sel) showCom(PT.sel); })
  .catch(() => { const e = document.getElementById('ptlegend');
                 if (e) e.innerHTML = '<span class="chip sev3">reference sheet unavailable</span> Showing embedded scoring data only — trading terms and hedgeability need data/commodities.json.'; });

function ptCol(k) {
  const m = DATA.commodities[k], r = CREF && CREF[k];
  if (PT.mode === 'hedge') return r ? HEDGE_COL[r.ind.hedge] : 'var(--ink3)';
  if (PT.mode === 'conc') return m[2] >= 5 ? 'var(--red)' : m[2] >= 4 ? '#B4541F' : m[2] >= 3 ? 'var(--amber)' : 'var(--teal)';
  if (PT.mode === 'dep') return m[3] >= 85 ? 'var(--red)' : m[3] >= 50 ? 'var(--amber)' : m[3] > 0 ? 'var(--accent)' : 'var(--teal)';
  const n = comUsers(k).length;
  return n >= 12 ? 'var(--red)' : n >= 5 ? 'var(--amber)' : n >= 1 ? 'var(--accent)' : 'var(--ink3)';
}
function ptLegend() {
  const sw = (c, t) => `<span style="display:inline-flex;align-items:center;gap:5px;margin-right:12px"><i style="width:9px;height:9px;border-radius:2px;background:${c};display:inline-block"></i>${t}</span>`;
  if (PT.mode === 'hedge') return HEDGE_COL.map((c, i) => sw(c, i + ' — ' + HEDGE_LABEL[i])).reverse().join('') +
    '<br>Hedgeability is the question a treasurer actually asks: is there an instrument, is it onshore, and what currency leg comes with it.';
  if (PT.mode === 'conc') return sw('var(--red)', '5 chokepoint') + sw('#B4541F', '4') + sw('var(--amber)', '3') + sw('var(--teal)', '1–2 fragmented') +
    '<br>Computed from producer shares (Herfindahl band), with documented overrides where world shares misstate India’s sourcing.';
  if (PT.mode === 'dep') return sw('var(--red)', '85%+ imported') + sw('var(--amber)', '50–84%') + sw('var(--accent)', '1–49%') + sw('var(--teal)', 'domestic');
  return sw('var(--red)', '12+ companies exposed') + sw('var(--amber)', '5–11') + sw('var(--accent)', '1–4') + sw('var(--ink3)', 'none in universe');
}
function comUsers(k) { return DATA.companies.filter(c => (DATA.deps[c.id] || {})[k] != null); }

function renderPeriodic() {
  const box = document.getElementById('ptable'); if (!box) return;
  document.getElementById('ptlegend').innerHTML = ptLegend();
  const fams = CFAM || { _: { n: 'All commodities' } };
  const q = PT.q.toLowerCase();
  let h = '';
  for (const fk in fams) {
    const ids = Object.keys(DATA.commodities).filter(k => {
      const r = CREF && CREF[k];
      if (CFAM && (!r || r.fam !== fk)) return false;
      if (!q) return true;
      return (DATA.commodities[k][0] + ' ' + (r ? r.sym + ' ' + r.hook : '')).toLowerCase().includes(q);
    }).sort((a, b) => DATA.commodities[a][0].localeCompare(DATA.commodities[b][0]));
    if (!ids.length) continue;
    h += `<div class="pfam"><h4>${fams[fk].n}</h4><span class="n">${ids.length}</span></div><div class="ptbl">`;
    h += ids.map(k => {
      const m = DATA.commodities[k], r = CREF && CREF[k];
      const tip = r ? `${m[0]} · ${r.trade.venue} · hedge ${r.ind.hedge}/4 — ${HEDGE_LABEL[r.ind.hedge]}` : m[0];
      return `<button class="ptile${PT.sel === k ? ' on' : ''}" data-com="${k}" title="${esc(tip)}" style="border-left-color:${ptCol(k)}"><b>${r ? esc(r.sym) : m[0].slice(0, 3)}</b><span>${esc(m[0])}</span></button>`;
    }).join('') + '</div>';
  }
  box.innerHTML = h || '<p class="meta">No commodity matches that filter.</p>';
}
window.ptMode = v => { PT.mode = v; renderPeriodic(); };
function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }

function shareBars(rows, cap) {
  if (!rows || !rows.length) return '';
  const mx = Math.max(...rows.map(r => r[1])) || 1;
  return `<div class="lbl">${cap}</div>` + rows.map(r =>
    `<div class="sbar"><i style="width:${(r[1] / mx * 120).toFixed(0)}px"></i><em>${r[1]}%</em><u>${esc(r[0])}</u></div>`).join('');
}

function showCom(k) {
  PT.sel = k;
  const m = DATA.commodities[k], r = CREF && CREF[k], box = document.getElementById('comdetail');
  const pill = (id, label) => `<span class="pill" data-com="${id}" style="cursor:pointer">${label}</span>`;
  const made = (m[4] || []).map(i => pill(i, DATA.commodities[i][0])).join(' ');
  const feeds = (CONS[k] || []).map(i => pill(i, DATA.commodities[i][0])).join(' ');
  const users = DATA.companies.filter(c => closureOf(c.id).has(k)).map(c => {
    const w = (DATA.deps[c.id] || {})[k];
    return `<span class="pill" data-dd="${c.id}" style="cursor:pointer">${c.name}${w ? ' · ' + Math.round(w * 100) + '%' : ' · indirect'}</span>`;
  }).join(' ');
  const row = (l, v) => v ? `<div class="lbl">${l}</div><div style="display:flex;flex-wrap:wrap;gap:6px">${v}</div>` : '';

  let h = '';
  if (r) {
    const fam = CFAM[r.fam];
    h += `<div style="display:flex;align-items:baseline;gap:10px;flex-wrap:wrap">
      <span style="font-family:'Spline Sans Mono',monospace;font-size:22px;font-weight:600">${esc(r.sym)}</span>
      <span style="font-size:19px;font-weight:600">${esc(r.n)}</span>
      <span class="badge" style="background:var(--card2);color:var(--ink2)">${esc(fam.n)}</span>
      <span class="badge" style="background:transparent;border:1px solid var(--line);color:var(--ink3)">${esc(r.trade.venue)}</span>
      ${r.tier === 'A' ? '' : '<span class="badge" style="background:transparent;border:1px solid var(--line);color:var(--ink3)">map entry — structural facts only</span>'}
    </div>
    <p style="font-size:14.5px;color:var(--ink2);margin:8px 0 4px">${esc(r.hook)}</p>`;

    const hc = HEDGE_COL[r.ind.hedge];
    h += `<div class="hedgecard" style="background:var(--card2);border-left:4px solid ${hc}">
      <div style="display:flex;align-items:baseline;gap:10px;flex-wrap:wrap">
        <span class="lbl" style="margin:0">Can an Indian client hedge this?</span>
        <b style="color:${hc};font-size:14px">${r.ind.hedge} / 4 — ${HEDGE_LABEL[r.ind.hedge]}</b>
      </div>
      <p style="font-size:12.5px;color:var(--ink3);margin:6px 0 4px">${esc(CHEDGE[String(r.ind.hedge)])}</p>
      <div class="lbl" style="margin:10px 0 2px">Indian contract</div>
      <div style="font-size:13px">${esc(r.ind.contract)}</div>
      <div class="lbl" style="margin:10px 0 2px">Basis a hedger inherits</div>
      <div style="font-size:13.5px;color:var(--ink2)">${esc(r.ind.basis)}</div>
      ${r.ind.note ? `<div class="lbl" style="margin:10px 0 2px">Who carries it</div><div style="font-size:13px;color:var(--ink2)">${esc(r.ind.note)}</div>` : ''}
    </div>`;

    h += `<div class="mrow"><span>Price volatility<br><b>${m[1]} / 5</b></span>
      <span>Supply concentration<br><b>${m[2]} / 5</b></span>
      <span>India import dependence<br><b>${m[3]}%</b></span>
      <span>Companies exposed<br><b>${comUsers(k).length} direct</b></span></div>
    <p class="meta" style="margin:-4px 0 8px">Concentration: ${esc(r.concWhy)}${r.concCalc != null && r.concCalc !== m[2] ? ` (Herfindahl band alone would give ${r.concCalc}).` : '.'}</p>`;

    const t = r.trade;
    h += `<div class="lbl">How it trades</div><table class="tt">
      <tr><td>Venue</td><td>${esc(t.venue)}</td></tr>
      <tr><td>Benchmark</td><td>${esc(t.bench)}</td></tr>
      <tr><td>Contract size</td><td>${esc(t.lot)}</td></tr>
      <tr><td>Price terms</td><td>${esc(t.terms)}</td></tr>
      <tr><td>Settlement</td><td>${esc(t.settle)}</td></tr>
      <tr><td>Typical curve</td><td>${esc(t.curve)}</td></tr>
      <tr><td>Liquidity</td><td>${esc(t.liq)}</td></tr></table>`;

    h += `<div style="display:flex;gap:26px;flex-wrap:wrap;margin-top:4px">
      <div style="flex:1;min-width:230px">${shareBars(r.prod, 'Top producers')}</div>
      <div style="flex:1;min-width:230px">${shareBars(r.use, 'Main uses')}</div>
      <div style="flex:1;min-width:230px">${shareBars(r.imp, 'Top importers')}</div></div>`;

    h += `<div class="lbl">What moves the price</div><ul style="font-size:13.5px;margin:4px 0;color:var(--ink2)">` +
      r.drv.map(d => `<li>${esc(d)}</li>`).join('') + `</ul>`;

    if (r.stats && r.stats.length) h += `<div class="lbl">Key stats</div><table class="tt">` +
      r.stats.map(s => `<tr><td>${esc(s[0])}</td><td><b>${esc(s[1])}</b> <span class="meta">${esc(s[2])}</span></td></tr>`).join('') + `</table>`;
  } else {
    h += `<div style="font-size:17px;font-weight:600">${esc(m[0])}</div>
      <div class="mrow"><span>Price volatility<br><b>${m[1]} / 5</b></span><span>Supply concentration<br><b>${m[2]} / 5</b></span><span>India import dependence<br><b>${m[3]}%</b></span></div>`;
  }

  h += `<div style="font-size:13px;color:var(--ink3);margin:8px 0 0">Supply origin: ${esc(m[5])}</div>`;
  h += row('Made from', made) + row('Feeds into', feeds) + row('Used by (direct % of cost base, or indirect via the chain)', users);
  if (r) h += `<p class="meta" style="margin:12px 0 0;border-top:1px solid var(--line);padding-top:8px">Sources: ${esc(r.src)}. Shares are indicative and dated — verify against the primary source before client-facing use.</p>`;
  box.innerHTML = h;
  renderPeriodic();
  box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}
"""


def main():
    src = open(HTML, encoding="utf-8").read()

    # 1. markup
    m = re.search(r'<div id="tab-commodities" style="display:none">.*?\n</div>\n', src, re.S)
    assert m, "commodity tab markup not found"
    src = src[:m.start()] + MARKUP + "\n\n" + src[m.end():]

    # 2. css
    src = src.replace(".mrow{display:flex", CSS.strip() + "\n.mrow{display:flex", 1)

    # 3. drop the fixed mind-map layout + renderer + the old grid/detail renderers
    for pat, what in [
        (r'const MMPOS = \{.*?\n\};\n', "MMPOS"),
        (r'const MMCORR = \[.*?\n\];\n', "MMCORR"),
        (r'const MMHUBS = \[.*?\n\];\n', "MMHUBS"),
        (r'function renderMindMap\(\) \{.*?\n\}\n', "renderMindMap"),
        (r'function renderComGrid\(\) \{.*?\n\}\n', "renderComGrid"),
        (r'function showCom\(k\) \{.*?\n\}\n', "showCom"),
    ]:
        m = re.search(pat, src, re.S)
        assert m, f"{what} block not found"
        src = src[:m.start()] + src[m.end():]

    # 4. inject the new renderer just before the chainHTML helper
    src = src.replace("function chainHTML(k, depth, w) {", JS.strip() + "\n\nfunction chainHTML(k, depth, w) {", 1)

    # 5. rewire remaining references
    src = re.sub(r'MM\.sel = ([^;]+); renderMindMap\(\); showCom\(', r'showCom(', src)
    src = re.sub(r'MM\.sel = (?:MM\.sel === )?[^;]+; renderMindMap\(\); showCom\(', r'showCom(', src)
    src = src.replace("renderComGrid();", "renderPeriodic();")
    src = re.sub(r'^\s*renderMindMap\(\);\s*$', "  renderPeriodic();", src, flags=re.M)
    src = src.replace("renderMindMap();", "renderPeriodic();")

    open(HTML, "w", encoding="utf-8").write(src)
    leftovers = sorted(set(re.findall(r'\b(MM|MMPOS|MMCORR|MMHUBS|renderMindMap|renderComGrid)\b[.\(]?', src)))
    print("patched commodity tab; remaining references to old map:", leftovers or "none")


if __name__ == "__main__":
    main()
