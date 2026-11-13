# What a commodity & treasury risk partner would actually pay for

**Written:** 30 July 2026 · companion to `PARTNER-REVIEW.md` (16 Jul), which covered correctness and architecture. This one covers *product*: which features solve a real problem for a partner running a commodity & treasury risk practice at a top-tier firm, and which ones only look like they do.

Every idea below is scored on two axes, because the second one is where most risk-tool roadmaps die:

- **Value** — does it help win, scope, or deliver billable work?
- **Validatable** — can the number be checked against something outside the tool? A feature that cannot be validated is a liability, not an asset. That is the standard the removals in this release were held to.

---

## 1. What the job actually is

A partner in this seat has four recurring problems. Not one of them is "I need another risk score."

**P1 — I have to find the conversation before the client does.** Advisory work is sold on a trigger: a rule changed, a deadline is approaching, a price moved past where the client's assumptions were set. The partner's scarcest input is a list of *named clients* with a *dated reason to call*. Generic market commentary is worthless here; every large firm already produces too much of it.

**P2 — I have to scope it before I can price it.** Between "there's an issue" and "here's a proposal" sits a diagnostic: how big is the exposure, in rupees, against what denominator, and what would fixing it involve. Partners lose deals by taking three weeks to answer that.

**P3 — I have to defend every number in front of a CFO and, eventually, an auditor.** One wrong date or stale price ends the tool's life in that account. This is why the removals in this release matter more than the additions.

**P4 — I have to deliver in the client's formats and vocabulary.** VaR and Expected Shortfall on real series, Cash-Flow-at-Risk, Ind AS 109 hedge effectiveness in the 80–125% band, UFCE capital treatment, RBI Master Direction compliance, board risk-appetite statements. A bespoke 0–100 composite is a fine ranking device and a terrible billing vocabulary.

A useful test for any feature: **which of P1–P4 does it serve, and would a director staff someone against it on Monday?**

---

## 2. The insight this release is built on

Going through the Commodities 101 breakdown, the section that matters most for this practice is not supply, demand, or price history. It is **How It Trades** — venue, benchmark contract, lot size, price terms, settlement, curve shape, liquidity.

Because that table answers the question a treasurer is actually asking, which is not "what will copper do" but:

> **Can I do anything about this at all?**

Cross that against a client's cost base and you get something no Indian risk tool currently ships:

| Bucket | Meaning | What it implies |
|---|---|---|
| Onshore INR contract | MCX / NCDEX listed | Hedge in rupees, no FX leg, lightest permissions |
| Offshore USD/EUR only | LME / CME / ICE / SGX | RBI Master Direction permission + a currency leg — and that leg sits under the April 2026 NDF prohibition |
| Proxy hedge only | correlated contract | Material basis; Ind AS 109 effectiveness at 80–125% is hard to hold |
| OTC / index-linked | formula pricing, bilateral swap | Counterparty credit and disclosure move to the client |
| No hedge exists | nothing, anywhere | Contractual and operational levers only |

That is the **Hedgeability Matrix**, shipped in this release. It runs off data already on the page, so every number is traceable, and it re-ranks the client universe in a way that surfaces different names than an exposure ranking does.

Three findings it produced immediately, none of which the previous exposure view showed:

- **Sun Pharma: ~100% of mapped cost base has no financial hedge.** APIs and KSMs are unhedgeable and China-concentrated. The exposure is *availability*, not price — which means the engagement is supply-chain mapping and dual-sourcing economics, not a hedge programme. Selling a hedging engagement here would be selling the wrong thing.
- **Exide: ~82% is hedgeable onshore, in rupees, today.** Lead is 56% of the cost base, MCX Lead is liquid, and the position is persistently under-hedged. Low complexity, high measurable value, and a natural first engagement that opens the account.
- **IndiGo: ~97% is hedgeable but only offshore in USD.** Jet fuel has no Indian contract, so the hedge carries a currency leg, an RBI permission, a fortnightly OMC price-reset lag and a route-weighted state VAT mix. Four-part basis. That is a flagship engagement and the reason Indian carriers historically hedge far less than global peers.

