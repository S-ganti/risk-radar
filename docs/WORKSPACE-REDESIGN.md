# Risk Radar research workbench

## Visual atlas revision

The atlas layer replaces the long sidebar with five main views and a More menu. The dark blue-green canvas uses compact metrics and expandable company sections. Existing scores, models, mappings and sources remain intact.

Dependency tree is a separate tab with direct company inputs, company/product/input branches, and reverse commodity-to-company mapping. It reads the existing DATA.deps and DATA.products records, labels percentage denominators, handles unmapped companies, and provides node inspection, zoom and links to original briefs/profiles. Product inputs are not claimed to reconcile to the separate company-level estimates. Long trees scroll within the canvas.

Imported the complete tracked source tree of origin/main at 0a90326 (2026-11-11 data refresh). Replaces the earlier sparse directory redesign. Python engines, MCP servers, pipeline, market history, embedded company research, commodity reference data and all analytical panels are retained.

The presentation layer in app/radar-workbench.js and app/radar-workbench.css adds searchable company comparison, task-based navigation, company context links, section navigation inside briefs, and visible approximation guidance. The original company grid and hedgeability matrix remain in an expandable browser above each brief. Risk mathematics are unchanged.

Specialist contributions are additive, in contributions.html: model/dataset URLs, optional JSON, owner, company scope, version, dates, assumptions, evidence, review history, archive and JSON export/import. This is a local browser register, not a shared server or authenticated review system. Registration does not execute packages or alter scores. Shared storage, permissions and controlled execution remain future work.

Scores, cost shares, commodity dependencies and scenario impacts remain research approximations. Data refresh dates do not establish that every policy narrative or company assumption was reverified. Upstream caveats and diagnostic limitations are retained. This change does not establish model validation or a current legal review. No deployment is implied by local implementation.
