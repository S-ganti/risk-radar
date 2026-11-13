# Test run

2026-11-13T09:45:38.863007+00:00

## node --test tests\html.test.js tests\models.test.js

Exit: 0

```text
✔ workspace script parses (2.5908ms)
✔ atlas navigation and dependency tree script parses (0.9658ms)
✔ market refresh and scenario script parses (0.7065ms)
✔ directory has unique company IDs (2.5698ms)
✔ original analytics retained alongside workbench (7.0306ms)
✔ composite risk is deterministic and bounded (1.5405ms)
✔ attention priority does not infer controls from recommended actions (0.1827ms)
✔ breach engine only emits evaluated rules (0.2424ms)
✔ pressure index cannot be mistaken for a probability (0.1783ms)
✔ ensemble reports disagreement without a decision floor (2.5989ms)
✔ control strength requires tested control evidence (0.1539ms)
✔ Ind AS 109 diagnostics expose evidence and never apply an 80-125 bright line (0.2791ms)
✔ stress engine keeps consumer cost and producer revenue channels separate (0.1636ms)
✔ portfolio CFaR uses supplied positions, live vols, and correlations (0.3409ms)
ℹ tests 14
ℹ suites 0
ℹ pass 14
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 114.3689

```

## C:\Users\Sriha\AppData\Local\Programs\Python\Python314\python.exe -m unittest discover -s tests -p test_*.py

Exit: 0

```text
.............
----------------------------------------------------------------------
Ran 13 tests in 0.161s

OK

```

## C:\Users\Sriha\AppData\Local\Programs\Python\Python314\python.exe tests/test_engine.py

Exit: 0

```text

stats
  PASS  quantile median
  PASS  quantile min/max
  PASS  z(0.99) ~ 2.326  [2.3263]
  PASS  Phi(0) = 0.5
  PASS  excess kurtosis of normal ~ 0  [-0.065]
  PASS  excess kurtosis of t(5) > 1  [4.48]
  PASS  pearson of identical series = 1
  PASS  pearson of opposite series = -1
  PASS  overlapping aggregation  [[3, 3, 3]]
  PASS  chi2_sf(3.84, 1) ~ 0.05  [0.0500]
  PASS  chi2_sf(5.99, 2) ~ 0.05  [0.0500]

var / es
  PASS  parametric VaR99 ~ 2.326 sigma  [0.0465 vs 0.0465]
  PASS  historical ~ parametric on normal data  [hist 0.0474 vs param 0.0465]
  PASS  ES > VaR always
  PASS  VaR99 > VaR95
  PASS  10-day VaR > 1-day VaR  [0.1471 vs 0.0474]
  PASS  10-day VaR roughly sqrt(10) scaled  [ratio 3.10]
  PASS  t-MC VaR exceeds normal parametric  [mc 0.0526 param 0.0465]
  PASS  short series returns None
  PASS  kupiec accepts correct coverage  [rate 0.0100 p=1.000]
  PASS  kupiec rejects 10x over-exceedance
  PASS  christoffersen flags clustering  [lr=159.429]
  PASS  kupiec accepts a VaR that is right by construction  [rate 0.0115]
  PASS  thin estimation window is flagged  [53/3750 tail_obs=2.5]
  PASS  thin-window verdict does not blame the model  [rejected at 5%, but the estimation windo]
  PASS  adequate window passes coverage  [31/3000 rate=0.0103]
  PASS  adequate window is not flagged
  PASS  95% on 250 days is adequate and passes  [rate=0.0509]

garch
  PASS  fit returns a result
  PASS  alpha recovered  [0.0897 vs 0.08]
  PASS  beta recovered  [0.8883 vs 0.9]
  PASS  persistence < 1 (stationary)  [0.9780]
  PASS  unconditional vol recovered  [0.00730 vs 0.00707]
  PASS  half-life positive
  PASS  21d forecast > 1d sigma
  PASS  short series returns None

evt
  PASS  exponential tail gives xi near 0  [xi=0.0257]
  PASS  pareto tail gives xi > 0.2  [xi=0.4296]
  PASS  heavier tail has larger xi than exponential  [0.4296 > 0.0257]
  PASS  tail quantiles increase with confidence  [0.09162 > 0.06366]
  PASS  ES exceeds VaR at same level
  PASS  mean-excess diagnostic produced
  PASS  short series refuses to fit
  PASS  tail table has 4 levels

copula
  PASS  correlated pair recovered ~0.8  [0.840]
  PASS  independent pair near 0  [0.058]
  PASS  non-PSD matrix repaired
  PASS  repaired matrix is choleskyable
  PASS  repaired diagonal is 1
  PASS  gaussian marginal vol ~ target  [0.0501]
  PASS  t marginal vol ~ target (standardised)  [0.0487]
  PASS  t copula fatter tailed than gaussian  [t 3.05 vs g 0.05]
  PASS  t copula shows more tail dependence than gaussian  [t 0.5433 vs g 0.4767]
  PASS  df estimator returns a number in range  [df=30.0]

hedge (Ind AS 109)
  PASS  perfect hedge: dollar offset 100%  [100.0]
  PASS  perfect hedge: slope -1  [-1.0]
  PASS  perfect hedge: R2 = 1
  PASS  perfect hedge: verdict effective
  PASS  noisy hedge produces a verdict  [mixed]
  PASS  unrelated instrument is not effective  [ineffective]
  PASS  over-hedge falls outside the band  [200.0%]
  PASS  basis risk computes a hedge ratio
  PASS  basis vol reported

cfar
  PASS  cfar returns a rupee figure  [1186.7 cr]
  PASS  cfar is positive (a cost increase)
  PASS  ES exceeds CFaR
  PASS  percent of EBITDA computed
  PASS  statement mentions crore
  PASS  hedging halves the exposure  [593.4 vs 1186.7]
  PASS  longer horizon increases CFaR  [24m 1678.3 > 12m 1186.7]
  PASS  contribution ranks the drivers
  PASS  largest weight is the top driver  [crude]
  PASS  missing vol is refused

============================================================
All engine tests passed.

```