**Why this is defensible:** the "can they hedge it" classification is checkable against published exchange contract specifications. It is a fact about the world, not a model output. That is the rarest property in this whole tool.

---

## 3. Ranked build list

### Tier 1 — build next (high value, fully validatable)

**1.1 Hedge-effectiveness calculator (Ind AS 109)** · serves P2, P3, P4
Dollar-offset and regression methods on a hedge series versus an exposure series, with the 80–125% band verdict, and the ability to upload a client's own series as CSV. This is the single most sellable feature for a treasury practice: it is a *standard*, the answer is objectively right or wrong, and it is exactly the test a client's auditor will run. It also pairs directly with the Hedgeability Matrix — the matrix says a proxy hedge carries basis, and this quantifies whether that basis breaks effectiveness. **Validatable: completely** — the method is published, and results reconcile against the client's own auditors.

**1.2 ₹ crore conversion everywhere, with EBITDA denominators** · serves P2, P4
Every impact currently shows as a percentage of cost base. Partners sell in rupees crore. `data/financials.json` already carries verified FY26 revenue and EBITDA for a handful of names; extend it across the universe and convert every modelled impact. A 2% cost-base move means nothing; "₹340 crore of FY27 EBITDA at risk, 11% of last year's" starts a conversation. **Validatable: completely** — filed financials.

**1.3 Basis decomposition for the top ten Indian hedge mismatches** · serves P2, P3
The reference sheet already names these one by one. Turn each into a computed number instead of prose:
- MCX crude settles against **WTI** while India's basket is ~75% **Dubai**-linked — the grade basis is unhedged in most Indian programmes
- Newcastle 6,000 kcal versus Indonesian 4,200 kcal thermal coal — needs a calorific-adjusted hedge ratio
- ICE Cotton No. 2 versus Indian Shankar-6, with an MSP floor that makes the downside distribution non-normal and breaks any VaR that assumes otherwise
- Bursa FCPO is **MYR**-denominated (a third currency leg) and prices Malaysian crude palm, not the Indonesian refined palmolein India imports
- CME HRC prices US Midwest steel, not Indian flat steel
Each is a self-contained diagnostic a director can staff, and each ends in a number the client can act on. **Validatable: yes** — computed from two public price series.

**1.4 Cash-Flow-at-Risk per company** · serves P2, P4
Shock distribution → cost base → EBITDA distribution → "5% chance FY27 EBITDA falls more than ₹X crore." Uses the real vols and correlations the pipeline already computes. This is the language a CFO thinks in and it converts the whole model lab into one sentence a board can act on. **Validatable: partly** — the mechanics are standard, the inputs are real, but the output is a model number and must be labelled as one.

**1.5 Freight as a hedgeable line** · serves P1, P2
Dry bulk freight is 15–30% of landed coal cost, moves more than the coal does, has liquid FFAs — and essentially no Indian importer hedges it. Adani Power, Tata Power, the cement makers and the fertiliser importers all carry it inside landed cost where nobody looks. This is the clearest unexploited hedge in the Indian corporate book and the instrument already exists. **Validatable: completely** — Baltic indices are public.

### Tier 2 — build after (high value, needs data or time)

**2.1 India-terms market data** · serves P3
FBIL USD/INR reference fix (the official number a treasurer quotes), MCX bhavcopy, forward premia and the MIFOR curve, MIBOR, G-sec yields. Everything on the page today is USD-terms from global feeds. A treasurer will not accept a number that is not the one they mark against. `scripts/pipeline.py` already flags MCX bhavcopy as a TODO. **Validatable: completely** — official published fixes.

**2.2 Forward-cover cost and the FCNR(B) window calculator** · serves P1, P2
Premia-based cost of cover by tenor, plus the arbitrage while the FCNR(B) subsidy window is open (closes 30 Sep 2026). Deadline-driven, so it is a P1 trigger as well as a P2 tool. Needs 2.1 first. **Validatable: completely.**

**2.3 RBI hedge-policy compliance checklist generator** · serves P1, P2
Client's instrument list versus the amended Master Direction post the 1 April and 5 June 2026 changes → a gap table. Turns "hedge-policy redesign" from a pitch line into a demo. Every Indian corporate with an FX book needs this and most have not re-papered since April. **Validatable: yes** — against the circular text.

