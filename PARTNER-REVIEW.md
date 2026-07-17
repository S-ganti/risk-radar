# Risk Radar — Partner Review & Go-Ahead Roadmap

**Reviewed:** 16 July 2026 · commit `9f5ab4a` · build `2026-07-10-sankey6-v15` · live check of https://s-ganti.github.io/risk-radar/
**Status:** ✅ **P0 (items 1–10) implemented and verified locally on 16 July 2026** — partner approved go-ahead. Next: P1 live-data backbone.
**Scope:** what a Big 4 partner (Risk Advisory — commodity & treasury, India) would value; accuracy audit of the embedded facts; gap analysis; and the full go-ahead list to reach live data + MCP servers + real model calculations.

---

## 1. The bar: what a Big 4 partner in this seat actually values

A partner running commodity & treasury risk advisory in India judges a tool like this on five things, in order:

1. **Does it help me win work this quarter?** The tool must answer "which client do I call this week, about what, before which deadline." Deadline-driven windows (FCNR(B) closing 30 Sep 2026, CBAM certificates Feb 2027, EUDR Dec 2026) are the strongest BD triggers because they compel client action.
2. **Can I repeat any number in front of a client CFO without checking it first?** Every figure must be traceable to a primary source (RBI circular number, OJ regulation number, annual-report page) with an as-of date. One wrong date or stale price in a client meeting permanently ends the tool's credibility — and the partner's willingness to open it.
3. **Does it speak the vocabulary their teams bill in?** VaR/Expected Shortfall on real price series, Cash-Flow-at-Risk, hedge-effectiveness testing under Ind AS 109 (80–125% band), UFCE capital treatment, board risk-appetite statements, RBI Master Direction compliance. A bespoke 0–100 composite score is fine as a *ranking* device, but the billable conversation happens in standard-model language.
4. **Is it current?** "Weekly cycle" is a promise; a missed week is visible. Treasury advisory in mid-2026 India moves on daily rupee levels and circular-by-circular RBI action.
5. **Can I get it into my formats?** Partners live in PPT and PDF board packs; directors staff from scoping tables; analysts want XLSX. A markdown brief is a good start and not enough.

**Persona nuances:** the partner cares about pipeline + defensibility; the director about scoping and owners; a treasury client about compliance and limits; a commodity client about physical exposure and basis. The existing five-persona cockpit maps to this correctly — the concept is right.

