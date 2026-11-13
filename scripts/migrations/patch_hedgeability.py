#!/usr/bin/env python3
"""
Adds the Hedgeability Matrix.

The reference sheet records, per commodity, whether a listed contract exists,
on which venue and in which currency. Crossed with each company's cost-base
map, that answers a question no Indian risk tool currently answers:

    of everything this client spends money on, how much can they actually
    hedge - onshore in rupees, offshore in dollars, only by proxy, or not at
    all - and what does the unhedgeable residual add up to?

Two surfaces:
  1. a per-company panel inside the deep dive
  2. a cross-universe league table in 'Who is exposed', ranked by the share of
     mapped cost base with no available instrument

Every number is derived from data already on the page - no new assumptions.
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "index.html")

JS = r"""
// ---- Hedgeability matrix --------------------------------------------------
// Crosses each company's cost-base map with the hedgeability rating in the
// commodity reference sheet. Buckets, coarsest first:
//   onshore  (4) MCX / NCDEX contract in INR - no FX leg, lightest permissions
//   offshore (3) liquid contract but USD/EUR only - RBI permission + FX leg
//   proxy    (2) correlated contract only - material basis, Ind AS 109 risk
//   contract (1) OTC swap or index-linked supply contract - no exchange
//   none     (0) no financial hedge exists at all
// Shares are of MAPPED cost base, not of revenue: they answer "of the input
// spend we can see, what is coverable", which is the question a hedge policy
// has to start from.
const HB_KEYS = ['none', 'contract', 'proxy', 'offshore', 'onshore'];
const HB_META = {
  onshore:  { l: 'Onshore INR contract', c: 'var(--teal)',   d: 'MCX or NCDEX listed. Hedge in rupees, no currency leg, lightest permission burden.' },
  offshore: { l: 'Offshore USD/EUR only', c: 'var(--accent)', d: 'Liquid contract exists but only abroad. Needs an offshore commodity derivative under the RBI Master Direction plus a currency leg — and that leg sits under the April 2026 NDF prohibition.' },
  proxy:    { l: 'Proxy hedge only',      c: 'var(--amber)',  d: 'Only a correlated contract is available. Material basis risk; Ind AS 109 effectiveness at 80–125% is hard to sustain.' },
  contract: { l: 'OTC / index-linked',    c: '#B4541F',       d: 'No exchange. Manageable through formula pricing or a bilateral swap, with counterparty credit attached.' },
  none:     { l: 'No hedge exists',       c: 'var(--red)',    d: 'No financial instrument anywhere. Contractual and operational levers only: pass-through clauses, indexation, inventory, dual sourcing.' }
};

function hedgeSplit(id) {
  if (!CREF) return null;
  const deps = DATA.deps[id] || {};
  const out = { onshore: 0, offshore: 0, proxy: 0, contract: 0, none: 0, total: 0, unknown: 0, items: [] };
  for (const k in deps) {
    const w = deps[k], r = CREF[k];
    out.total += w;
    if (!r) { out.unknown += w; continue; }
    const b = HB_KEYS[r.ind.hedge];
    out[b] += w;
    out.items.push({ k: k, n: DATA.commodities[k][0], w: w, b: b, h: r.ind.hedge, contract: r.ind.contract, basis: r.ind.basis });
  }
  out.items.sort((a, b) => (a.h - b.h) || (b.w - a.w));
  return out.total ? out : null;
}
// Share of mapped cost base with no instrument at all, or only an index-linked one.
function unhedgeableShare(id) {
  const s = hedgeSplit(id);
  return s ? (s.none + s.contract) / s.total : null;
}

function hedgeBar(s, maxw) {
  const seg = HB_KEYS.slice().reverse().filter(b => s[b] > 0).map(b =>
    `<span title="${HB_META[b].l} — ${Math.round(s[b] / s.total * 100)}% of mapped cost base" style="width:${(s[b] / s.total * 100).toFixed(1)}%;background:${HB_META[b].c}"></span>`).join('');
  return `<div class="hbar" style="max-width:${maxw || 520}px">${seg}</div>`;
}

