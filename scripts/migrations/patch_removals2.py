#!/usr/bin/env python3
"""
Second removal pass — the code paths the first pass left behind.

  - secCounterparty() and the COUNTERPARTIES fixture. The fixture was worse
    than a display-only mock: allBreaches() read its invented limit
    utilisations and pushed "Limit utilization > 100%" rows into the cockpit's
    breach and escalation queue, next to real ones. Deleted at the source.
  - hseriesSynthetic(), now unreferenced since the backtest went. hseries()
    already reads real history from data/history.json and spark() already
    handles an empty series.
  - The whole Alpha Vantage client-side correlation path. The daily pipeline
    computes a real 105-pair correlation matrix; a fallback that asks the
    viewer to paste a personal API key into the browser is dead weight, and
    when it silently failed the map fell back to curated priors while still
    reading as live. renderManagedCorr() stays; the box now states plainly
    when no computed matrix is available.
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "index.html")


def cut(s, pattern, what, flags=re.S):
    m = re.search(pattern, s, flags)
    assert m, f"NOT FOUND: {what}"
    return s[:m.start()] + s[m.end():]


def main():
    s = open(HTML, encoding="utf-8").read()
    n0 = len(s)

    # counterparty fixture + renderer + the breach rows it manufactured
    s = cut(s, r'function secCounterparty\(\) \{.*?\n\}\n', "secCounterparty")
    s = cut(s, r'\s*COUNTERPARTIES\.forEach\(c=>\{ if\(c\.util>100\).*?\}\);\n', "counterparty breach rows")
    for pat, what in [(r'const COUNTERPARTIES\s*=\s*\[.*?\n\];\n', "COUNTERPARTIES fixture"),
                      (r'const cpStatus\s*=[^\n]*\n', "cpStatus"),
                      (r'function cpStatus\([^\n]*\n', "cpStatus fn")]:
        if re.search(pat, s, re.S):
            s = cut(s, pat, what)

    # unreferenced synthetic history generator
    s = cut(s, r'function hseriesSynthetic\(id\)\{.*?\n(?=function spark)', "hseriesSynthetic")

    # Alpha Vantage client-side correlation path
    s = cut(s, r'async function loadCorr\(force\) \{.*?\n\}\n', "loadCorr")
    s = cut(s, r'window\.avRefresh = [^\n]*\n', "avRefresh")
    s = cut(s, r'function renderCorrBox\(state, info\) \{.*?\n\}\n', "renderCorrBox")
    s = cut(s, r'\s*renderCorrBox\(\'done\'[^\n]*\n', "renderCorrBox call")
    s = s.replace("""  if (CDATA && CDATA.corr && Object.keys(CDATA.corr).length) { renderManagedCorr(); renderPeriodic(); }
  else loadCorr(false);""",
                  """  if (CDATA && CDATA.corr && Object.keys(CDATA.corr).length) { renderManagedCorr(); renderPeriodic(); }
  else { const el = document.getElementById('corrbox');
    if (el) el.innerHTML = `<div style="font-weight:600">Price correlation matrix</div>
      <p style="font-size:13px;color:var(--ink2);margin:8px 0">The daily pipeline computes Pearson correlations on overlapping monthly log returns and writes them to <code>data/latest.json</code>. No computed matrix is loaded right now, so the copula model is falling back to curated structural priors — those are documented assumptions, not measurements, and are labelled as such in the model's parameters.</p>`; }""", 1)
    s = s.replace("window.restoreManaged = () => { if (CDATA && CDATA.corr) { LIVECORR = CDATA.corr; renderManagedCorr(); renderPeriodic(); } };\n", "")

    open(HTML, "w", encoding="utf-8").write(s)
    print(f"second removal pass: {n0} -> {len(s)} chars ({n0 - len(s)} removed)")


if __name__ == "__main__":
    main()