## C:\Users\Sriha\AppData\Local\Programs\Python\Python314\python.exe tests/test_mcp_servers.py

Exit: 0

```text

risk-engine-mcp
  PASS  list_series returns series  [15 series]
  PASS  crude present
  PASS  run_var historical produces a loss  [0.0706]
  PASS  run_var returns all three estimators
  PASS  run_var reports estimator spread  [estimators disagree materially � tail ]
  PASS  run_var refuses unknown series
  PASS  backtest returns a verdict  [model rejected at 5% � exception rate is]
  PASS  thin window is warned about
  PASS  garch fit converges
  PASS  garch is stationary  [0.9765]
  PASS  garch forecast returned
  PASS  garch refuses a short monthly series  ['copper' has 61 returns; GARCH(1,1) needs >= ]
  PASS  tail fit returns xi  [xi=0.1045]
  PASS  tail table produced
  PASS  tail shape described
  PASS  joint stress uses t copula  [8.0]
  PASS  joint stress returns basket move
  PASS  joint stress needs 2+ series
  PASS  perfect hedge judged effective  [effective]
  PASS  dollar offset ~100%
  PASS  mismatched lengths refused
  PASS  basis risk aligns on common dates  [1295 obs]
  PASS  brent vs wti correlation is high  [rho=0.869]
  PASS  basis vol reported
  PASS  min-variance hedge ratio near 1  [0.8865]
  PASS  cfar list returned  [7 scored]
  PASS  cfar detail has rupee figure
  PASS  cfar detail ranks drivers
  PASS  cfar refuses unknown company
  PASS  model summary has method notes
  PASS  per-series summary has garch and evt

india-markets-mcp
  PASS  spot marks returned
  PASS  stale manual marks identified  [eua,cbam_ref]
  PASS  usdinr spot has as-of and source  [93.96 @ 2026-11-11]
  PASS  series returns requested tail
  PASS  series summary computed
  PASS  unknown series refused with alternatives
  PASS  volatility carries method and n  [EWMA(0.94) daily]
  PASS  correlations filtered by threshold  [3 pairs]
  PASS  regime label present  [normal]
  PASS  regime components exposed
  PASS  hedgeability lists commodities  [97 commodities]
  PASS  score history has a span  [117 obs 2026-07-17->2026-11-11]
  PASS  validation readiness stated  [True]
  PASS  moved/unmoved risks distinguished

regwatch-mcp  (network-dependent: content is not asserted)
  PASS  sources listed
  PASS  official-source policy stated
  PASS  elapsed-deadline check runs offline
  PASS  watchlist deadlines evaluated
  PASS  next deadline identified  [{"id": "eudr-application", "date": "2026-12-30", "days": 47}]
  PASS  no watchlist deadline is already elapsed  [[]]
  PASS  rbi feed returns items or a stated error  [could not reach Reserve Bank of India: <urlopen error [Errno]
  PASS  unreachable feed does not imply 'no change'
  PASS  unknown source refused
  PASS  watchlist diff runs
  PASS  diff refuses to conclude on its own
  PASS  candidates flagged as untrusted
  PASS  search returns a result set
  PASS  search notes feeds are untrusted input

============================================================
All MCP server tests passed.

```

## C:\Users\Sriha\AppData\Local\Programs\Python\Python314\python.exe scripts/validate.py

Exit: 0

```text
PASS    latest.freshness: latest.json is 37.7 hours old
PASS    spot.required: USD/INR, gold and Brent records are present
PASS    volatility.coverage: 15 volatility series
PASS    correlation.coverage: 105 correlation pairs
PASS    history.order: 117 sorted, unique dates
PASS    history.validation-window: 117 score snapshots retained; outcome labels are still required for validation
PASS    model-registry.ids: 9 unique model records
PASS    evidence-registry.ids: 11 unique evidence records
WARNING advisory-scope: Advisory research retained by design; check content and local pursuit notes before publishing.
PASS    public-copy: no blocked trust or confidentiality phrases found

Publication gate: degraded � 0 error(s), 1 warning(s)

```
