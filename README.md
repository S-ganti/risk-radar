# Risk Radar — India commodity and treasury decision support

[Live demo](https://s-ganti.github.io/risk-radar/) · 87 public-company profiles · 97 commodity markets · evidence-led stress and hedgeability analysis

Risk Radar connects a dated public-source trigger to the companies and commodities it may affect, shows the evidence and assumptions, and proposes a reviewable next action. It is a public decision-support demonstration—not a treasury management system, audit tool, investment product, or validated forecasting platform.

## Product shape

- **Radar:** ranked attention signals, evaluated rules, deadlines, and next actions.
- **Explore:** companies, commodity dependencies, hedgeability, and deep dives.
- **Scenarios:** directional stress, local portfolio CFaR, hedge diagnostics, and experimental model lenses.
- **Trust:** data health, evidence, methodology, model status, validation limits, and a dated market benchmark.

The strongest differentiator is India-specific evidence translation: policy or market trigger → exposed company/commodity → hedgeability and basis implication → traceable next action. Transaction capture, independent valuation, hedge-accounting postings, counterparty exposure, and execution belong in established TMS/risk platforms and are integration targets rather than features to imitate.

## Trust boundaries

- Public and secondary sources, manual marks, and estimates are explicitly labelled.
- The composite and pressure outputs are ranking indices, not likelihoods, capital measures, or booked limit utilisation.
- Alerts come only from evaluated rules with an observed value, limit, unit, and source.
- The five model lenses share inputs and are not independent votes. The UI reports their range and disagreement.
- No model-performance validation claim is made. Score history is retained, but governed outcome labels do not yet exist.
- Portfolio CSVs and hedge series are processed locally in the browser and are not uploaded.
- Hedge diagnostics follow the Ind AS 109 economic-relationship, credit-risk, and hedge-ratio framework. They do not apply a legacy bright-line pass/fail test or issue an accounting conclusion.

## Repository layout

```text
index.html                    application shell and current view renderers
app/models/core.js            pure, testable risk/model primitives
data/latest.json              dated market observations, vols, correlations, regime
data/history.json             retained score snapshots (up to two years)
data/financials.json          sourced public-company denominators
data/commodities.json         commodity and hedgeability reference
data/evidence-registry.json   evidence provenance and verification state
data/model-registry.json      model status, outputs, tests, and limitations
data/benchmarks.json          dated official-product capability comparison
data/health.json              generated publication-gate status
scripts/pipeline.py           deterministic market-data refresh
scripts/validate.py           schema, freshness, range, coverage, and copy gate
tests/                        JavaScript model and Python pipeline tests
```

The app remains framework-free. Model logic is being extracted incrementally from the legacy single-file renderer; a framework rewrite is intentionally out of scope.

## Local verification

```powershell
node --test tests/models.test.js
python -m unittest discover -s tests -p "test_*.py"
python scripts/validate.py --write-health
```

The data workflow is `fetch → normalize → validate → health manifest → staged pull request → reviewed deployment`. Failed validation must not publish new data.

## Market benchmark

The dated registry compares public capability claims from LSEG, Kyriba, FIS, IBSFINtech, and an LCH governance reference. It compares metric coverage—not model accuracy, because comparable vendor calibration or error statistics are not publicly disclosed on the reviewed product pages. Risk Radar currently adds local portfolio CFaR and hedge diagnostics as transparent foundations; it does not claim feature parity with enterprise platforms.

## Data and model caveats

Cost shares and qualitative ratings may be estimated where filings do not disclose enough detail. Market series have different lags and some fields are manually maintained. Scenario outputs use directional public-company mappings, not client ledgers. CFaR is a one-month variance–covariance normal approximation and excludes liquidity, basis, optionality, timing, and nonlinear instruments. Every output should be rechecked against current primary evidence and client-owned positions before use.

## License

No open-source license has been granted. Copyright remains with the repository owner pending an explicit licensing decision.