**Competitive whitespace (validated):** IBSFINtech and Kyriba automate treasury *execution* ([IBSFINtech](https://www.ibsfintech.com/us/), IDC-recognized TMS), [QuantArt](https://quantartmarket.com/) sells hedging *advisory*, Bloomberg/LSEG sell *data*. None ships an India-policy-interpretation radar that converts regulatory events into named-client advisory openings. That is this tool's defensible niche — the cycle-JSON "so-what" already says this, and the research confirms it.

---

## 2. Verdict on the current build

**What is genuinely partner-shaped (keep all of it):**
- The **signal → exposure pathway → evidence → action → brief** chain. This is exactly how a risk partner thinks, and almost no internal tool implements it end-to-end.
- The **evidence-first weekly cycle log** (reasoning before conclusions, citations on every claim, secondary sources flagged and queued for primary retrieval). This is audit-culture discipline applied to BD — a differentiator.
- **Model governance disclosure** (every constant, cap, and blind spot in "Parameters & limits"; a governance registry with owners and review cadence). Mirrors real model-risk-management practice and will impress a partner more than the models themselves.
- The **stress lab** (stackable historical/hypothetical shocks, editable pass-through/hedge/inventory assumptions, saved configs that become scoreable risk items).
- The honest-caveat culture, persona reordering, command palette, and overall presentation quality. Zero console errors; all 11 tabs and 6 model families compute live.

**The blocking flaw:** the numbers underneath are mock or hand-set in exactly the places a partner would drill:

| Layer | Current state |
|---|---|
| Monte Carlo volatility | σ derived from a 1–5 *rating*, not market data |
| EVT / GPD tail fit | Fitted to the simulator's own output — circular; adds no information |
| Copula correlations | Defaults (0.2 / 0.55) unless a viewer pastes an Alpha Vantage key |
| Velocity / exposure / concentration (RSCORE) | Hand-typed constants per risk |
| 12-week trend sparklines | Fabricated random walks, labeled "12-week trend" in the UI with no synthetic disclaimer — the one place the caveat culture fails |
| Backtest outcomes | Synthetic (labeled ✓), but the mock is designed so the ensemble wins — the "empirical case for multi-model weighting" bullet is manufactured |
| Regime detection | Average of the hand-set velocities — self-referential |
| Counterparty table | Explicitly illustrative |
| Company impact | % of cost base only — never converted to ₹ crore EBITDA |

**Verdict: a credible demo with the right architecture, not yet a defensible tool.** The path is not to redesign — it is to keep the skeleton and replace every hand-set number with a computed one from live data. That is achievable at zero infrastructure cost (Section 5).

---

## 3. Information accuracy audit (verified 16 July 2026)

| Claim in dashboard | Status | Detail / required correction |
|---|---|---|
| CBAM definitive regime 1 Jan 2026; certificate sales 1 Feb 2027; first surrender 30 Sep 2027 | ✅ Correct | Matches [EC](https://taxation-customs.ec.europa.eu/carbon-border-adjustment-mechanism_en) and [DEHSt](https://www.dehst.de/EN/Topics/CBAM/CBAM-definitive-regime-2026/CBAM-certificates/cbam-certificates_node.html). **Add:** quarterly certificate-holding requirement cut 80%→50% (Omnibus) — relevant to client cash-flow planning; 2027 purchases priced off *2026 quarterly-average* ETS. |
| EUDR applies 30 Dec 2026 (large operators) | ✅ Correct | Regulation (EU) 2025/2650 as cited. |
| EU–India FTA concluded 27 Jan 2026, unratified | ✅ Correct | Sharpen "timing open" → **entry into force expected early 2027**; EU legal scrubbing concludes ~Jul 2026 ([ORF](https://www.orfonline.org/expert-speak/the-india-eu-fta-from-political-agreement-to-ratification-and-coming-into-force), [EC](https://ec.europa.eu/commission/presscorner/detail/en/ip_26_184)). |
| Gold import duty hiked May 2026 | ✅ Correct but incomplete | State the numbers: **6% → 15% effective 13 May 2026** (10% BCD + 5% AIDC) ([TaxGuru](https://taxguru.in/custom-duty/customs-duty-gold-silver-raised-15-percent-effective-13-may-2026.html), [CNBC](https://www.cnbc.com/2026/05/13/india-hikes-bullion-import-duties-to-arrest-rupee-slide.html)). Silver also 15% — relevant for Titan. A partner will ask "hiked *to what*?" |
| RBI "June 2026 package" = FCNR(B) subsidy + NDF ban + cancel/rebook bar, detected 2026-06-08 | ⚠️ **Dates wrong** | The **NDF prohibition and the cancel-and-rebook bar came via circular of 1 April 2026** after INR breached 95 ([Business Standard](https://www.business-standard.com/industry/banking/rbi-bars-banks-from-offering-ndf-contracts-to-corporates-126040101461_1.html), [circular text](https://worldtradescanner.com/03-RBI%20Circular-01.04.2026.htm)); earlier NDF tightening 2 Mar 2026 ([MUFG](https://www.mufgresearch.com/fx/india-rbi-further-tightens-inr-ndf-regulations-driving-a-wedge-2-march-2026/)). The **5 June 2026 MPC package** is the FCNR(B) piece: RBI absorbs full hedging cost (~280–300 bp) on fresh 3–5y deposits mobilised 8 Jun–30 Sep 2026; rate ceiling withdrawn 17 Jun ([Business Standard](https://www.business-standard.com/economy/news/rbi-bears-hedging-costs-banks-may-offer-100-bps-more-on-fcnr-b-deposits-126060501146_1.html), [MUFG](https://www.mufgresearch.com/fx/india-shoring-up-the-indian-rupee-rbi-june-2026-measures-8-june-2026/)). Fix `RISKS['rbi-fx']` (detected date, whyNow), the glossary entries, and cycle W28 text. The advisory story *survives* — arguably strengthens (corporates have been non-compliant since April). |
| RBI evidence URL (`Notification.aspx?Id=853`) | ❌ **Wrong document** | Resolves to the **July 2011** Master Circular on Risk Management and Inter-Bank Dealings — withdrawn July 2012. Replace with the actual 2026 A.P. (DIR Series) circular reference. This is the tool's single most load-bearing citation. |
| Snapshot: Brent $72.1, "+3.6% y/y" (7 Jul 2026) | ❌ **Stale & wrong, uncorrected** | Brent ≈ **$84.6 on 16 Jul 2026**, +21.7% y/y, on Strait of Hormuz escalation ([Trading Economics](https://tradingeconomics.com/commodity/brent-crude-oil)). The live strip fetches FX and gold but **has no Brent source**, so the wrong print sits on screen indefinitely. Meanwhile the "Brent +10%" risk card models as hypothetical something that partially happened. |
| Live FX/gold strip | ✅ Works | USD/INR 96.33 live (+0.97% vs baseline), gold $3,997 (−3.65%); INR signal correctly names most-exposed companies. This is the pattern to extend to everything else. |
| "Regenerated weekly" | ⚠️ Already broken | Only cycle 2026-W28 (7 Jul) is embedded; W29 (due ~14 Jul) is missing. Until automation exists, change copy to "as of cycle 2026-W28". |
| "12-week trend" sparklines | ❌ Integrity gap | Synthetic series presented as history. Label "illustrative" or hide until real history accumulates. |
| Company cost shares, lens scores, anchors | ✅ Acceptable as framed | Estimates are disclosed as estimates with AR anchors — this is the right pattern; keep. |

---

## 4. Gap analysis — what's missed, what to add, what needs more precision

### 4.1 Missing information types
- **India-terms market data**: MCX gold/silver/crude/natgas/base-metals (₹), FBIL USD/INR reference fix (the official number a treasurer quotes), forward premia / MIFOR curve, MIBOR, G-sec yields. Everything currently shown is USD-terms from global free APIs.
- **EUA price** — the dashboard tells steel clients they carry "a brand-new hedgeable EUA exposure" but never shows the EUA price or a certificate-cost estimate.
- **Coking-coal index** (the #1 steel input risk named) — no price at all.
- **₹ materiality** — no company revenue/EBITDA denominators, so no "₹ X crore EBITDA at risk". Partners sell in ₹ crore, not %.
- **Hedge disclosures per company** — ARs disclose hedge ratios/instruments (e.g., Maruti's JPY program); the tool assumes hedge = 0 by default.
- **Interest-rate layer** — a "rates" risk exists with no curve, no refinancing-wall data (bond maturities are public).
- **Between-cycle news flow** — nothing updates between weekly cycles; a daily headline scan (even links-only) keeps the tool "alive".

### 4.2 Model precision (replace hand-set with computed)
- Volatility: **EWMA (λ=0.94) and GARCH(1,1) on real daily returns**, not 1–5 ratings.
- VaR/ES: **historical simulation (1d/10d/1m) on 5y daily data** per commodity and per company input basket, with parametric and MC cross-checks — this makes the Quant card a real number a treasury team can reconcile.
- EVT: **GPD peaks-over-threshold on real return tails** (the code's method-of-moments fit is fine — feed it real data), with mean-excess diagnostics.
- Copula: real correlation matrix from returns; upgrade Gaussian → **t-copula** for tail dependence (or empirical copula).
- Regime: from **market observables** (realized-vol percentile, INR momentum, breadth of commodity moves), not the average of hand-set velocities.
- RSCORE velocity/exposure/concentration: computed (velocity = rate of change of underlying market/regulatory drivers; exposure = Σ affected cost bases in ₹; concentration from the dependency data it already has).
- Forecast: keep the logistic, but **Platt-calibrate on realized outcomes** once ~12 weeks of true history exists; label "seeded" until then.
- Backtest: swap synthetic outcomes for the accumulating real history; keep the metric machinery (it's already production-grade).

### 4.3 Missing treasury-specific features (the billable ones)
- **Hedge-effectiveness calculator** (Ind AS 109): dollar-offset + regression method on hedge vs exposure series, 80–125% band verdict. The single most sellable feature for treasury advisory; also feeds bank UFCE conversations.
- **CFaR per company**: shock distributions mapped through cost base → EBITDA distribution → "5% chance EBITDA falls > ₹X cr".
- **Forward-cover cost calculator**: premia-based cost of cover by tenor; quantifies the FCNR(B)-window arbitrage while it's open (76 days left).
- **UFCE provisioning estimator** — for the bank channel play already described in `watch`.
- **RBI-compliance checklist generator**: client's instrument list vs the amended Master Direction (post-April/June 2026) → gap table. Turns the "hedge-policy redesign" pitch into a demo.

### 4.4 Presentation gaps
- **Client-safe mode** (important): pipeline, pursuit status, "talking points", and rival-activity content are internal BD material sitting one tab away from client-facing analysis. A partner screen-sharing this in a client meeting leaks pipeline. Add a toggle that strips all BD layers.
- **As-of + source chip on every number** (the live strip has it; scores and snapshots don't).
- **PPT/XLSX export** (board pack via pptxgenjs, exposure tables via SheetJS) alongside the .md brief.
- **Alerts that fire when nobody has the tab open** — watchlist/KRI currently evaluate only in-browser.

---

## 5. Target architecture — live data, MCP servers, real calculations (zero-cost)

Keep the philosophy that makes this deployable anywhere (single static file, GitHub Pages, no server, no keys in the file). Move *data acquisition and heavy computation* into the repo's CI, and expose the same capabilities as MCP servers for agent-driven analysis.

```
GitHub Actions (cron)                      GitHub Pages (static)
┌──────────────────────────────┐           ┌──────────────────────────┐
│ daily 18:30 IST  data pull   │  commits  │ index.html               │
│  FBIL fix · MCX bhavcopy     │──────────▶│  fetch('./data/latest    │
│  EIA Brent/gas · er-api FX   │           │   .json') same-origin,   │
│  gold-api · EUA proxy · WB   │           │  embedded snapshot as    │
│ engine/ (real calcs)         │           │  offline fallback        │
│  returns · EWMA/GARCH vol    │           │ models seeded with real  │
│  hist-sim VaR/ES · GPD tails │           │  params; interactivity   │
│  corr matrix · regime state  │           │  stays client-side       │
│  ₹ impact · KRI/watch eval   │           └──────────────────────────┘
│ weekly Mon 06:00 IST         │
│  6-agent cycle w/ MCP tools  │──▶ auto-PR with diff (human gate) ──▶ merge deploys
│  alerts → GitHub issue/email │
└──────────────────────────────┘

MCP servers (local stdio, built with mcp-builder):
  india-markets-mcp   get_fbil_fix · get_mcx_eod · get_eia_series · get_history · get_eua
  risk-engine-mcp     run_var · run_stress · fit_gpd · hedge_effectiveness · score_risk · cfar
  regwatch-mcp        rbi_notifications · ec_cbam_news · pib_releases · diff_since(date)
```

**Why this shape:**
- **Same-origin `data/*.json`** removes CORS/key problems, keeps the page self-contained offline (embedded snapshot fallback stays), and — because snapshots are committed — **history accumulates in git**, which is what makes real sparklines, real regime detection, and real backtests possible within ~8–12 weeks.
- **The MCP servers are the "agents use real calculations" guarantee**: the weekly cycle agent writes its narrative *by calling* `risk-engine-mcp.run_var(...)` and `regwatch-mcp.rbi_notifications(...)` instead of asserting numbers. Every figure in a cycle JSON becomes tool-output-backed. (The claude.ai connector registry has no finance connectors, so custom servers are the right path; the installed bigdata.com plugin could complement news research but needs OAuth authorization first.)
- **Human gate before publish**: the weekly run opens a PR with the cycle diff; the analyst/partner approves → merge → Pages deploys. That is the model-governance story made real.

**Data sources (all free):** [FBIL](https://www.fbil.org.in/) reference rates (official fix, also via [frankfurter's FBIL provider](https://frankfurter.dev/providers/fbil/)); [MCX bhavcopy](https://www.mcxindia.com/market-data/bhavcopy) daily EOD; [EIA API](https://www.eia.gov/dnav/pet/hist/rbrted.htm) (Brent/WTI/HH, free key); open.er-api.com + gold-api.com (already used); World Bank Pink Sheet monthly; [RBI DBIE](https://data.rbi.org.in/DBIE/); RBI notifications RSS; sandbag/EEX public EUA prints or ICE-derived proxy; NSE/BSE announcements for company events.

---

## 6. The go-ahead list

### P0 — Correctness (do before any partner sees it; ~half a day)
1. Fix the RBI timeline: NDF ban + cancel/rebook bar → 1 Apr 2026 circular (and 2 Mar tightening); June = FCNR(B) subsidy package. Update `RISKS['rbi-fx']`, glossary, cycle text, SVCMAP labels.
2. Replace the broken RBI citation (currently the withdrawn 2011 Master Circular) with the real 2026 circular reference(s).
3. Kill or correct the Brent snapshot ($72.1 → ~$84.6, +3.6% → ~+22% y/y); until a live feed exists, show Brent with an explicit "snapshot, not live" chip.
4. Label the sparklines "illustrative" (or hide) until real history exists; same for the counterparty table.
5. Soften the backtest note ("ensemble beats single models" is a property of the mock design, not evidence yet).
6. State the gold-duty numbers: 6% → 15% w.e.f. 13 May 2026 (BCD 10% + AIDC 5%), silver included.
7. Sharpen FTA line: entry into force expected early 2027; EU legal scrubbing ~Jul 2026 — this *dates* the "EUR build-out" pitch window.
8. Add the CBAM 50% quarterly-holding relaxation to the policy note.
9. Change "regenerated weekly" copy to "as of cycle 2026-W28" until automation lands.
10. Add **client-safe mode** toggle (hides pipeline, pursuit, talking points, rival activity).

### P1 — Live-data backbone (the big unlock; ~2 days)
11. GitHub Action (daily cron): pull FBIL fix, MCX bhavcopy, EIA Brent/gas, er-api FX, gold-api, monthly WB Pink Sheet → write `data/latest.json` + dated history files; commit.
12. Page consumes `data/latest.json` with the embedded snapshot as fallback; every number gets a source + as-of chip.
13. Compute real daily/monthly returns, correlation matrix, EWMA vol in the Action (`engine/`); page reads computed params — retire the "paste an Alpha Vantage key" UX to an optional fallback.
14. Add company financial denominators (revenue, EBITDA, net debt — annual, sourced from filings) → convert every impact to **₹ crore** alongside %.
15. Compute RSCORE velocity/exposure/concentration from data; document the formulas in Methodology.
16. Persist per-cycle score history (`data/history.json`) → real sparklines and real "what moved".
17. Add EUA price series + a CBAM certificate-cost estimator (t CO₂/t steel × volumes × EUA) for Tata Steel / JSW / Hindalco.
18. Real regime detection from vol percentile + INR momentum + move breadth.

### P2 — Real model calculations (~3 days)
19. Historical-simulation VaR/ES (1d/10d/1m) per commodity and per company basket; parametric + MC cross-checks; show all three.
20. GARCH(1,1)/EWMA vol feeding the MC engine; vol cones on commodity pages.
21. GPD/EVT fitted to real return tails with diagnostics; drop the circular fit-to-simulation.
22. t-copula (or empirical) joint stress on the real correlation matrix.
23. CFaR per company: shock distribution → cost base → EBITDA distribution → "5% worst case = ₹X cr".
24. Hedge-effectiveness module (dollar-offset + regression, 80–125% verdict) with CSV upload for client series — the flagship treasury demo.
25. Forward-cover cost + FCNR(B)-window arbitrage calculators (premia-based).
26. Platt-calibrate the breach forecast once ≥12 weeks of real outcomes exist; wire the backtest harness to real history (the metric code already accepts it).
27. Network model: eigenvector centrality; keep λ-decay propagation.

### P3 — MCP servers + automation (~2–3 days)
28. Build `india-markets-mcp`, `risk-engine-mcp`, `regwatch-mcp` (Python FastMCP; stdio for Claude Code/Desktop). Tools as listed in §5.
29. Re-point the weekly 6-agent cycle to run *through* these tools — every cycle claim becomes tool-output-backed; enforce primary-source-or-flagged rule mechanically.
30. Weekly cycle on schedule (Actions cron or Claude scheduled task) → **auto-PR with the cycle diff** for human sign-off before deploy.
31. Alerting in the pipeline: watchlist/KRI triggers → GitHub issue + email (Actions SMTP) so alerts fire with no browser open.

### P4 — Partner-grade output (~2 days)
32. One-click **PPT board pack** (pptxgenjs, client-side: cockpit summary, top risks, exposure map, calendar) and **XLSX exposure tables** (SheetJS).
33. Briefs get ₹ figures, charts, and firm-style cover page; PDF polish.
34. Sector playbooks as first-class pages — start with **airline fuel hedging** (content already exists from prior diagnostics work), steel/CBAM, jewellery/gold.
35. UFCE provisioning estimator for the bank-channel pitch.
36. RBI hedge-policy compliance checklist generator (instrument list → Master Direction gap table).

### Future features (post-approval backlog)
37. Multi-cycle trend analytics and score attribution over time.
38. Tier-2 CBAM exposure (Indian suppliers of EU manufacturers) — already an open question in cycle W28.
39. FTA tariff-schedule chapter tracker when the legal text publishes in the OJ.
40. MCX options analytics (gold options for Titan-type plays; Greeks, lease-vs-futures-vs-options comparison).
41. Monsoon/climate scenario pack (IMD data) for FMCG/tractor names.
42. CCTS domestic carbon-price tracker as the Indian market matures.
43. Multi-user: auth + shared pipeline state (replace localStorage) — only if it graduates from single-partner tool.
44. Refinancing-wall data (public bond maturities) to make the "rates" risk concrete.

---

## 7. Questions the partner will ask (be ready)

1. *"Where does this number come from?"* — after P1, every number has a source chip; until then, the Methodology tab is the answer.
2. *"Can I email this to a client?"* — only after P0 items 1–3 and 10 (client-safe mode); today the BD layer and the date errors make it internal-only.
3. *"What if RBI clarifies the rebooking rule for trade-linked changes?"* — banks are already seeking FEDAI clarification; the regwatch pipeline (P3) is the systematic answer.
4. *"Why should I trust the ensemble score?"* — honest answer today: it's a structured ranking, not a validated model; after P2/P3 the backtest tab shows real AUC/Brier on real outcomes.
5. *"Who maintains this?"* — the automation + PR-gate design (P3) means one analyst-hour a week plus partner sign-off.

---

## 8. Cost & effort summary

Everything above runs on free tiers: GitHub Actions cron + Pages, FBIL/MCX/EIA/er-api/World Bank public data, client-side export libraries. No server, no paid keys required (EIA needs a free registration key stored as an Actions secret). Total effort to a partner-defensible live tool: **P0 ≈ 0.5 day → P1 ≈ 2 days → P2 ≈ 3 days → P3 ≈ 2–3 days → P4 ≈ 2 days.**

*Prepared as an internal review. All verification sources accessed 16 July 2026.*