function hedgeCard(id) {
  const s = hedgeSplit(id);
  if (!s) return CREF ? '' : '<p class="meta">Hedgeability needs the commodity reference sheet (data/commodities.json).</p>';
  const pct = b => Math.round(s[b] / s.total * 100);
  const cov = pct('onshore') + pct('offshore');
  const stuck = pct('none') + pct('contract');
  let h = `<div class="lbl">Hedgeability of the cost base</div>
    <p class="kcap" style="margin:0 0 6px">Of the ${Math.round(s.total * 100)}% of the cost base mapped here, this is how much has an instrument behind it. Read it as the opening page of a hedge policy: what can be covered, what needs an offshore permission and a currency leg, and what has to be managed by contract because no market exists.</p>
    ${hedgeBar(s)}
    <div style="display:flex;flex-wrap:wrap;gap:14px;font-size:12px;margin:6px 0 10px">` +
    HB_KEYS.slice().reverse().filter(b => s[b] > 0).map(b =>
      `<span style="display:inline-flex;align-items:center;gap:5px"><i style="width:9px;height:9px;border-radius:2px;background:${HB_META[b].c};display:inline-block"></i>${HB_META[b].l} <b>${pct(b)}%</b></span>`).join('') +
    `</div>
    <div class="mrow" style="margin-top:0"><span>Coverable with a listed contract<br><b>${cov}% of mapped cost base</b></span>
      <span>Needs an offshore permission and an FX leg<br><b>${pct('offshore')}%</b></span>
      <span>No market instrument exists<br><b style="color:${stuck >= 40 ? 'var(--red)' : 'var(--ink)'}">${stuck}%</b></span></div>`;
  h += `<details style="margin:2px 0 6px"><summary style="font-size:13px;color:var(--ink2)">Input by input — instrument, and the basis that comes with it</summary><table class="tt">` +
    s.items.map(it => `<tr><td><b>${esc(it.n)}</b><br><span class="meta">${Math.round(it.w * 100)}% of cost base</span></td>
      <td><span style="color:${HB_META[it.b].c};font-weight:600">${HB_META[it.b].l}</span> — ${esc(it.contract)}
      <p style="font-size:12.5px;color:var(--ink2);margin:4px 0 0">${esc(it.basis)}</p></td></tr>`).join('') +
    `</table></details>`;
  if (s.unknown > 0.005) h += `<p class="meta">${Math.round(s.unknown * 100)}% of the cost base maps to an input with no reference entry yet — excluded from the split rather than assumed hedgeable.</p>`;
  return h;
}

function renderHedgeTable() {
  const box = document.getElementById('hedgetbl');
  if (!box) return;
  if (!CREF) { box.innerHTML = '<p class="meta">Loading the commodity reference sheet…</p>'; return; }
  const rows = DATA.companies.map(c => [c, hedgeSplit(c.id)]).filter(r => r[1])
    .sort((a, b) => ((b[1].none + b[1].contract) / b[1].total) - ((a[1].none + a[1].contract) / a[1].total));
  const pct = (s, b) => Math.round(s[b] / s.total * 100);
  box.innerHTML = `<table class="t"><tr><th>Company</th><th>Mapped cost base</th><th>Hedgeability split</th><th>No instrument</th><th>Needs offshore + FX leg</th></tr>` +
    rows.map(([c, s]) => {
      const stuck = pct(s, 'none') + pct(s, 'contract');
      return `<tr data-go="${c.id}" style="cursor:pointer"><td style="font-weight:600;white-space:nowrap">${esc(c.name)}</td>
        <td>${Math.round(s.total * 100)}%</td>
        <td style="min-width:180px">${hedgeBar(s, 200)}</td>
        <td style="font-weight:600;color:${stuck >= 50 ? 'var(--red)' : stuck >= 25 ? 'var(--amber)' : 'var(--ink2)'}">${stuck}%</td>
        <td>${pct(s, 'offshore')}%</td></tr>`;
    }).join('') + `</table>`;
}
"""

MARKUP = """
<h2 style="margin-top:26px">Hedgeability matrix — what can actually be covered</h2>
<p class="sub" style="margin-bottom:10px">Every company's cost base crossed with whether an instrument exists for each input. Ranked by the share with <b>no market instrument at all</b> — the part of the risk that has to be managed by contract, inventory and sourcing rather than by treasury. Sorting by this rather than by exposure size surfaces a different, and usually more actionable, set of names. Click a row for the full brief.</p>
<div class="card" id="hedgetbl" style="overflow-x:auto"></div>
"""


def main():
    src = open(HTML, encoding="utf-8").read()

    # 1. markup into the 'Who is exposed' tab, after the company grid
    old = '<div class="grid" id="cogrid"></div>\n\n<div id="panel"></div>'
    assert old in src, "companies tab anchor not found"
    src = src.replace(old, '<div class="grid" id="cogrid"></div>\n' + MARKUP + '\n<div id="panel"></div>', 1)

    # 2. renderer
    src = src.replace("function renderDeep(id) {", JS.strip() + "\n\nfunction renderDeep(id) {", 1)

    # 3. per-company panel in the deep dive, right after the input chain
    old = "  h += prodHTML(id);"
    assert old in src
    src = src.replace(old, "  h += hedgeCard(id);\n  h += prodHTML(id);", 1)

    # 4. render the league table when the reference sheet lands, and on tab switch
    src = src.replace("renderPeriodic(); if (PT.sel) showCom(PT.sel); })",
                      "renderPeriodic(); renderHedgeTable(); if (PT.sel) showCom(PT.sel); })", 1)

    open(HTML, "w", encoding="utf-8").write(src)
    print("hedgeability matrix added")


if __name__ == "__main__":
    main()
