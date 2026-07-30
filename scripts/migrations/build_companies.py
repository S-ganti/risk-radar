#!/usr/bin/env python3
"""
Company universe extension -> splices into index.html.

The original universe was the Nifty large-cap list, which is where the market
cap is but not where the commodity risk is. Half of those names (banks, IT,
insurers) have no material input exposure at all, while the companies with the
sharpest, most nameable exposure - an airline that is 38% jet fuel, a battery
maker that is 58% lead, an adhesives business built on one imported monomer -
sit just below it. This adds those.

Every cost-base share is an estimate from segment disclosure and annual-report
commentary unless the anchor says otherwise. That framing is deliberate and
matches the existing disclosure pattern: estimates are labelled as estimates.

Tuple order:
  id, name, sector, deps, anchor,
  lens(fx, fin, conc, trans) each (score 1-5, note),
  watch [(theme, why, advisory action)],
  mitigants [..],
  prod (commodities the company sells - the green side of a shock)
run:  python scripts/build_companies.py
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "index.html")

NEW = []


def co(id, name, sector, deps, anchor, fx, fin, conc, trans, watch, mit, prod=None):
    NEW.append(dict(id=id, name=name, sector=sector, deps=deps, anchor=anchor,
                    lens=dict(fx=fx, fin=fin, conc=conc, trans=trans),
                    watch=watch, mit=mit, prod=prod or {}))


# --------------------------------------------------------------------------
# Aviation
# --------------------------------------------------------------------------
co("interglobe", "InterGlobe Aviation (IndiGo)", "Airlines",
   {"jet": 0.38, "elec": 0.01},
   "Fuel is the largest single line in an Indian carrier's cost base, typically 35-40% of operating cost (DGCA and company disclosure). Aircraft leases, a large share of maintenance and much of the spares bill are USD-denominated against almost entirely INR revenue - so a rupee move hits the P&L and the lease liability at the same time. Cost shares estimated from disclosed operating-cost breakdown.",
   (5, "USD lease liabilities, USD MRO and USD fuel against INR ticket revenue - the deepest structural mismatch in Indian corporate India"),
   (3, "Lease liabilities dominate the balance sheet; operating cash flow is strong but the obligation is long-dated and dollar-denominated"),
   (4, "Single fleet family, single home market, one dominant route network"),
   (3, "SAF blending mandates and EU ETS exposure on Europe-bound routes"),
   [("Commodity / FX", "ATF is 35-40% of cost with no Indian contract; the international leg is hedgeable through Singapore jet swaps but the fortnightly OMC price reset and state VAT mix are not. Historically Indian carriers hedge far less than global peers.",
     "Design a three-part ATF hedge programme: Singapore jet swap for the international leg, an explicit basis budget for the OMC reset lag, and a route-weighted state-VAT model. Pair it with the USD lease-liability hedge in one board paper - flagship engagement."),
    ("FX / regulatory", "USD lease and maintenance obligations under the April 2026 NDF prohibition and cancel-and-rebook bar.",
     "Re-paper the FX hedge book against the amended Master Direction; quantify the cost of the lost rebooking flexibility on a long-dated lease book.")],
   ["Market-leading share supports fare pass-through", "Young, fuel-efficient fleet", "Growing ancillary and cargo revenue"])

# --------------------------------------------------------------------------
# Oil, gas and utilities
# --------------------------------------------------------------------------
co("iocl", "Indian Oil Corporation", "Refining and marketing",
   {"dubai": 0.70, "crude": 0.04, "natgas": 0.02, "elec": 0.02},
   "Crude is essentially the entire cost base of a refiner. India's basket is roughly three-quarters Dubai/Oman-linked sour crude, so the correct benchmark is Dubai, not Brent or WTI. Retail fuel prices are administratively smoothed, which means the refining margin and the marketing margin move on different clocks.",
   (4, "USD crude purchases against INR-denominated administered retail revenue"),
   (3, "Large working capital swing with crude; subsidy receivable timing on LPG"),
   (3, "State-owned marketing network is a strength and a constraint"),
   (4, "Long-run demand transition plus a mandated ethanol and green-hydrogen build"),
   [("Commodity basis", "Hedging feedstock with WTI-settled MCX contracts leaves the Brent-Dubai and WTI-Dubai spreads unhedged - a spread that has moved several dollars a barrel through the Russian-discount era.",
     "Quantify the grade-basis residual in the existing hedge book and rebuild the programme on Dubai swaps; this is a defensible, self-contained diagnostic.")],
   ["Integrated refining-plus-marketing offsets margin swings", "Sovereign ownership supports funding cost"])

co("bpcl", "Bharat Petroleum", "Refining and marketing",
   {"dubai": 0.72, "crude": 0.04, "elec": 0.02},
   "Same structure as IOC: crude-dominated cost base, Dubai-linked basket, administratively smoothed retail pricing. LPG under-recovery is a government-receivable timing exposure rather than a market one.",
   (4, "USD crude bill against INR revenue"), (3, "Crude-driven working capital swings"),
   (3, "Concentrated in fuels; petchem diversification underway"),
   (4, "Refining asset transition risk over the long run"),
   [("Commodity / FX", "Combined crude and rupee exposure with a fortnightly retail price reset in between.",
     "Joint crude-plus-INR stress test showing the P&L path through the reset lag rather than at a point in time.")],
   ["Integrated marketing network", "Petrochemical expansion diversifies the margin base"])

co("gail", "GAIL (India)", "Gas transmission and petrochemicals",
   {"lng": 0.30, "apmgas": 0.18, "elec": 0.05, "ethylene": 0.04},
   "GAIL's gas book mixes long-term oil-indexed LNG contracts (including US Henry-Hub-linked volumes), domestic administered APM gas, and spot JKM cargoes. Those are three different pricing regimes inside one portfolio, and each needs a different hedge. The petrochemical arm adds a gas-to-polymer spread on top.",
   (4, "USD-denominated LNG contracts against INR domestic tariffs"),
   (2, "Regulated transmission tariffs provide a stable cash floor"),
   (3, "Dominant pipeline network but concentrated in one fuel"),
   (3, "Long-run gas demand is a transition beneficiary, then a stranded-asset question"),
   [("Commodity", "One gas book spanning Henry-Hub-indexed, Brent-slope-indexed and JKM-spot pricing. A single hedge instrument against all three is the common error and fails effectiveness testing.",
     "Decompose the gas book by pricing index and build a matched hedge per tranche - Henry Hub futures for US volumes, Brent for oil-indexed, JKM for spot. High-value and genuinely diagnostic."),
    ("Margin", "Petrochemical spread depends on the gas cost the transmission business passes through internally.",
     "Transfer-pricing and spread-hedging review across the two segments.")],
   ["Regulated tariff base", "Diversified across transmission, LPG and petrochemicals"])

co("petronet", "Petronet LNG", "LNG regasification",
   {"lng": 0.72, "elec": 0.03},
   "Long-term Qatari and Australian contracts on Brent-slope pricing plus spot JKM cargoes. The tolling model insulates a large share of earnings, but the marketing margin on own-account cargoes carries direct price and volume risk - Indian buyers step away above roughly $10-12/MMBtu.",
   (4, "USD LNG purchase obligations against INR regasification revenue"),
   (2, "Take-or-pay structures provide contracted cash flow"),
   (4, "Two terminals, a narrow customer set and a single commodity"),
   (3, "Gas is a transition fuel with a finite runway"),
   [("Commodity / volume", "Spot JKM exposure compounds with demand destruction: when the price rises, Indian offtake falls, so price and volume losses arrive together rather than offsetting.",
     "Model the joint price-volume distribution rather than price alone - a Cash-Flow-at-Risk framing that a tolling-model treasury has usually never seen.")],
   ["Take-or-pay contracts", "Dominant regasification market share"])

co("gujgas", "Gujarat Gas", "City gas distribution",
   {"lng": 0.42, "apmgas": 0.22, "elec": 0.03},
   "Gujarat Gas serves an industrial customer base - Morbi ceramics above all - that switches to propane or coal gasifiers when spot LNG runs hot. So the exposure is not just cost but volume: a price spike destroys the demand it was meant to be passed through to.",
   (4, "USD spot LNG purchases against INR industrial tariffs"),
   (2, "Asset-light distribution with regulated returns on part of the book"),
   (5, "Heavy concentration in one industrial cluster with a ready substitute fuel"),
   (3, "CNG demand grows; industrial demand is exposed to fuel switching"),
   [("Commodity / volume", "Spot LNG price and Morbi volume are inversely linked, so a hedge on price alone leaves the larger exposure untouched.",
     "Build a switching-threshold model - the LNG price at which ceramic customers move to propane - and hedge the volume-weighted exposure below it. Directly actionable and unusual."),
    ("Concentration", "Single-cluster customer concentration is a credit and volume risk at once.",
     "Customer-concentration and receivables stress test alongside the commodity work.")],
   ["Regulated city gas exclusivity in its geographies", "Growing CNG segment is less price-elastic"])

co("igl", "Indraprastha Gas", "City gas distribution",
   {"apmgas": 0.42, "lng": 0.18, "elec": 0.03},
   "IGL's margin depends on how much cheap administered APM gas it is allocated versus how much it must buy at market rates. That allocation has been cut repeatedly, and each cut is a direct margin event with no market instrument against it.",
   (3, "Partial USD exposure on the non-APM slice"),
   (2, "Strong cash generation, low leverage"),
   (4, "Single-city concentration with regulated tariffs"),
   (3, "EV adoption in Delhi NCR erodes the CNG volume base over time"),
   [("Regulatory", "APM gas allocation cuts are the dominant margin driver and are entirely administrative - no hedge exists.",
     "Scenario-model allocation cuts against the tariff pass-through mechanism; this is policy risk quantification, not hedging, and it is what the board actually needs.")],
   ["Regulated exclusivity in the NCR", "Strong balance sheet"])

co("tatapower", "Tata Power", "Power generation and distribution",
   {"coal": 0.30, "drybulk": 0.05, "poly": 0.04, "elec": 0.02},
   "The Mundra imported-coal plant has been the recurring loss centre because the tariff was bid on a coal price assumption Indonesia later legislated away. The renewables and solar-manufacturing arms carry a polysilicon and module-cost exposure instead.",
   (4, "USD coal imports and USD-denominated equipment against INR tariffs"),
   (3, "Capex-heavy renewable build programme"),
   (3, "Diversified across generation, distribution and renewables"),
   (2, "Best-positioned Indian utility for the transition"),
   [("Commodity", "Imported coal at Mundra plus dry bulk freight, both USD, against a regulated INR tariff with limited pass-through.",
     "Landed-cost hedge combining Newcastle coal (calorific-adjusted for Indonesian grade) and a Capesize FFA - the freight leg alone is often 20% of landed cost and is almost never hedged."),
    ("Transition", "Solar manufacturing exposes the group to polysilicon and ALMM policy.",
     "Module cost-curve and policy scenario pack for the manufacturing arm.")],
   ["Diversified generation mix", "Regulated distribution provides a cash floor", "Leading renewable portfolio"])

co("adanipower", "Adani Power", "Thermal power generation",
   {"coal": 0.48, "drybulk": 0.08, "elec": 0.02},
   "Predominantly imported-coal generation, so landed cost is the entire story: seaborne coal price, calorific grade, ocean freight and the rupee, against PPAs whose fuel pass-through is contested and slow.",
   (5, "Coal and freight in USD against INR PPA tariffs with contested pass-through"),
   (4, "High leverage against long-dated PPA cash flows"),
   (5, "Single fuel, single technology"),
   (4, "Thermal generation faces a structural transition and now a CCTS carbon cost"),
   [("Commodity", "Imported coal plus dry bulk freight is the dominant cost, both USD, both hedgeable, neither typically hedged.",
     "Calorific-adjusted Newcastle hedge plus Capesize FFA overlay, sized against actual annual tonnage. The clearest unexploited hedge in the Indian power sector."),
    ("Regulatory", "CCTS obligated-entity status adds a domestic carbon cost from the 2026 compliance cycle.",
     "CCTS baseline and certificate-requirement modelling - most obligated entities have not yet quantified it.")],
   ["Long-dated PPAs", "Supercritical fleet efficiency"])

co("oilindia", "Oil India", "Oil and gas production",
   {"diesel": 0.05, "steel": 0.04, "elec": 0.03},
   "An upstream producer, so it is long crude and gas - a price spike is an earnings gain, not a cost. The windfall levy on domestic crude, imposed and withdrawn episodically since 2022, is the policy risk that cuts the other way.",
   (2, "USD-linked realisations against INR costs - a natural long"),
   (2, "Strong cash generation"), (4, "Single upstream basin concentration"),
   (4, "Long-run oil demand transition"),
   [("Policy", "The special additional excise duty on domestic crude production converts a price gain into a fiscal transfer at unpredictable thresholds.",
     "Model the effective realisation ceiling created by the levy - it caps the upside in a way that no price forecast captures.")],
   ["Natural long position in a rising commodity market", "Sovereign ownership"],
   prod={"crude": 0.62, "natgas": 0.22})

# --------------------------------------------------------------------------
# Metals and mining
# --------------------------------------------------------------------------
co("vedanta", "Vedanta", "Diversified natural resources",
   {"alumina": 0.11, "coal": 0.14, "elec": 0.09, "bauxite": 0.04, "caustic": 0.03},
   "A basket of long positions - aluminium, zinc, silver, oil, iron ore - against a short position in coal and power. That makes group-level commodity risk a net exposure across correlated markets rather than a sum of individual ones, which is exactly the case a copula model is for.",
   (4, "USD-linked LME realisations against INR costs and a large USD debt stack"),
   (5, "High holding-company leverage with a demanding refinancing schedule"),
   (3, "Genuinely diversified across metals, oil and power"),
   (3, "Aluminium is power-intensive and now carbon-exposed"),
   [("Commodity portfolio", "Long aluminium, zinc, silver, oil and iron ore; short coal and power. The correlations between those legs determine the true group exposure, and a sum-of-parts view materially overstates it.",
     "Portfolio-level VaR and Expected Shortfall across the whole commodity book using a real correlation matrix - the single most defensible piece of quantitative work available on this name."),
    ("Financial", "Holding-company leverage against commodity-cyclical cash flows.",
     "Cash-Flow-at-Risk against the debt service schedule - link the commodity distribution directly to covenant headroom.")],
   ["Diversification across uncorrelated metal cycles", "Low-cost zinc and aluminium assets"],
   prod={"alum": 0.30, "zinc": 0.18, "crude": 0.08, "silver": 0.04, "ironore": 0.04})

co("hindzinc", "Hindustan Zinc", "Zinc, lead and silver mining",
   {"coal": 0.10, "elec": 0.08, "diesel": 0.05},
   "One of the world's lowest-cost zinc producers, and structurally long three metals at once - zinc, lead and by-product silver. Silver has become a material share of earnings as solar demand lifted the price.",
   (3, "USD-linked LME and silver realisations against INR costs - a natural long"),
   (2, "Cash-generative with low debt"),
   (4, "Single mining complex in Rajasthan"),
   (2, "Zinc for galvanising and silver for solar are both transition-supported"),
   [("Commodity portfolio", "Three correlated long positions plus a coal and power short. Silver's rising earnings share changes the risk profile from a zinc story to a precious-metals-linked one.",
     "Multi-metal exposure decomposition and a producer-side hedge policy - the hedge direction here is short, which most Indian hedge policies are not written for.")],
   ["Lowest-quartile cost position", "Silver by-product credit lowers effective zinc cost"],
   prod={"zinc": 0.62, "silver": 0.18, "lead": 0.12})

co("nalco", "National Aluminium", "Alumina and aluminium",
   {"coal": 0.17, "elec": 0.14, "caustic": 0.06, "diesel": 0.03},
   "Integrated from captive bauxite through alumina to metal, which makes it one of the few Indian smelters insulated from alumina price spikes - and a beneficiary of them, since it exports surplus alumina.",
   (3, "USD-linked LME and alumina export realisations against INR costs"),
   (1, "Debt-free with strong cash generation"),
   (4, "Single commodity chain, single location"),
   (3, "Power-intensive smelting faces a carbon cost under CCTS"),
   [("Commodity", "Long both alumina and aluminium with captive bauxite - the integrated position means an alumina spike is a gain, the opposite of a non-integrated smelter.",
     "Integrated-margin hedging: the exposure to hedge is the alumina-to-metal spread and the power cost, not the metal price alone.")],
   ["Full backward integration to captive bauxite", "Debt-free balance sheet"],
   prod={"alumina": 0.38, "alum": 0.52})

co("sail", "Steel Authority of India", "Steelmaking",
   {"metcoal": 0.27, "elec": 0.06, "ferroalloy": 0.03, "ironore": 0.02},
   "Integrated blast-furnace producer with captive iron ore, so the exposure concentrates almost entirely in imported coking coal - roughly 85% Australian-origin - and in the rupee that pays for it.",
   (4, "USD coking coal imports against largely INR revenue"),
   (4, "High working capital intensity and legacy leverage"),
   (5, "Single commodity, blast-furnace route only"),
   (4, "Blast-furnace route is the hardest steel technology to decarbonise; CBAM and CCTS both apply"),
   [("Commodity", "Coking coal at ~85% import dependence with a well-matched SGX hedge available and unused.",
     "SGX premium HCC hedge programme with iron-ore overlay to construct a synthetic steel-spread hedge. The basis here is unusually small - this is the best-matched offshore hedge available to any Indian heavy industry."),
    ("Regulatory", "CCTS obligated entity plus CBAM on any EU-bound tonnes.",
     "Dual carbon-cost model - EU certificate liability and domestic CCTS obligation in one framework.")],
   ["Captive iron ore", "Domestic demand growth from infrastructure spending"],
   prod={"steel": 0.88})

co("jindalsteel", "Jindal Steel & Power", "Steelmaking",
   {"metcoal": 0.23, "ironore": 0.11, "elec": 0.06},
   "Partially integrated - captive coal and some iron ore - but still a large coking-coal importer. Spot iron ore purchases add a second unhedged input on top.",
   (4, "USD coking coal against domestic INR steel realisations"),
   (3, "Deleveraged materially but capex cycle is active"),
   (4, "Single commodity chain"),
   (4, "Blast-furnace transition exposure plus CBAM and CCTS"),
   [("Commodity", "Dual exposure to coking coal and spot iron ore, both hedgeable on SGX, neither typically hedged.",
     "Dual-commodity hedge overlay constructed as a steel-spread position rather than two independent hedges - materially lower cost and better effectiveness.")],
   ["Partial raw material integration", "Modern capacity with competitive conversion cost"],
   prod={"steel": 0.82})

# --------------------------------------------------------------------------
# Tyres and auto components
# --------------------------------------------------------------------------
co("apollotyre", "Apollo Tyres", "Tyres",
   {"natrub": 0.23, "carbonblack": 0.11, "sbr": 0.09, "crude": 0.02, "container": 0.02},
   "Roughly half the raw material bill is rubber - natural and synthetic - with carbon black adding another tenth. Natural rubber is the rare Indian input with a genuinely well-matched offshore hedge in SICOM TSR20, and European operations add a EUR leg.",
   (4, "USD rubber and carbon black inputs, EUR revenue from European operations, INR cost base"),
   (3, "Capex cycle in Europe and India"),
   (3, "Concentrated in one product category across two geographies"),
   (3, "EUDR applies to natural rubber for EU-bound goods"),
   [("Commodity", "Natural rubber is roughly a quarter of raw material cost and SICOM TSR20 matches the imported grade closely - one of the cleanest hedges available to an Indian manufacturer. The Kerala domestic leg needs a partial ratio, not a full one.",
     "Build a procurement-mix-weighted hedge ratio across imported TSR20 and domestic RSS4, with the carbon-black feedstock lag modelled alongside it. Concrete and quickly deliverable."),
    ("Regulatory", "EUDR traceability on natural rubber for European sales from December 2026.",
     "EUDR sourcing-traceability readiness review with cost-of-compliance modelling.")],
   ["Pricing power in the replacement market", "European operations diversify the demand cycle"])

co("mrf", "MRF", "Tyres",
   {"natrub": 0.25, "carbonblack": 0.11, "sbr": 0.08, "crude": 0.02},
   "The largest Indian tyre maker by revenue with the same rubber-plus-carbon-black cost structure. Historically conservative on derivatives, which makes the unhedged input exposure larger in absolute rupee terms than any peer.",
   (3, "USD rubber and carbon black inputs against a largely domestic INR revenue base"),
   (1, "Very strong balance sheet, minimal debt"),
   (3, "Single product category, domestic-heavy"),
   (2, "Replacement-market demand is resilient"),
   [("Commodity", "Largest absolute unhedged natural rubber exposure in the Indian tyre sector.",
     "Hedge-policy design from a standing start: board mandate, instrument authorisation, effectiveness testing framework. A greenfield hedge programme rather than an optimisation.")],
   ["Premium brand pricing power", "Fortress balance sheet absorbs input swings"])

co("balkrishna", "Balkrishna Industries", "Off-highway tyres",
   {"natrub": 0.21, "carbonblack": 0.12, "sbr": 0.08, "container": 0.04},
   "An export business - the large majority of sales are outside India, mostly Europe - so it is short USD-priced inputs and long EUR and USD receivables. That partial natural offset is rarely quantified, and the residual is what should actually be hedged.",
   (5, "EUR and USD receivables against USD-priced inputs and an INR cost base - a three-currency book"),
   (2, "Low leverage, strong margins"),
   (4, "Concentrated in one niche category and one export region"),
   (3, "EUDR on natural rubber; European agricultural demand cycle"),
   [("FX", "A three-currency book where input purchases in USD partly offset receivables in USD and EUR. Hedging the gross positions rather than the net residual is expensive and common.",
     "Net-exposure FX programme: quantify the natural offset, hedge only the residual, and re-paper it under the April 2026 rules. Immediately measurable cost saving."),
    ("Commodity", "Rubber and carbon black exposure alongside the currency book.",
     "Integrated commodity-plus-FX hedge rather than two separate programmes.")],
   ["Niche market leadership with pricing power", "Export diversification across geographies"])

# --------------------------------------------------------------------------
# Fertiliser and chemicals
# --------------------------------------------------------------------------
co("coromandel", "Coromandel International", "Fertilisers and crop protection",
   {"dap": 0.19, "ammonia": 0.15, "sulphur": 0.10, "potash": 0.08, "drybulk": 0.04},
   "A phosphatic fertiliser maker squeezed between internationally set input costs - phosphoric acid, ammonia, sulphur, all imported and USD-priced - and a domestically controlled maximum retail price, with a Nutrient Based Subsidy that adjusts on a lag. When world prices spike, the company funds the gap until the subsidy catches up.",
   (5, "Fully USD-priced imported inputs against an INR price ceiling set by government"),
   (4, "Subsidy receivable timing drives large working capital swings and short-term borrowing"),
   (4, "Concentrated in phosphatics with a narrow supplier set"),
   (3, "Nutrient-use-efficiency policy shifts and the move toward nano and specialty products"),
   [("Commodity / policy", "The exposure is a squeeze between an international landed cost and an administered selling price, buffered by a subsidy rate revised with a lag. That lag is the actual risk and it is quantifiable.",
     "Model the subsidy-lag working capital requirement across input-price scenarios, and size the short-term funding line against it. This converts a vague policy worry into a treasury number - exactly the deliverable a fertiliser CFO wants."),
    ("Commodity", "Ammonia, sulphur and phosphate all move with gas and refinery runs, plus dry bulk freight on top.",
     "Landed-cost decomposition with a partial hedge on the components that have instruments - ammonia swaps and Capesize FFAs - and an explicit unhedgeable residual.")],
   ["Backward integration into phosphoric acid", "Crop protection segment diversifies the earnings base"])

co("chambal", "Chambal Fertilisers", "Urea and agri-inputs",
   {"natgas": 0.38, "potash": 0.06, "dap": 0.05},
   "A urea producer, so roughly 25-28 MMBtu of natural gas per tonne is the cost base - but gas is supplied under a pooled administered mechanism and urea sells at a statutorily fixed farmgate price with subsidy covering the gap. Almost every economic variable is administered, which changes the nature of the risk entirely.",
   (3, "Partial USD exposure through imported gas in the pool and traded fertiliser"),
   (4, "Subsidy payment cycle drives working capital"),
   (4, "Single product concentration"),
   (3, "Green ammonia and energy-efficiency norms reshape the cost curve over time"),
   [("Policy", "Both the input price and the output price are administered. The genuine exposure is the subsidy release cycle and the gas pooling formula, neither of which is a market risk.",
     "Split the book into administered and market legs and model each properly. Treating the whole thing as a gas-price exposure produces answers a CFO will immediately recognise as wrong - and getting this distinction right is what establishes credibility on this account.")],
   ["Efficient plants under the gas pooling mechanism", "Trading and crop protection diversification"])

co("srf", "SRF", "Specialty chemicals and packaging films",
   {"fluorspar": 0.13, "methanol": 0.05, "elec": 0.06, "pta": 0.05, "crude": 0.03},
   "Fluorspar sits at the head of the fluorochemicals chain and India has essentially no domestic supply - it comes from China, Mexico, South Africa and Vietnam with no hedge available. The refrigerant business also carries a Kigali HFC phase-down schedule that is a demand risk, not a cost one.",
   (4, "USD-priced imported inputs with substantial export revenue - a partial natural offset worth netting"),
   (2, "Comfortable leverage against a heavy capex programme"),
   (3, "Three distinct segments: chemicals, packaging films, technical textiles"),
   (4, "HFC phase-down under Kigali restructures the refrigerant portfolio over the next decade"),
   [("Supply chain", "Fluorspar is unhedgeable, import-dependent and concentrated in China. Availability, not price, is the risk that materialises.",
     "Supplier-concentration mapping with a qualification-timeline model for alternative sources, plus inventory policy sized against a 60-90 day interruption."),
    ("Transition", "Kigali phase-down changes which refrigerants can be sold and when.",
     "Product-portfolio transition model linking the phase-down schedule to segment revenue - a strategy-adjacent piece that opens a wider mandate.")],
   ["Diversified across three segments", "Strong position in fluorochemical intermediates"])

co("tatachem", "Tata Chemicals", "Soda ash and specialty chemicals",
   {"coal": 0.13, "elec": 0.10, "limestone": 0.05, "natgas": 0.05},
   "A soda ash producer - so it is long the price, with energy as the dominant input. Global operations in the UK, US and Kenya add currency and energy-regime exposure in three more jurisdictions.",
   (4, "GBP, USD and KES operations alongside the Indian base"),
   (3, "Moderate leverage with a capex programme"),
   (3, "Soda ash concentration with specialty diversification"),
   (3, "Energy-intensive production faces CCTS in India and ETS in the UK"),
   [("Commodity", "Long soda ash, short energy, across four currency zones with different power markets and carbon regimes.",
     "Multi-jurisdiction energy-cost and carbon-cost model; the UK ETS and Indian CCTS obligations need to sit in one framework."),
    ("Demand", "Solar glass has become a growth driver for soda ash demand.",
     "Demand-scenario work linking Indian and global solar build-out to the soda ash order book.")],
   ["Natural long position in a tightening soda ash market", "Geographic diversification"],
   prod={"sodaash": 0.55})

co("deepaknitrite", "Deepak Nitrite", "Intermediates and phenolics",
   {"benzene": 0.21, "propylene": 0.08, "methanol": 0.05, "elec": 0.04},
   "Benzene is the dominant input and prices off FOB Korea assessments with no derivative available. The phenol-acetone plant substituted a large share of India's imports, which turned an import-cost exposure into a domestic-spread exposure.",
   (4, "USD-priced aromatic feedstocks against a mix of domestic and export sales"),
   (2, "Low leverage"),
   (3, "Concentrated in the aromatics chain"),
   (2, "Import substitution supports the domestic position"),
   [("Commodity", "Benzene at over a fifth of cost with no hedging instrument anywhere - the exposure is a landed-cost formula.",
     "Back-to-back pricing review: match input formula resets to customer contract resets so the spread, not the level, is what the P&L carries. A contractual solution where no financial one exists.")],
   ["Import substitution position in phenol", "Integrated aromatics chain"])

co("upl", "UPL", "Crop protection",
   {"benzene": 0.07, "methanol": 0.05, "phenol": 0.04, "elec": 0.03, "container": 0.03},
   "A global agrochemicals business with revenue in dozens of currencies, manufacturing concentrated in India and China, and a Latin American receivables book that carries both FX and credit risk on a long collection cycle.",
   (5, "Revenue across many emerging-market currencies against USD debt and INR costs - one of the most complex FX books in Indian corporate India"),
   (5, "High leverage against a working-capital-intensive Latin American receivables cycle"),
   (4, "Latin American concentration in both revenue and credit exposure"),
   (3, "Regulatory pressure on legacy actives in Europe"),
   [("FX / credit", "Brazilian and Argentine receivables carry currency risk and counterparty risk on the same long cycle, against USD-denominated debt.",
     "Combined FX-and-credit exposure model on the Latin American book, with a hedging cost-benefit analysis per currency - some of those hedges cost more than the risk they remove, which is worth demonstrating."),
    ("Financial", "Leverage against a volatile agrochemical cycle.",
     "Cash-Flow-at-Risk against covenant thresholds.")],
   ["Global scale and distribution reach", "Diversified active-ingredient portfolio"])

co("pidilite", "Pidilite Industries", "Adhesives and construction chemicals",
   {"vam": 0.15, "plastics": 0.06, "crude": 0.03, "elec": 0.02},
   "Vinyl acetate monomer is the single largest input and India imports 100% of it, from a global market with very little redundancy - plant outages in Taiwan, the US or Saudi Arabia have moved the price by multiples. There is no derivative anywhere in the world for VAM.",
   (4, "Fully USD-denominated imported VAM against domestic INR revenue"),
   (1, "Net cash, very strong balance sheet"),
   (5, "Extreme single-input concentration with no substitute and no hedge"),
   (2, "Construction and repair demand is structurally supported"),
   [("Commodity / concentration", "A single unhedgeable imported monomer is the largest input line. This is the textbook case for a board-level input-concentration metric - and Pidilite survives it only because it has the brand pricing power to pass it through. A client with the same concentration and no pricing power would not.",
     "Input-concentration diagnostic: quantify the Herfindahl of the input book, the pass-through lag actually achieved historically, and the inventory cover needed to bridge a supply interruption. Then generalise the framework to the client's whole portfolio - this is how a single finding becomes a standing mandate.")],
   ["Dominant brand with demonstrated pricing power", "Net cash balance sheet absorbs input spikes"])

co("bergerpaints", "Berger Paints", "Paints and coatings",
   {"tio2": 0.16, "plastics": 0.13, "crude": 0.02, "elec": 0.02},
   "Titanium dioxide is typically the largest single raw material in a paint formulation and India imports the majority. Anti-dumping duty on Chinese TiO2 cuts against paint makers - it protects domestic pigment producers and raises the coating industry's cost.",
   (3, "USD-priced pigment and resin inputs against domestic INR revenue"),
   (2, "Moderate leverage"),
   (3, "Decorative paints concentration in a market facing new entrants"),
   (2, "Water-based and low-VOC formulation shift"),
   [("Commodity / policy", "TiO2 is unhedgeable and its Indian landed cost is set as much by anti-dumping duty decisions as by the world price.",
     "Trade-remedy watch and duty-scenario model for the input basket - a policy exposure most paint treasuries track informally if at all.")],
   ["Established distribution network", "Broad product portfolio"])

# --------------------------------------------------------------------------
# Consumer and agri
# --------------------------------------------------------------------------
co("britannia", "Britannia Industries", "Packaged foods",
   {"wheat": 0.15, "palm": 0.10, "sugar": 0.08, "milk": 0.07, "plastics": 0.05},
   "A four-commodity basket - wheat, palm oil, sugar and dairy - of which only palm has any hedging venue and that one is offshore, MYR-denominated and periodically suspended domestically. Wheat and sugar are policy-priced; dairy is unhedgeable.",
   (3, "USD and MYR palm purchases; the rest is domestic INR"),
   (1, "Net cash"),
   (3, "Biscuits dominate the portfolio"),
   (2, "Rural demand cyclicality tied to monsoon"),
   [("Commodity", "Four major inputs, one partial hedge. The realistic risk framework here is not hedging but forward procurement, formulation flexibility and pricing cadence.",
     "Input-basket volatility model feeding a pricing-decision calendar: how much input inflation, over how long, before a price increase is required. That is the actual decision an FMCG board makes.")],
   ["Strong brand pricing power", "Net cash balance sheet"])

co("marico", "Marico", "Consumer staples",
   {"copra": 0.21, "palm": 0.08, "crude": 0.04, "plastics": 0.06},
   "Copra is the largest single input and there is no copra derivative anywhere in the world. Marico buys a very large share of India's edible-grade copra, so it is exposed to the price and large enough to move it - a rare combination that makes procurement timing itself a market-impact problem.",
   (3, "Largely domestic INR inputs with a USD palm leg and international operations"),
   (1, "Net cash"),
   (4, "Heavy dependence on one input and a small number of hero brands"),
   (2, "Premiumisation and category expansion underway"),
   [("Commodity / concentration", "No hedge exists for copra anywhere. Procurement timing across the two harvest peaks, storage economics and shelf pricing are the only levers, and the company's own buying moves the price it pays.",
     "Procurement-optimisation model across harvest seasonality and storage cost, with an explicit market-impact term. This is an operations-research problem dressed as a commodity problem, and framing it that way is what makes it solvable."),
    ("Commodity", "Palm oil adds a second, hedgeable-but-awkward edible oil exposure alongside copra.",
     "Combined edible-oil basket view rather than two separate exposures.")],
   ["Category-leading brands with pricing power", "Net cash balance sheet"])

co("godrejcp", "Godrej Consumer Products", "Home and personal care",
   {"palm": 0.19, "plastics": 0.06, "sodaash": 0.03, "crude": 0.02},
   "Palm oil and its derivatives dominate the soap cost base, and the company also owns palm plantations in Indonesia - so it sits on both sides of the same commodity, an internal offset that group treasury should be netting rather than hedging twice.",
   (4, "USD and IDR palm exposure, African currency operations, INR domestic base"),
   (2, "Moderate leverage"),
   (3, "Soaps and household insecticides dominate"),
   (3, "EUDR applies to palm for any EU-bound flow"),
   [("Commodity", "Long palm through Indonesian plantations and short palm through Indian soap manufacturing. The group's true exposure is the residual, and hedging the legs separately doubles the cost.",
     "Group-level net commodity exposure consolidation across the plantation and manufacturing arms - immediate and quantifiable hedging cost reduction."),
    ("FX", "African subsidiary currencies have delivered repeated translation shocks.",
     "Emerging-market translation exposure review with a hedge-versus-accept cost analysis.")],
   ["Vertical integration into palm plantations", "Diversified geographic footprint"])

co("awl", "AWL Agri Business", "Edible oils and foods",
   {"palm": 0.40, "soyoil": 0.17, "sunoil": 0.08, "plastics": 0.04, "drybulk": 0.03},
   "Effectively a physical commodity trading business with a consumer brand attached. Edible oil is around 60% import-dependent for India, the inventory position is large relative to margin, and SEBI's suspension of agricultural derivatives removed the domestic hedging venue for years.",
   (5, "USD and MYR oil purchases financed short-term against INR sales - the classic importer squeeze"),
   (4, "Very high inventory and working capital intensity relative to margin"),
   (4, "Edible oil dominates the revenue mix"),
   (3, "EUDR on palm for any export flow; biofuel policy shifts in Indonesia"),
   [("Commodity", "Thin margins on a large inventory position, in a commodity where the Indian derivative market has been switched off by the regulator and the offshore alternative carries currency, grade and origin basis.",
     "Full basis decomposition of the palm hedge - MYR currency leg, crude-versus-refined grade, Malaysian-versus-Indonesian origin, and regulatory availability - then size the hedgeable share honestly. Most clients believe they are hedged; this shows what they actually carry."),
    ("Financial", "Inventory value swings dominate earnings and drive the working capital line.",
     "Inventory-at-Risk model linking price distribution to funding requirement.")],
   ["Scale advantage in procurement", "Branded portfolio supports margin over pure trading"])

co("tataconsumer", "Tata Consumer Products", "Beverages and foods",
   {"tea": 0.17, "coffee": 0.08, "plastics": 0.04, "sugar": 0.03},
   "Tea is bought at auction with enormous quality dispersion, so there is no single price to hedge. Coffee is different - it is liquid on ICE, and the group has both a plantation side that is long and a roasting side that is short, an internal offset rarely netted.",
   (3, "USD and GBP exposure through international brands, INR domestic base"),
   (2, "Comfortable leverage"),
   (3, "Tea and salt dominate the domestic portfolio"),
   (2, "Premiumisation and packaged-foods expansion"),
   [("Commodity", "Coffee is genuinely hedgeable on ICE and the group is naturally long through plantations and short through roasting. Netting first, hedging second is the cheaper order of operations.",
     "Internal net-position consolidation across plantation and branded businesses, then a residual hedge with an explicit direction mandate - hedge policies that assume a short position get this wrong."),
    ("Regulatory", "EUDR applies to coffee for EU-bound flows from December 2026.",
     "EUDR traceability readiness for the coffee export chain.")],
   ["Diversified beverage and food portfolio", "Backward integration into plantations"])

co("varunbev", "Varun Beverages", "Beverages bottling",
   {"sugar": 0.15, "plastics": 0.14, "alum": 0.05, "elec": 0.04},
   "Sugar and PET resin are the two dominant inputs, with aluminium cans a growing third as packaging mix shifts. Sugar is policy-priced in India, PET tracks PTA and crude, and aluminium is fully hedgeable on MCX - three inputs with three completely different risk characters.",
   (3, "International territory operations in Africa alongside the INR domestic base"),
   (3, "Capex-heavy expansion programme"),
   (4, "Single-franchise concentration with strong seasonality"),
   (3, "Sugar-content regulation and plastic packaging EPR rules"),
   [("Commodity", "Three inputs with three different hedgeability profiles: sugar is administered, PET is index-linked, aluminium has a liquid MCX contract nobody uses.",
     "Hedgeability triage across the input basket - hedge what is hedgeable (aluminium), contract for what is not (PET formula pricing), and scenario-model the administered leg (sugar). A clean demonstration of the framework."),
    ("Regulatory", "Extended Producer Responsibility obligations on plastic packaging.",
     "EPR compliance cost model as packaging mix shifts between PET, glass and cans.")],
   ["Exclusive bottling territories", "Growing international footprint"])

co("balrampur", "Balrampur Chini Mills", "Sugar and ethanol",
   {"coal": 0.04, "elec": 0.03, "diesel": 0.02},
   "A sugar mill whose economics are now set almost entirely by government: the Fair and Remunerative Price for cane on the input side, the minimum selling price and export quota for sugar, and the notified procurement price for ethanol by feedstock route. Ethanol has become the dominant earnings driver and it is 100% administratively priced.",
   (1, "Almost entirely domestic INR"),
   (3, "Cane payment obligations create a seasonal working capital cycle"),
   (5, "Single crop, single geography, single set of policy levers"),
   (3, "Ethanol blending policy is both the opportunity and the concentration risk"),
   [("Policy", "Every material price in this business - cane, sugar, ethanol - is administered. There is no commodity hedge to recommend, and saying so plainly is more valuable than proposing one.",
     "Policy-scenario model across FRP revisions, MSP changes, export quota decisions and ethanol procurement-price notifications, mapped to the mill's feedstock mix. Delivered as a board-level sensitivity pack rather than a hedging proposal."),
    ("Concentration", "Ethanol is now the earnings engine and depends on one procurement decision each year.",
     "Single-point-of-policy-failure analysis with a diversification options review.")],
   ["Integrated sugar, ethanol and cogeneration", "Efficient cane catchment in Uttar Pradesh"],
   prod={"sugar": 0.60, "ethanol": 0.28})

# --------------------------------------------------------------------------
# Electricals, electronics and components
# --------------------------------------------------------------------------
co("polycab", "Polycab India", "Wires and cables",
   {"copper": 0.41, "alum": 0.09, "pvc": 0.10, "plastics": 0.04},
   "Copper alone is over 40% of the cost base - one of the highest single-commodity intensities in Indian manufacturing - and MCX offers a liquid INR contract against it. The order book is typically priced with a copper pass-through, which means the real exposure is the lag between purchase and repricing, not the price level.",
   (3, "USD-linked LME copper flows through MCX pricing; largely INR revenue"),
   (1, "Net cash, strong working capital discipline"),
   (3, "Wires and cables dominate the mix"),
   (2, "Electrification and grid capex are structural tailwinds"),
   [("Commodity", "Copper at over 40% of cost with a liquid onshore INR hedge available. The exposure that matters is the timing gap between inventory purchase and contract repricing, which a simple price hedge does not address.",
     "Inventory-timing hedge design: match hedge tenor to the actual purchase-to-invoice lag rather than to the fiscal year. Also worth flagging that MCX copper bundles metal and currency risk - a client already hedging USDINR separately may be double-counting."),
    ("Commodity", "PVC compounds add a second unhedgeable input on top.",
     "Formula-pricing review for the PVC leg where no instrument exists.")],
   ["Copper pass-through clauses in most contracts", "Net cash balance sheet", "Market leadership supports pricing"])

co("havells", "Havells India", "Electrical consumer goods",
   {"copper": 0.19, "alum": 0.08, "plastics": 0.08, "steel": 0.06},
   "A diversified electricals portfolio where copper and aluminium drive the cable and motor lines while plastics and steel drive appliances. Consumer-facing pricing means pass-through is slower than in the industrial cable business.",
   (3, "USD-linked metal inputs against domestic INR consumer revenue"),
   (1, "Net cash"), (2, "Broad product portfolio"),
   (2, "Energy-efficiency standards drive product refresh"),
   [("Commodity", "Metal inputs are hedgeable on MCX but consumer pricing cadence is slower than industrial pass-through, so the margin absorbs more of the move.",
     "Pass-through-lag quantification by segment, feeding a segment-specific hedge ratio rather than one company-wide ratio.")],
   ["Diversified portfolio across industrial and consumer", "Strong brand and distribution"])

co("dixon", "Dixon Technologies", "Electronics manufacturing",
   {"chips": 0.21, "plastics": 0.10, "copper": 0.06, "steel": 0.04},
   "Contract manufacturing on thin margins, which makes input availability a bigger risk than input price - a component shortage stops a line, and unbuilt units are lost revenue rather than expensive cost. Most components are imported and USD-priced against INR customer contracts.",
   (4, "USD component imports on thin INR-denominated conversion margins"),
   (3, "Working-capital-intensive with a heavy capex programme"),
   (4, "Customer concentration is high in contract manufacturing"),
   (3, "PLI scheme dependence and the domestic value-addition trajectory"),
   [("Supply chain", "On a thin conversion margin, a small input-cost move or a component shortage consumes the entire margin. This is business-interruption risk more than price risk.",
     "Margin-at-Risk model combining component price, availability and customer contract terms; the output is a required buffer, not a hedge ratio."),
    ("FX", "USD component purchases against INR contracts with limited pass-through.",
     "Short-tenor rolling FX programme sized to the procurement cycle, re-papered under the April 2026 rules.")],
   ["PLI scheme support", "Scale across multiple product categories"])

co("motherson", "Samvardhana Motherson", "Auto components",
   {"plastics": 0.17, "copper": 0.10, "alum": 0.06, "steel": 0.05, "chips": 0.04},
   "Operations in dozens of countries make this one of the most complex FX books among Indian-listed companies, with polymer and copper inputs bought locally in each region. Most customer contracts carry raw-material pass-through clauses, so the exposure is the lag and the clause coverage, not the price.",
   (5, "Manufacturing and revenue across many currencies with a consolidated INR reporting base"),
   (3, "Acquisition-driven leverage"),
   (3, "Diversified across customers and geographies"),
   (3, "EV transition reshapes the component mix"),
   [("FX", "A genuinely multi-currency operating footprint where translation and transaction exposure need different treatment.",
     "Separate the translation exposure (accept or hedge as a capital decision) from transaction exposure (hedge on the operating cycle). Conflating them is the most common error in multinational Indian treasuries and is expensive."),
    ("Commodity", "Pass-through clause coverage varies by customer and region.",
     "Contract-clause audit: what share of the input book is actually covered by pass-through, at what lag. Frequently the answer surprises the CFO.")],
   ["Raw material pass-through clauses in most OEM contracts", "Diversification across customers, geographies and products"])

co("bharatforge", "Bharat Forge", "Forgings and defence",
   {"steel": 0.34, "elec": 0.07, "natgas": 0.03, "container": 0.02},
   "Alloy and special steel is the dominant input with no usable Indian hedge, and a large export book into Europe and North America creates EUR and USD receivables against an INR cost base.",
   (4, "EUR and USD export receivables against an INR cost base"),
   (3, "Capex programme across defence and e-mobility diversification"),
   (3, "Commercial vehicle cycle exposure moderated by defence growth"),
   (3, "Powertrain content declines as vehicles electrify"),
   [("Commodity", "Special steel at a third of cost with no liquid Indian contract and only a loose CME HRC proxy.",
     "Steel escalation-clause review across the customer contract book, plus a synthetic input hedge using SGX iron ore and coking coal where clause coverage is thin."),
    ("FX", "Export receivables in two hard currencies against an INR cost base.",
     "Layered receivables programme re-papered under the amended FX rules.")],
   ["Defence and aerospace diversification", "Long-standing global OEM relationships"])

co("exide", "Exide Industries", "Lead-acid and lithium batteries",
   {"lead": 0.56, "plastics": 0.07, "elec": 0.03, "lithium": 0.02},
   "Lead is roughly 60-65% of a lead-acid battery's material cost - among the highest single-input intensities of any listed Indian manufacturer - and MCX offers a liquid INR-denominated lead contract. Recycled lead supplies over half of Indian demand, which adds an informal-sector ESG and regulatory dimension to the supply chain.",
   (3, "USD-linked LME lead flowing through MCX pricing against INR revenue"),
   (2, "Comfortable leverage with a lithium capex programme"),
   (5, "Extreme single-input concentration in a single product technology"),
   (4, "Lithium substitution in starter and backup applications is a long-run structural threat"),
   [("Commodity", "A 20% lead move is a double-digit hit to gross margin, and MCX Lead would have neutralised it. Persistent under-hedging of an available, liquid, onshore, INR-denominated contract is the clearest single finding available on this name.",
     "Straightforward hedge programme design - board mandate, MCX Lead instrument authorisation, Ind AS 109 effectiveness framework, and a hedge ratio tied to the actual procurement calendar. Low complexity, high measurable value, and an easy first engagement that opens the account."),
    ("Supply chain / ESG", "Over half of Indian lead supply is secondary, with substantial informal-sector smelting.",
     "Supply-chain due diligence on the recycled lead channel - increasingly a lender and customer requirement, not just a reputational one.")],
   ["Market leadership in automotive batteries", "Recycling integration lowers input cost"])

co("amararaja", "Amara Raja Energy & Mobility", "Batteries and energy storage",
   {"lead": 0.54, "plastics": 0.07, "lithium": 0.03, "elec": 0.03},
   "The same lead-dominated cost structure as Exide, with a lithium gigafactory programme layering a second, completely different commodity risk on top - one that has no usable hedge and is priced CIF China.",
   (3, "USD-linked lead and lithium inputs against INR revenue"),
   (3, "Gigafactory capex against an established cash-generating base"),
   (5, "Single dominant input in the legacy business"),
   (4, "Managing a technology transition while the legacy product still funds it"),
   [("Commodity", "Lead is hedgeable onshore and typically under-hedged; lithium is not hedgeable at all and is the input for the growth business.",
     "Two-track approach: a conventional MCX Lead programme for the legacy book, and supply-agreement price collars plus scenario modelling for the lithium book. Presenting them as one integrated framework is the differentiator.")],
   ["Established automotive battery franchise", "Early mover in Indian lithium cell manufacturing"])

# --------------------------------------------------------------------------
# Autos, cement, logistics
# --------------------------------------------------------------------------
co("bajajauto", "Bajaj Auto", "Two and three-wheelers",
   {"steel": 0.15, "alum": 0.09, "plastics": 0.06, "natrub": 0.03, "chips": 0.03, "copper": 0.02},
   "A metal-intensive cost base with a substantial export book into Africa and Latin America - so it carries emerging-market currency risk on receivables alongside USD-linked input costs, and those markets are exactly where currency crises happen.",
   (4, "Emerging-market export receivables in fragile currencies against USD-linked inputs"),
   (1, "Net cash"),
   (3, "Two-wheeler concentration with meaningful export dependence"),
   (3, "Electrification of two and three-wheelers"),
   [("FX", "Export receivables in Nigerian naira, Egyptian pound and Latin American currencies - markets where devaluation is a recurring event and forward markets are thin or nonexistent.",
     "Frontier-currency exposure review: where hedging is possible, where it is not, and where the right answer is pricing and payment-terms redesign rather than a derivative. This is the honest answer and clients respect it."),
    ("Commodity", "Metal inputs are hedgeable on MCX but pass-through to price-sensitive two-wheeler buyers is limited.",
     "Pass-through-constrained hedge ratio: hedge the share the market will not absorb.")],
   ["Net cash balance sheet", "Premium and export mix supports margin"])

co("heromoto", "Hero MotoCorp", "Two-wheelers",
   {"steel": 0.16, "alum": 0.08, "plastics": 0.06, "natrub": 0.03, "chips": 0.02},
   "The largest two-wheeler maker by volume with a domestic-heavy revenue base and a metal-intensive cost structure. Price sensitivity in the mass segment limits how much input inflation can be passed on.",
   (2, "Largely domestic INR with USD-linked input costs"),
   (1, "Net cash"), (3, "Two-wheeler and domestic-market concentration"),
   (3, "Electric two-wheeler transition and new entrants"),
   [("Commodity", "Metal input inflation in a segment with limited pricing power - the margin absorbs what the customer will not.",
     "Quantify historical pass-through elasticity by segment and set the hedge ratio to cover the unabsorbable share. Uses the client's own price history, which makes it hard to argue with.")],
   ["Scale and distribution depth", "Net cash balance sheet"])

co("ambuja", "Ambuja Cements", "Cement",
   {"petcoke": 0.11, "coal": 0.10, "diesel": 0.06, "elec": 0.06, "limestone": 0.05},
   "Cement itself is unhedgeable and regionally priced. The hedgeable part of the P&L is entirely upstream - petcoke and imported coal, both USD, plus diesel freight and power. The fuel-mix switch between coal and petcoke is a real option with a calculable threshold.",
   (3, "USD petcoke and coal imports against domestic INR realisations"),
   (2, "Strong balance sheet post-acquisition"),
   (3, "Regional market concentration typical of cement"),
   (4, "CCTS obligated entity; cement is among the hardest sectors to decarbonise"),
   [("Commodity", "The client will ask about cement prices; the answer is that the exposure is petcoke, coal, freight and power.",
     "Kiln fuel-mix optimisation: the coal-versus-petcoke switching threshold in rupees per million kcal, updated with live prices, plus a landed-cost hedge on the imported leg. Reframing the question correctly is itself the value here."),
    ("Regulatory", "CCTS greenhouse-gas intensity targets from the 2026 compliance cycle.",
     "CCTS baseline and certificate-requirement model with an abatement cost curve.")],
   ["Captive limestone reserves", "Strong balance sheet and cost position"])

co("gesco", "Great Eastern Shipping", "Shipping",
   {"bunker": 0.21, "elec": 0.01},
   "A shipowner is long freight rates and short bunker fuel - the mirror image of every importer on this list. Both legs are hedgeable: FFAs on the revenue side, Singapore bunker swaps on the cost side, both in USD, which is also the revenue currency, so the currency mismatch is small.",
   (2, "USD revenue and USD costs - one of the few naturally currency-matched Indian businesses"),
   (2, "Conservative leverage through the cycle"),
   (4, "Highly cyclical single-sector exposure"),
   (4, "IMO decarbonisation rules and EU ETS extension to shipping"),
   [("Commodity", "Long freight, short bunkers, both hedgeable in the same currency as revenue - the cleanest hedging setup of any company in this universe.",
     "Integrated spread hedge across FFAs and bunker swaps rather than two independent programmes; the correlation between the legs materially reduces required hedge notional."),
    ("Regulatory", "EU ETS maritime phase-in and FuelEU Maritime add a compliance cost per EU-touching voyage.",
     "Voyage-level carbon cost model feeding into charter pricing.")],
   ["Natural currency match between revenue and cost", "Conservative balance sheet through the cycle"],
   prod={"crudetanker": 0.45, "drybulk": 0.25})

co("concor", "Container Corporation", "Rail logistics",
   {"diesel": 0.13, "elec": 0.06, "container": 0.03},
   "Rail haulage charges paid to Indian Railways are the dominant cost and are administratively set; diesel and traction power are the market-linked remainder. Volume tracks EXIM trade, so container freight rates matter for demand rather than for cost.",
   (2, "Largely domestic INR"), (1, "Net cash"),
   (4, "EXIM trade concentration with a single infrastructure counterparty"),
   (2, "Dedicated freight corridors improve the structural position"),
   [("Policy", "Haulage charges are set by Indian Railways, not by a market - the largest cost line has no hedge and no negotiation.",
     "Sensitivity model on haulage revisions against contracted customer rates; identifies the repricing lag the P&L absorbs.")],
   ["Net cash balance sheet", "Dedicated freight corridor connectivity"])

# --------------------------------------------------------------------------
# Textiles, paper, solar
# --------------------------------------------------------------------------
co("welspunliving", "Welspun Living", "Home textiles",
   {"cotton": 0.40, "elec": 0.05, "plastics": 0.03, "container": 0.04},
   "Cotton is around 40% of cost with no functioning Indian derivative - SEBI's agri-derivative suspension removed it - and the customer base is concentrated in a small number of large US retailers, so the same shock hits input cost and negotiating position together.",
   (4, "USD export receivables against INR cotton procurement"),
   (3, "Working-capital-intensive with cotton inventory cycles"),
   (5, "Concentrated in a handful of large US retail customers"),
   (3, "Cotton traceability and forced-labour import rules in the US and EU"),
   [("Commodity", "Cotton at 40% of cost with the domestic hedge switched off by the regulator and ICE Cotton No. 2 pricing a different continent's crop.",
     "Honest hedgeability assessment - quantify the ICE basis against Indian Shankar-6 and show where a hedge does and does not work, then build the inventory and forward-contracting policy that has to substitute for it."),
    ("Concentration", "Customer concentration and US tariff exposure on the same revenue base.",
     "Combined customer-concentration and tariff-scenario stress test.")],
   ["Vertically integrated from spinning to finished product", "Established relationships with large global retailers"])

co("vardhman", "Vardhman Textiles", "Yarn and fabric",
   {"cotton": 0.53, "elec": 0.09, "plastics": 0.02},
   "Over half the cost base is cotton, unhedgeable domestically, against yarn prices set by a global market where Chinese and Vietnamese demand is the swing factor. The MSP floor from the Cotton Corporation of India truncates the downside in a way no futures curve reflects.",
   (3, "Export receivables in USD against INR cotton procurement"),
   (3, "Inventory-heavy with seasonal cotton buying"),
   (4, "Single-fibre and single-industry concentration"),
   (2, "China-plus-one sourcing shifts favour Indian textiles"),
   [("Commodity", "Cotton at over half of cost, no domestic derivative, and an MSP floor that makes the downside distribution non-normal - which breaks any VaR calculation that assumes it is.",
     "Rebuild the cotton risk model with the MSP floor as an explicit boundary condition rather than a normal distribution. Technically correct and immediately visible as more credible than the standard output.")],
   ["Vertical integration from spinning to fabric", "Scale advantage in procurement"])

co("jkpaper", "JK Paper", "Paper and packaging board",
   {"pulp": 0.29, "coal": 0.10, "elec": 0.08, "caustic": 0.04},
   "Wood pulp is the dominant input and India imports around half of it, priced off index assessments with no derivative. Captive plantation and farm-forestry programmes are the structural hedge that Indian mills have pursued in place of a financial one.",
   (3, "USD pulp imports against domestic INR realisations"),
   (3, "Capex cycle in packaging board"),
   (3, "Paper and board concentration"),
   (3, "Packaging demand grows as single-use plastic is restricted"),
   [("Commodity", "Imported pulp with no hedging instrument; the effective hedge is agroforestry, which is a capital allocation decision with a multi-year payback.",
     "Model the plantation programme as a real hedge: compare the capital cost of farm-forestry expansion against the volatility it removes, expressed as a hedge cost per tonne. Reframes a capex proposal as a risk decision.")],
   ["Captive plantation and farm-forestry programme", "Packaging board growth offsets writing-paper decline"])

co("waaree", "Waaree Energies", "Solar module manufacturing",
   {"poly": 0.33, "alum": 0.08, "silver": 0.05, "sodaash": 0.03, "container": 0.02},
   "Polysilicon and cells are the dominant input, made overwhelmingly in China, with silver paste and aluminium frames adding hedgeable components. ALMM domestic-content rules and customs duty make the landed cost a policy variable as much as a market one.",
   (4, "USD-denominated cell and wafer imports against INR module sales"),
   (3, "Heavy capex on backward integration into cells and wafers"),
   (4, "Single technology, and policy-dependent domestic demand"),
   (2, "Structurally supported by India's renewable capacity targets"),
   [("Commodity / policy", "Polysilicon has no accessible hedge and Chinese overcapacity has crushed the price - good for developers, bad for Indian cell makers. The company's own backward integration changes which side of that it sits on.",
     "Landed-cost model across the ALMM and customs-duty policy space, with a make-versus-buy breakeven for the backward integration programme."),
    ("Commodity", "Silver paste and aluminium frames are hedgeable on MCX and usually overlooked in a polysilicon-focused discussion.",
     "Hedge the hedgeable components - silver and aluminium - while managing the polysilicon leg contractually. Simple, and it demonstrates the triage framework.")],
   ["Backward integration reduces cell import dependence", "Domestic content advantage under ALMM"])

# --------------------------------------------------------------------------
# Pharma and jewellery
# --------------------------------------------------------------------------
co("cipla", "Cipla", "Pharmaceuticals",
   {"api": 0.19, "plastics": 0.03, "elec": 0.02},
   "APIs and key starting materials are largely Chinese-sourced, and a large share of revenue is USD-denominated - which creates a natural offset between USD input costs and USD receivables that group treasury should be netting before hedging either.",
   (3, "USD API purchases against substantial USD revenue - a natural offset worth quantifying"),
   (1, "Net cash"),
   (3, "US generics concentration alongside a strong domestic franchise"),
   (3, "US price erosion and regulatory inspection risk"),
   [("Supply chain", "Chinese API dependence is an availability risk more than a price risk - an export restriction or environmental shutdown stops production regardless of price.",
     "Molecule-level supply-chain map identifying single-source KSMs, with a 60-90 day interruption scenario run against the product portfolio and its revenue contribution."),
    ("FX", "USD costs and USD revenue on different tenors.",
     "Net-exposure analysis before hedging - the gross positions materially overstate what needs covering.")],
   ["Natural USD revenue offset against USD input costs", "Strong domestic branded franchise"])

co("aurobindo", "Aurobindo Pharma", "Pharmaceuticals",
   {"api": 0.23, "plastics": 0.03, "elec": 0.03},
   "Among the most API-intensive of the large Indian pharma companies, with substantial in-house API manufacturing that reduces but does not remove Chinese KSM dependence, and a US-heavy revenue base.",
   (3, "USD-heavy revenue against USD KSM purchases"),
   (3, "Capex-heavy across API and injectables"),
   (4, "US generics concentration"),
   (3, "Price erosion and inspection risk in the US market"),
   [("Supply chain", "Backward integration into APIs still leaves KSM dependence on China one step further up the chain - a tier-2 exposure that is often not mapped.",
     "Tier-2 supply-chain mapping: the KSMs behind the in-house APIs. Most companies have mapped tier 1 and stopped.")],
   ["Backward integration into API manufacturing", "Broad product and geographic portfolio"])

co("kalyan", "Kalyan Jewellers", "Jewellery retail",
   {"gold": 0.71, "diamonds": 0.05},
   "Gold is over 70% of the cost base and India imports essentially all of it, so the exposure is metal price, rupee and import duty at once. The May 2026 duty hike from 6% to 15% repriced landed cost by roughly nine percentage points in a single session - and no listed instrument hedges a duty change.",
   (4, "USD gold purchases and gold-on-lease funding against INR retail revenue"),
   (3, "Inventory-heavy with gold metal loan funding"),
   (5, "Single commodity dominates the cost base"),
   (2, "Formalisation of the jewellery market favours organised retail"),
   [("Commodity / policy", "MCX Gold hedges the metal but not the duty, and the duty moved more than the metal did in May 2026. Gold-on-lease funding adds a separate lease-rate exposure that the metal hedge does not cover either.",
     "Three-layer gold exposure decomposition - metal, currency, duty - with a hedging structure for the first two and a policy playbook for the third. Compare lease, futures and options funding structures on an all-in cost basis. Flagship jewellery-sector engagement."),
    ("Financial", "Gold metal loans are both a funding instrument and a commodity position.",
     "Treat the metal loan book as a commodity exposure in its own right - most jewellers account for it as funding and never risk-manage it as metal.")],
   ["Hedged inventory model reduces price risk versus unhedged peers", "Organised-sector share gains"])

co("supremeind", "Supreme Industries", "Plastic piping and products",
   {"pvc": 0.46, "plastics": 0.10, "elec": 0.03},
   "PVC resin is nearly half the cost base, India imports over half its PVC, and there is no accessible derivative. Anti-dumping duties and BIS quality control orders make the landed cost a regulatory variable, and inventory gains and losses on resin swings drive reported margin more than volume does.",
   (3, "USD-priced imported PVC against domestic INR sales"),
   (1, "Net cash"),
   (4, "Piping dominates the mix; demand is monsoon and agriculture-linked"),
   (2, "Infrastructure and irrigation spending are structural drivers"),
   [("Commodity", "Half the cost base in an unhedgeable, import-dependent resin whose landed price is set partly by trade-remedy decisions. Reported margin is dominated by inventory revaluation.",
     "Inventory-at-Risk model that separates operating margin from resin revaluation - management and the board frequently cannot tell them apart, and separating them changes how performance is judged."),
    ("Policy", "Anti-dumping duty and BIS quality control orders on PVC change landed cost and supplier availability.",
     "Trade-remedy and QCO watch with a supplier-qualification contingency plan.")],
   ["Net cash balance sheet", "Market leadership in plastic piping"])


# --------------------------------------------------------------------------
# Splice into index.html
# --------------------------------------------------------------------------
def j(o):
    return json.dumps(o, ensure_ascii=False)


def insert_before(src, anchor, text):
    i = src.index(anchor)
    return src[:i] + text + src[i:]


def main():
    src = open(HTML, encoding="utf-8").read()
    existing = set(re.findall(r'\{"id":"([a-z0-9]+)","name"', src))
    dupes = [x["id"] for x in NEW if x["id"] in existing]
    if dupes:
        raise SystemExit(f"ERROR duplicate company ids: {dupes}")

    # 1. companies array
    rows = ",\n".join(f'    {{"id":"{x["id"]}","name":{j(x["name"])},"sector":{j(x["sector"])}}}' for x in NEW)
    src = src.replace('    {"id":"ongc","name":"ONGC","sector":"Oil and gas production"}\n  ],',
                      '    {"id":"ongc","name":"ONGC","sector":"Oil and gas production"},\n' + rows + '\n  ],', 1)

    # 2. deps
    rows = ",\n".join(f'    "{x["id"]}":{j(x["deps"])}' for x in NEW)
    src = src.replace('    "ongc":{"diesel":0.04,"steel":0.03}\n  },',
                      '    "ongc":{"diesel":0.04,"steel":0.03},\n' + rows + '\n  },', 1)

    # 3. prod (producers)
    prods = [x for x in NEW if x["prod"]]
    rows = ",\n".join(f'    "{x["id"]}":{j(x["prod"])}' for x in prods)
    src = src.replace('    "hindalco":{"alum":0.45}\n  },',
                      '    "hindalco":{"alum":0.45},\n' + rows + '\n  },', 1)

    # 4. anchors  (insert before the _default key)
    rows = "".join(f'    "{x["id"]}":{j(x["anchor"])},\n' for x in NEW)
    src = insert_before(src, '    "_default":"No material direct commodity inputs.', rows)

    # 5. lenses
    rows = ",\n".join(
        '    "%s":{fx:[%d,%s],fin:[%d,%s],conc:[%d,%s],trans:[%d,%s]}' % (
            x["id"], x["lens"]["fx"][0], j(x["lens"]["fx"][1]), x["lens"]["fin"][0], j(x["lens"]["fin"][1]),
            x["lens"]["conc"][0], j(x["lens"]["conc"][1]), x["lens"]["trans"][0], j(x["lens"]["trans"][1]))
        for x in NEW)
    m = re.search(r'\n  lenses: \{\n(.*?)\n  \},\n', src, re.S)
    src = src[:m.end(1)] + ",\n" + rows + src[m.end(1):]

    # 6. mitigants
    rows = ",\n".join(f'    "{x["id"]}":{j(x["mit"])}' for x in NEW)
    m = re.search(r'\n  mitigants: \{\n(.*?)\n  \},\n', src, re.S)
    src = src[:m.end(1)] + ",\n" + rows + src[m.end(1):]

    # 7. watch
    rows = ",\n".join(
        '    "%s":[%s]' % (x["id"], ",".join(j({"t": t, "w": w, "a": a}) for t, w, a in x["watch"]))
        for x in NEW)
    m = re.search(r'\n  watch: \{\n(.*?)\n  \},\n', src, re.S)
    src = src[:m.end(1)] + ",\n" + rows + src[m.end(1):]

    open(HTML, "w", encoding="utf-8").write(src)
    print(f"added {len(NEW)} companies ({len(prods)} with producer positions) to index.html")


if __name__ == "__main__":
    main()