**2.4 UFCE provisioning estimator** · serves P1
The bank-channel play. RBI's unhedged foreign currency exposure framework forces banks to collect borrower hedging data and hold capital against unhedged clients. Show a bank how much provisioning a borrower's hedge programme would release, and the bank introduces you to the borrower. The bank sources the client; you deliver the work. **Validatable: yes** — the RBI formula is published.

**2.5 Real GARCH/EVT on market history** · serves P3, P4
The circular fit-to-simulation is now removed. The honest replacement is GARCH(1,1) vol and a GPD peaks-over-threshold fit on the actual return series the pipeline already stores, with mean-excess diagnostics — for the ~15 series where real history exists, and explicitly not for the rest. **Validatable: partly** — the fit is checkable, the extrapolation is not.

**2.6 Real backtest, once there is history** · serves P3
`data/history.json` holds four days. At twelve weeks the Validation tab can report real AUC, Brier and calibration. The outcome definition must be written down *now*, before the data exists, or the backtest measures the choice rather than the model. **Validatable: completely — and not before then.**

### Tier 3 — worth doing, lower leverage

- **PPT board pack and XLSX exposure tables** (pptxgenjs / SheetJS, client-side). Serves P4. Partners live in PPT; a markdown brief is a good start and not enough.
- **Sector playbooks as first-class pages** — airline fuel hedging, steel/CBAM, jewellery gold-duty. The content largely exists; packaging it as a repeatable methodology is what makes it a practice asset rather than a one-off.
- **Alerts that fire with no browser open** — watchlist and KRI triggers to a GitHub issue or email from the Action. Currently they only evaluate in-browser, which means they never fire when it matters.
- **Contract-clause audit template.** Recurring across the expanded universe: Motherson, Polycab, Bharat Forge and the road EPC contractors all depend on pass-through and escalation clauses whose actual coverage nobody has measured. "What share of your input book is covered, at what lag" is a five-minute question that repeatedly surprises the CFO. Low tech, high hit rate.

### Tier 4 — do not build

- **Anything that generates its own evidence.** The synthetic backtest, the seeded expert panel, the GPD fitted to the simulator's own draws, the invented counterparty limits feeding the real breach queue. All removed in this release. The failure mode is not that they are wrong; it is that they are *unfalsifiable*, and a partner who discovers one stops trusting every other number on the page.
- **A credit-risk module.** Real counterparty risk needs real credit data. Half a credit system is worse than none.
- **Price forecasting.** The tool's credibility rests on being right about *structure* — who is exposed, to what, and whether they can hedge it. One bad price call in a client meeting costs more than every correct structural insight earns.
- **Multi-user auth and shared state.** Only if this graduates from a single-partner tool. Until then it is infrastructure work that serves no P.

---

## 4. Where this tool is genuinely differentiated

The competitive picture from the July review still holds, and the Hedgeability Matrix sharpens it:

- **IBSFINtech, Kyriba** — automate treasury *execution*. They assume you already know what to hedge.
- **QuantArt** — sells hedging *advisory*, name by name.
- **Bloomberg, LSEG** — sell *data*. They will tell you the LME price; they will not tell you that MCX crude settles against WTI while your client buys Dubai.

Nobody ships the layer in between: **a structural map of which Indian corporate exposures are hedgeable, by what instrument, with what basis, under which RBI permission.** That is a defensible niche, it is built from public facts rather than proprietary data, and it is the natural front end to every engagement in Tier 1.

---

## 5. The honest caveats

- Cost-base shares are estimates from segment disclosure and annual-report commentary. They are disclosed as estimates and should stay that way. They are good enough to rank and to scope; they are not good enough to put in a client deliverable without confirming against that client's own ledger — which is itself the first day of the engagement.
- The Hedgeability Matrix answers "is there an instrument", not "should they use it". Whether to hedge is a policy question involving pricing power, competitor behaviour and board appetite. The tool's job is to make the question askable.
- 49 of the 97 commodities carry structural facts and trading terms only, not full profiles. That is labelled on each. Deepening them is worth doing when a client engagement demands it, not before — depth without a buyer is inventory.
