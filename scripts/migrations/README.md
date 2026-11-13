# One-shot migrations

These scripts have already been applied to `index.html`. They are **not
re-runnable** — several of them assert on markup that no longer exists, which
is deliberate: a second run should fail loudly rather than corrupt the file.

They are kept because their docstrings are the record of *what changed and
why*, which is the same audit discipline the tool applies to its own numbers.
For a risk tool, "we removed the backtest" is a much weaker statement than
"we removed the backtest, and here is the code that generated the synthetic
outcomes it was reporting as evidence."

| Script | What it did |
|---|---|
| `build_companies.py` | Added 53 India-listed names with material commodity or FX exposure, each with a cost-base map, annual-report anchor, six-lens scores, advisory hooks and mitigants. |
| `patch_commodity_tab.py` | Replaced the hand-placed 33-node mind map and the thin detail panel with a family-grouped periodic table and a full fact sheet. |
| `patch_hedgeability.py` | Added the Hedgeability Matrix — per-company cost-base split and the cross-universe league table. |
| `patch_removals.py` | Removed the counterparty mock, the synthetic-outcome backtest, the structured-judgment model family, the circular GPD fit, the Alpha Vantage key path, and the probability language on an unfitted logistic. |
| `patch_removals2.py` | Second pass for the code paths the first left behind — including `COUNTERPARTIES`, which was feeding invented limit breaches into the real cockpit escalation queue. |

## What is still live

`../build_commodities.py` is **not** a migration. It is the source of truth for
`data/commodities.json` and should be edited and re-run whenever the commodity
reference sheet changes. It also emits `data/_commodities_block.js`, the
`DATA.commodities` literal for `index.html` — regenerate and splice that block
if the scoring layer changes.

Company data now lives in `index.html` and is edited there. `build_companies.py`
is retained for its content, not as a source: keeping a second copy of the same
data would only create drift.
