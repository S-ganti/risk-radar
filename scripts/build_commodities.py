#!/usr/bin/env python3
"""
Source of truth for the commodity reference sheet -> data/commodities.json.

Structure is adapted from the Commodities 101 fact-sheet breakdown
(family / symbol / hook / how-it-trades / producers / consumers / importers /
uses / what-moves-the-price / key stats) with one layer added that the handbook
does not carry and a treasury-risk practice cannot work without:

    the India hedgeability layer

For every commodity we record whether a listed contract exists, on which venue,
in which currency, whether an onshore INR contract exists (MCX / NCDEX), and
what basis a hedger inherits. That is what converts "this client buys X" into
"this client can or cannot do anything about X", which is the billable question.

Field key
---------
id      dashboard id, must match DATA.commodities in index.html where present
n      name
sym    periodic-table symbol (<=4 chars)
fam    family key
tier   'A' full profile, 'B' map entry
hook   one line: what this market is
trade  venue / bench / lot / terms / settle / curve / liq
ind    India layer: hedge 0-4, contract, basis, dep (import dependence %), note
prod   [[country, % share], ...] production or export share, see src
use    [[end use, % share], ...]
imp    [[country, % share], ...] import share
drv    [what moves the price]
stats  [[label, value, as-of]]
src    primary sources for the shares above
run:  python scripts/build_commodities.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "commodities.json")

HEDGE_SCALE = {
    "4": "Listed contract available onshore in INR (MCX / NCDEX) and liquid globally. Hedge onshore, no FX leg, lightest permission burden.",
    "3": "Liquid listed contract exists offshore in USD only (LME / CME / ICE / SGX / DCE). Hedging needs an offshore commodity derivative under the RBI Master Direction plus an FX leg - and the FX leg is itself constrained by the April 2026 NDF prohibition.",
    "2": "Listed but thin, or hedgeable only through a correlated proxy contract. Material basis risk; Ind AS 109 hedge effectiveness is hard to pass at 80-125%.",
    "1": "No exchange contract. OTC swap, index-linked supply contract or formula pricing only. Counterparty credit and disclosure burden sit with the client.",
    "0": "No financial hedge exists. Managed contractually only: pass-through clauses, indexation, tenders, inventory policy, dual sourcing.",
}

FAMILIES = {
    "precious": {"n": "Precious Metals", "c": "#C9A227"},
    "base":     {"n": "Base Metals, Iron & Steel", "c": "#A2703F"},
    "critical": {"n": "Battery & Critical Materials", "c": "#7A6BD8"},
    "oil":      {"n": "Oil & Refined Products", "c": "#4C5C68"},
    "gas":      {"n": "Gas, Power & Coal", "c": "#3E7B8C"},
    "petchem":  {"n": "Petrochemicals & NGLs", "c": "#8C5A7A"},
    "ag":       {"n": "Agriculture", "c": "#4E8C5A"},
    "fert":     {"n": "Fertilizer", "c": "#6E8B3D"},
    "freight":  {"n": "Freight & Shipping", "c": "#41708A"},
    "env":      {"n": "Environmental Markets", "c": "#2E8B72"},
}

C = []


def c(**kw):
    C.append(kw)


# ===========================================================================
# PRECIOUS METALS
# ===========================================================================

c(
    id="gold", n="Gold", sym="Au", fam="precious", tier="A",
    hook="India's second-largest import line after crude, and after the May 2026 duty hike the most policy-exposed price on the board.",
    trade=dict(
        venue="LBMA (OTC spot) · COMEX · MCX · SGX",
        bench="LBMA Gold Price PM (USD/oz); COMEX GC front month",
        lot="100 oz (COMEX); 1 kg (MCX Gold); 8 g (MCX Gold Petal)",
        terms="USD per troy ounce; INR per 10 g on MCX",
        settle="LBMA loco London unallocated transfer; COMEX physical into approved vaults; MCX physical delivery at Ahmedabad",
        curve="Contango set by the USD lease/forward rate (GOFO); backwardation is rare and signals physical stress",
        liq="Deepest precious metal market; 24-hour OTC plus three liquid futures venues"),
    ind=dict(
        hedge=4,
        contract="MCX Gold (1 kg), Gold Mini (100 g), Gold Petal (1 g), Gold Guinea (8 g) - INR per 10 g, physically settled",
        basis="MCX = LBMA x USDINR x (1 + import duty) + local premium/discount. The 13 May 2026 duty hike from 6% to 15% (10% BCD + 5% AIDC) repriced this basis by ~9 percentage points in one session, which is exactly the kind of move that breaks a hedge ratio set on the old duty. Duty is a policy variable, not a market one, and no listed instrument hedges it.",
        dep=99,
        note="India imports ~800 t/yr against negligible domestic mine output. Gold-on-lease funding used by jewellers carries a separate lease-rate exposure that the metal hedge does not cover."),
    prod=[["China", 10], ["Russia", 10], ["Australia", 9], ["Canada", 6], ["United States", 5], ["Rest of world", 60]],
    use=[["Jewellery", 45], ["Investment (bar, coin, ETF)", 25], ["Central banks", 21], ["Technology", 6], ["Other", 3]],
    imp=[["China", 22], ["India", 20], ["Switzerland (refining hub)", 18], ["Rest of world", 40]],
    drv=["Real US yields and Fed path", "Central bank buying, led by emerging Asia", "USD direction", "Indian and Chinese physical demand and the festival/wedding calendar",
         "Indian import duty and any policy aimed at the current account", "Geopolitical and de-dollarisation flows", "ETF holdings"],
    stats=[["India annual imports", "~800 t", "2025"], ["India import duty", "15% (10% BCD + 5% AIDC)", "13 May 2026"],
           ["Share of India's import bill", "second only to crude", "FY26"], ["Central bank net purchases", "~1,000 t/yr run rate", "2022-2025"]],
    src="World Gold Council, USGS MCS 2026, LBMA, CBIC notification of 13 May 2026",
)

c(
    id="silver", n="Silver", sym="Ag", fam="precious", tier="A",
    hook="Half precious metal, half industrial input - and the solar build-out has made the industrial half the marginal buyer.",
    trade=dict(
        venue="LBMA (OTC) · COMEX · MCX",
        bench="LBMA Silver Price (USD/oz); COMEX SI",
        lot="5,000 oz (COMEX); 30 kg (MCX Silver), 5 kg (Silver Mini), 1 kg (Silver Micro)",
        terms="USD per troy ounce; INR per kg on MCX",
        settle="LBMA loco London; COMEX and MCX physical delivery",
        curve="Usually contango; far more volatile than gold, roughly 1.5-2x gold's realised vol",
        liq="Liquid but thinner than gold; prone to squeezes because visible above-ground stock is small relative to turnover"),
    ind=dict(
        hedge=4,
        contract="MCX Silver (30 kg), Silver Mini (5 kg), Silver Micro (1 kg) - INR per kg",
        basis="Same duty-driven basis as gold: silver was included in the 13 May 2026 hike to 15%. Solar-cell and contact-paste importers carry the duty risk without the jewellery channel's ability to reprice.",
        dep=85,
        note="Hindustan Zinc is a material domestic by-product producer, which makes it one of the few Indian names that is long silver rather than short it."),
    prod=[["Mexico", 24], ["China", 14], ["Peru", 13], ["Chile", 7], ["Poland", 5], ["Rest of world", 37]],
    use=[["Industrial (electrical, brazing)", 45], ["Photovoltaics", 17], ["Jewellery and silverware", 20], ["Investment", 15], ["Photography and other", 3]],
    imp=[["India", 17], ["United States", 14], ["United Kingdom", 11], ["Rest of world", 58]],
    drv=["Solar cell manufacturing volumes and thrifting of silver paste per cell", "Gold direction (silver beta)", "Industrial electronics demand",
         "Mine supply, most of which is a by-product of lead-zinc and copper mining and does not respond to the silver price", "Indian import duty", "Investment flows"],
    stats=[["World mine production", "~26,000 t", "2025"], ["PV share of demand", "~17% and rising", "2025"],
           ["India import duty", "15%", "13 May 2026"], ["By-product share of mine supply", "~70%", "2025"]],
    src="USGS MCS 2026, Silver Institute, CBIC",
)

c(
    id="pallad", n="Palladium", sym="Pd", fam="precious", tier="A",
    hook="A single Russian producer sets the marginal tonne of the metal in every petrol autocatalyst.",
    trade=dict(
        venue="NYMEX · LPPM (OTC)",
        bench="NYMEX PA front month; LBMA/LPPM palladium fix",
        lot="100 oz (NYMEX)",
        terms="USD per troy ounce",
        settle="Physical delivery into approved vaults; most industrial purchase is direct from refiners on formula pricing",
        curve="Erratic; deep backwardation during the 2020-2022 supply squeeze",
        liq="Thin. Small market, few participants, and a bid-ask that widens sharply in stress"),
    ind=dict(
        hedge=2,
        contract="No MCX contract. NYMEX only, USD.",
        basis="No onshore instrument. A NYMEX hedge is offshore, USD-denominated, and thin enough that a large Indian autocatalyst hedge would move the market against itself. Most Indian exposure is embedded inside imported catalyst assemblies, so the price risk arrives as a component cost, not a metal purchase - which makes it nearly impossible to hedge cleanly.",
        dep=100,
        note="Substitution toward platinum in petrol autocats is the real long-run mitigant, and it is an engineering decision, not a treasury one."),
    prod=[["Russia", 44], ["South Africa", 35], ["Canada", 8], ["United States", 6], ["Rest of world", 7]],
    use=[["Autocatalysts (petrol)", 80], ["Electronics", 6], ["Chemical and dental", 8], ["Jewellery and investment", 6]],
    imp=[["China", 25], ["United States", 20], ["Germany", 13], ["Rest of world", 42]],
    drv=["Russian export policy and any sanctions touching Norilsk Nickel", "South African power availability and shaft closures",
         "Petrol vehicle production volumes", "Platinum-for-palladium substitution in catalyst formulations", "EV share gains, which erode the demand base structurally"],
    stats=[["Russia share of mine supply", "44%", "2025"], ["Autocatalyst share of demand", "~80%", "2025"], ["Loading per petrol vehicle", "2-7 g", "2025"]],
    src="USGS MCS 2026, Johnson Matthey PGM market report",
)

c(
    id="platinum", n="Platinum", sym="Pt", fam="precious", tier="B",
    hook="Diesel autocatalysts and, increasingly, the substitute for palladium and the electrode metal for green hydrogen.",
    trade=dict(venue="NYMEX · LPPM (OTC)", bench="NYMEX PL; LPPM platinum fix", lot="50 oz",
               terms="USD per troy ounce", settle="Physical delivery into approved vaults",
               curve="Contango in surplus years", liq="Thin, comparable to palladium"),
    ind=dict(hedge=2, contract="No MCX contract; NYMEX only",
             basis="Offshore USD only. India's platinum import flow has also been distorted by alloy-classification arbitrage against the gold duty, which makes customs policy a live risk on top of price.",
             dep=100, note="Watch the platinum-alloy import route: it is a duty-arbitrage channel that a policy change closes overnight."),
    prod=[["South Africa", 67], ["Russia", 11], ["Zimbabwe", 8], ["Canada", 4], ["Rest of world", 10]],
    use=[["Autocatalysts", 40], ["Jewellery", 25], ["Industrial and glass", 25], ["Investment", 10]],
    imp=[["China", 30], ["United States", 15], ["Japan", 10], ["Rest of world", 45]],
    drv=["South African power and mine supply", "Diesel vehicle share", "Palladium substitution", "Green hydrogen electrolyser build-out", "Chinese jewellery demand"],
    stats=[["South Africa share of supply", "67%", "2025"]],
    src="USGS MCS 2026, Johnson Matthey",
)

c(
    id="diamonds", n="Rough Diamonds", sym="Dia", fam="precious", tier="A",
    hook="India cuts around 90% of the world's stones by volume, so a rough-price move lands on Surat before anywhere else.",
    trade=dict(
        venue="No exchange. Producer tender and long-term contract (De Beers sights, Alrosa auctions)",
        bench="Producer price lists and index services (Rapaport for polished, no accepted rough index)",
        lot="Parcel, by tender",
        terms="USD per carat, by grade",
        settle="Physical, on allocation or auction",
        curve="No forward curve exists",
        liq="Illiquid and opaque. Every stone grade is effectively its own market"),
    ind=dict(
        hedge=0,
        contract="None. There is no diamond futures contract anywhere.",
        basis="Unhedgeable in the financial sense. The only levers are inventory policy, tender discipline, and the payment terms negotiated with sight-holders. Lab-grown substitution has additionally repriced the polished side faster than the rough side, compressing cutting margins from both ends.",
        dep=100,
        note="Sanctions on Russian rough (G7 import restrictions) plus lab-grown substitution have made this a structurally shrinking-margin business, not a cyclical one."),
    prod=[["Russia", 30], ["Botswana", 20], ["Canada", 13], ["DRC", 10], ["South Africa", 8], ["Rest of world", 19]],
    use=[["Gem and jewellery", 70], ["Industrial and abrasives", 30]],
    imp=[["India (cutting)", 55], ["Belgium (trading)", 15], ["UAE (trading)", 15], ["Rest of world", 15]],
    drv=["US and Chinese bridal jewellery demand", "Lab-grown penetration, the structural driver", "G7 sanctions on Russian rough and the traceability regime",
         "De Beers and Alrosa supply discipline", "Credit availability to Surat and Antwerp traders"],
    stats=[["India share of cutting by volume", "~90%", "2025"], ["Lab-grown share of US engagement stones", "over half", "2025"]],
    src="Kimberley Process, GJEPC, Bain diamond report",
)

# ===========================================================================
# BASE METALS, IRON & STEEL
# ===========================================================================

c(
    id="copper", n="Copper", sym="Cu", fam="base", tier="A",
    hook="The bottleneck metal of electrification, and one India stopped being self-sufficient in the day Tuticorin closed.",
    trade=dict(
        venue="LME (global benchmark) · COMEX (US) · SHFE and INE (China) · MCX (India)",
        bench="LME Copper 3-month forward",
        lot="25 t (LME); 25,000 lb (COMEX); 1 t (MCX)",
        terms="USD per tonne (LME); US cents per pound (COMEX); INR per kg (MCX)",
        settle="LME physical delivery of warehouse warrants on the prompt date; most OTC swaps cash-settle against the LME official cash price. MCX cash-settled against LME.",
        curve="Modest contango in surplus years, flipping to sharp backwardation when LME stocks run low; the cash-to-3s spread is the standard tightness gauge",
        liq="Deepest base metal across the three global venues; the usual macro vehicle for a China or electrification view"),
    ind=dict(
        hedge=4,
        contract="MCX Copper - 1 t lot, INR per kg, cash-settled against LME",
        basis="MCX tracks LME converted at USDINR plus import duty and local premium. Because settlement references LME, the INR contract bundles metal risk and currency risk into one instrument - convenient for a physical buyer, but it means a treasurer who has already hedged USDINR separately is double-counting. Untangling that is a common first finding in a hedge-policy review.",
        dep=45,
        note="India has been a net importer since the 2018 Sterlite Tuticorin closure removed roughly 40% of domestic smelting. Hindalco and Hindustan Copper are the offsetting long positions."),
    prod=[["Chile", 23], ["DRC", 13], ["Peru", 11], ["China", 8], ["United States", 5], ["Indonesia", 5], ["Rest of world", 35]],
    use=[["Electrical and grid", 28], ["Construction", 28], ["Machinery", 20], ["Transport", 13], ["Other", 11]],
    imp=[["China", 52], ["European Union", 13], ["United States", 9], ["South Korea", 4], ["Rest of world", 22]],
    drv=["Chinese credit impulse and construction, still the biggest swing factor", "Grid investment, EV production and data-centre build-out",
         "Mine disruption: Grasberg 2025, Cobre Panama shut since November 2023", "Treatment and refining charges as the live concentrate-scarcity signal",
         "LME, COMEX and SHFE visible inventories", "US trade policy and the COMEX-LME arbitrage", "USD and global rate expectations"],
    stats=[["World mine production", "~23 Mt", "2024"], ["World refined consumption", "~27 Mt", "2024"],
           ["China share of refined demand", "~55%", "2025"], ["Copper in a BEV", "50-80 kg vs ~20 kg in a combustion car", "2025"],
           ["India import dependence", "~45% of refined demand", "FY26"]],
    src="ICSG, USGS MCS 2026, IMF PCPS, MCX contract specification",
)

c(
    id="alum", n="Aluminium", sym="Al", fam="base", tier="A",
    hook="Congealed electricity. India smelts it competitively only because the smelters sit next to captive coal.",
    trade=dict(
        venue="LME · COMEX · SHFE · MCX",
        bench="LME Aluminium 3-month, plus regional physical premia (Midwest, Rotterdam, MJP)",
        lot="25 t (LME); 1 t (MCX)",
        terms="USD per tonne; INR per kg on MCX",
        settle="LME warrant delivery; MCX cash-settled against LME",
        curve="Persistent contango historically, financed by the carry trade; premia are a separate and separately volatile market",
        liq="Deep on LME and SHFE; the physical premium leg is OTC and much thinner"),
    ind=dict(
        hedge=4,
        contract="MCX Aluminium (1 t) and Aluminium Mini",
        basis="The LME contract hedges the metal but not the regional physical premium, which is a distinct exposure and moved violently through the 2025 tariff cycle. For an Indian smelter the bigger point is that aluminium risk is really power risk: at roughly 14 MWh per tonne, coal and grid tariffs drive the cost line more than the LME does.",
        dep=10,
        note="India is a net exporter of primary aluminium. Hindalco, Vedanta and NALCO are long the price - an aluminium spike is a P&L gain, not a cost."),
    prod=[["China", 59], ["India", 6], ["Russia", 6], ["Canada", 5], ["UAE", 4], ["Rest of world", 20]],
    use=[["Transport", 27], ["Construction", 25], ["Packaging", 16], ["Electrical", 13], ["Machinery and other", 19]],
    imp=[["United States", 15], ["Germany", 9], ["Japan", 8], ["Rest of world", 68]],
    drv=["Power cost at the smelter, the single largest input", "Chinese smelting capacity cap of roughly 45 Mt", "Alumina and bauxite availability",
         "Regional physical premia and trade policy", "Russian metal sanctions and LME warehousing rules", "Green-aluminium premium and CBAM"],
    stats=[["Power intensity", "~14 MWh per tonne", "structural"], ["India primary output", "~4.2 Mt", "FY26"],
           ["China capacity cap", "~45 Mt", "policy"], ["CBAM coverage", "aluminium is an in-scope good", "from Jan 2026"]],
    src="IAI, USGS MCS 2026, Ministry of Mines, IMF PCPS",
)

c(
    id="alumina", n="Alumina", sym="Alu", fam="base", tier="B",
    hook="The intermediate between bauxite and aluminium, and a market that spikes far harder than the metal it feeds.",
    trade=dict(venue="LME (alumina contract) · SGX · OTC index", bench="Platts / Fastmarkets alumina index FOB Australia",
               lot="50 t (LME alumina)", terms="USD per tonne", settle="Cash-settled against the index",
               curve="Driven by refinery outages; the 2024-25 Australian and Guinean disruptions produced a violent spike",
               liq="Thin - mostly index-linked physical contracts rather than exchange volume"),
    ind=dict(hedge=2, contract="No MCX contract", basis="Index-linked or thin offshore only. Indian smelters with captive refineries (NALCO, Vedanta Lanjigarh) are naturally hedged; those buying spot alumina are not.",
             dep=15, note="NALCO is a significant alumina exporter, so a spike helps it and hurts non-integrated smelters."),
    prod=[["China", 57], ["Australia", 15], ["Brazil", 8], ["India", 6], ["Rest of world", 14]],
    use=[["Aluminium smelting", 90], ["Non-metallurgical (refractories, ceramics, abrasives)", 10]],
    imp=[["China", 30], ["Rest of world", 70]],
    drv=["Refinery outages and gas supply", "Bauxite availability, especially Guinean export policy", "Chinese refinery restarts", "Caustic soda cost"],
    stats=[["Alumina per tonne of aluminium", "~1.9 t", "structural"]],
    src="IAI, USGS MCS 2026",
)

c(
    id="bauxite", n="Bauxite", sym="Bx", fam="base", tier="B",
    hook="The ore at the head of the aluminium chain, and a market defined by two governments' export policy.",
    trade=dict(venue="No exchange", bench="Bilateral contract and index assessment, CIF China",
               lot="Cargo", terms="USD per tonne", settle="Physical", curve="None",
               liq="Illiquid; a handful of trade routes"),
    ind=dict(hedge=0, contract="None", basis="Unhedgeable. Managed through captive mining leases and long-term offtake. Odisha and Jharkhand leases are the Indian mitigant.",
             dep=0, note="India is bauxite-sufficient. The global risk is Guinea and Indonesia export policy, which reaches India through the alumina price."),
    prod=[["Australia", 27], ["Guinea", 24], ["China", 16], ["Brazil", 8], ["India", 7], ["Rest of world", 18]],
    use=[["Alumina refining", 88], ["Cement, abrasives, refractories", 12]],
    imp=[["China", 65], ["Rest of world", 35]],
    drv=["Guinean political stability and export policy", "Indonesian export bans", "Chinese refinery demand", "Freight"],
    stats=[["Bauxite per tonne of alumina", "~2.5-3 t", "structural"]],
    src="USGS MCS 2026, Ministry of Mines",
)

c(
    id="zinc", n="Zinc", sym="Zn", fam="base", tier="A",
    hook="The galvanising metal - its demand is a direct read on steel construction and infrastructure.",
    trade=dict(venue="LME · SHFE · MCX", bench="LME Zinc 3-month", lot="25 t (LME); 5 t (MCX)",
               terms="USD per tonne; INR per kg on MCX", settle="LME warrant delivery; MCX cash-settled against LME",
               curve="Swings with concentrate availability; treatment charges are the tightness gauge",
               liq="Liquid on LME and SHFE; MCX volumes are modest but usable"),
    ind=dict(hedge=4, contract="MCX Zinc (5 t) and Zinc Mini",
             basis="Onshore INR contract available. Hindustan Zinc is one of the world's lowest-cost producers, so India is structurally long - the exposure sits with galvanisers and steel-coating lines, not the country.",
             dep=5, note="Hindustan Zinc's silver and lead by-products mean its earnings are a three-metal basket, which complicates any single-metal hedge."),
    prod=[["China", 33], ["Peru", 11], ["Australia", 9], ["India", 6], ["Rest of world", 41]],
    use=[["Galvanising", 60], ["Die-casting alloys", 14], ["Brass and bronze", 14], ["Chemicals and other", 12]],
    imp=[["China", 25], ["Rest of world", 75]],
    drv=["Steel galvanising demand and construction cycles", "Mine supply and treatment charges", "Chinese smelter margins and power curtailment", "LME stocks"],
    stats=[["Galvanising share of demand", "~60%", "2025"], ["India refined output", "~0.8 Mt", "FY26"]],
    src="ILZSG, USGS MCS 2026",
)

c(
    id="lead", n="Lead", sym="Pb", fam="base", tier="A",
    hook="Boring, recycled, and roughly 60% of the bill of materials in every lead-acid battery India makes.",
    trade=dict(venue="LME · SHFE · MCX", bench="LME Lead 3-month", lot="25 t (LME); 5 t (MCX)",
               terms="USD per tonne; INR per kg on MCX", settle="LME warrant delivery; MCX cash-settled",
               curve="Usually flat; the most recycled major metal, so secondary supply damps spikes",
               liq="Adequate; the least volatile base metal"),
    ind=dict(hedge=4, contract="MCX Lead (5 t) and Lead Mini",
             basis="Fully hedgeable onshore, which makes the persistent under-hedging by Indian battery makers a straightforward advisory finding. Roughly 60-65% of a lead-acid battery's material cost is the metal; a 20% lead move is a double-digit hit to gross margin that an available MCX contract would have neutralised.",
             dep=25, note="Exide and Amara Raja are the concentrated exposures. Secondary (recycled) lead is over half of Indian supply, and informal-sector smelting makes that supply chain an ESG and regulatory risk as well as a price one."),
    prod=[["China", 44], ["Australia", 8], ["United States", 6], ["Peru", 5], ["Rest of world", 37]],
    use=[["Lead-acid batteries", 85], ["Pigments, alloys, cable sheathing", 15]],
    imp=[["Rest of world", 100]],
    drv=["Automotive replacement-battery demand, which is steadier than new vehicle sales", "Telecom and data-centre backup battery build",
         "Secondary supply and scrap collection rates", "Chinese environmental crackdowns on informal smelters", "Long-run substitution toward lithium in starter and backup roles"],
    stats=[["Battery share of demand", "~85%", "2025"], ["Metal share of battery material cost", "~60-65%", "indicative"],
           ["Secondary share of Indian supply", "over half", "2025"]],
    src="ILZSG, USGS MCS 2026, company annual reports",
)

c(
    id="nickel", n="Nickel", sym="Ni", fam="base", tier="A",
    hook="Stainless steel's alloying metal, now bent out of shape by Indonesian supply growth and battery demand.",
    trade=dict(venue="LME · SHFE", bench="LME Nickel 3-month", lot="6 t",
               terms="USD per tonne", settle="LME warrant delivery",
               curve="Structurally in surplus since the Indonesian NPI build-out; the class 1 / class 2 split means the LME price does not represent all nickel",
               liq="Damaged. The March 2022 short squeeze and cancelled trades cost the LME contract credibility and open interest it has not fully recovered"),
    ind=dict(hedge=3, contract="MCX Nickel was delisted; no active onshore contract",
             basis="Offshore LME only, in USD. Worse, the LME contract prices class 1 refined nickel while most Indian stainless input arrives as ferronickel, NPI or scrap - so the hedge carries a grade basis on top of the FX leg. Ind AS 109 effectiveness testing on that combination frequently fails.",
             dep=100, note="India imports essentially all its primary nickel. Jindal Stainless is the concentrated exposure."),
    prod=[["Indonesia", 55], ["Philippines", 10], ["Russia", 5], ["New Caledonia", 4], ["Rest of world", 26]],
    use=[["Stainless steel", 65], ["Batteries", 12], ["Alloys and plating", 23]],
    imp=[["China", 40], ["Rest of world", 60]],
    drv=["Indonesian supply growth and any export policy change", "Stainless steel output, above all in China and India",
         "Battery chemistry mix - LFP gains erode nickel demand", "LME credibility and inventory", "Class 1 versus class 2 spread"],
    stats=[["Indonesia share of mine supply", "~55%", "2025"], ["Stainless share of demand", "~65%", "2025"], ["India primary nickel import dependence", "~100%", "FY26"]],
    src="INSG, USGS MCS 2026",
)

c(
    id="tin", n="Tin", sym="Sn", fam="base", tier="B",
    hook="The solder metal - small market, concentrated supply, and every circuit board needs it.",
    trade=dict(venue="LME · SHFE", bench="LME Tin 3-month", lot="5 t", terms="USD per tonne",
               settle="LME warrant delivery", curve="Frequently backwardated; tiny visible stocks",
               liq="The thinnest LME base metal; a few thousand tonnes moves the price"),
    ind=dict(hedge=3, contract="No MCX contract", basis="Offshore USD only, and in a market thin enough that hedging size is constrained. Most Indian exposure is embedded in imported electronics.",
             dep=90, note="Myanmar's Wa State mining suspension and Indonesian export licensing are the recurring supply shocks."),
    prod=[["China", 25], ["Indonesia", 20], ["Myanmar", 15], ["Peru", 9], ["Rest of world", 31]],
    use=[["Solder", 48], ["Tinplate", 12], ["Chemicals", 17], ["Other alloys", 23]],
    imp=[["China", 20], ["Rest of world", 80]],
    drv=["Myanmar Wa State mining policy", "Indonesian export licences", "Electronics and semiconductor packaging demand", "LME stocks, which are tiny"],
    stats=[["Solder share of demand", "~48%", "2025"]],
    src="ITA, USGS MCS 2026",
)

c(
    id="ironore", n="Iron Ore", sym="Fe", fam="base", tier="A",
    hook="The largest dry bulk trade on earth, and one of the few major inputs India does not have to import.",
    trade=dict(venue="SGX (dominant) · DCE (China) · CME · NCDEX (India)",
               bench="Platts IODEX 62% Fe CFR China; SGX TSI 62% Fe future",
               lot="100 t (SGX)", terms="USD per dry metric tonne CFR China",
               settle="Cash-settled against the monthly average index",
               curve="Backwardated most of the time; the market rarely pays to carry ore",
               liq="SGX is deeply liquid and the reference for seaborne hedging; DCE is the onshore Chinese pool"),
    ind=dict(
        hedge=3,
        contract="NCDEX has listed iron ore contracts with limited traction; SGX is the practical venue",
        basis="The liquid benchmark prices 62% Fe CFR China. Indian domestic ore is sold at NMDC administered prices or through state auctions, and the correlation to CFR China is loose - a Chinese-index hedge against an Odisha purchase carries large basis. For most Indian mills the real exposure is domestic royalty, auction premia and evacuation logistics, none of which is hedgeable.",
        dep=0,
        note="India is ore-sufficient and a periodic exporter. Export duty policy is the swing variable: the May 2022 duty and its November 2022 rollback each moved domestic prices more than the seaborne index did."),
    prod=[["Australia", 36], ["Brazil", 17], ["China", 14], ["India", 10], ["Rest of world", 23]],
    use=[["Blast-furnace steelmaking", 98], ["Other", 2]],
    imp=[["China", 70], ["Japan", 6], ["European Union", 6], ["Rest of world", 18]],
    drv=["Chinese steel output and property construction", "Vale and Rio Tinto shipment guidance and weather in the Pilbara",
         "Simandou ramp-up in Guinea, the largest new supply in decades", "Chinese port inventories", "Indian export duty policy", "Freight"],
    stats=[["India output", "~280 Mt", "FY26"], ["China share of seaborne imports", "~70%", "2025"], ["Ore per tonne of BF steel", "~1.6 t", "structural"]],
    src="Ministry of Steel, USGS MCS 2026, IMF PCPS, SGX contract specification",
)

c(
    id="steel", n="Steel", sym="Stl", fam="base", tier="A",
    hook="India is the world's second-largest producer and, since 2024, a net importer - which changed who carries the price risk.",
    trade=dict(
        venue="CME (US HRC) · LME (steel scrap, rebar) · SHFE · NCDEX (India, thin)",
        bench="CME US Midwest HRC; Platts HRC FOB China and CFR India assessments",
        lot="20 short tons (CME HRC)",
        terms="USD per short ton (CME); INR per tonne domestically",
        settle="Cash-settled against the published index",
        curve="Follows the steel spread - ore plus coking coal versus finished price",
        liq="CME HRC is genuinely liquid for US exposure; Asian and Indian steel hedging is thin and mostly OTC"),
    ind=dict(
        hedge=2,
        contract="NCDEX steel contracts exist but carry negligible open interest; no usable onshore hedge",
        basis="This is the largest hedging gap in Indian industry. A construction or auto client buying HRC in Mumbai has no liquid domestic contract, and the CME contract prices US Midwest steel - a different continent's supply-demand balance. The workable structures are contractual: escalation clauses indexed to a published assessment, or a synthetic spread hedge using iron ore (SGX) and coking coal (SGX) on the input side. Designing that synthetic is real advisory work.",
        dep=5,
        note="Safeguard duties, the EU CBAM on exports, and US Section 232 all bear on the same tonne. Tata Steel and JSW are long the price; L&T, autos and appliance makers are short it."),
    prod=[["China", 53], ["India", 8], ["Japan", 4], ["United States", 4], ["Russia", 4], ["Rest of world", 27]],
    use=[["Construction and infrastructure", 52], ["Machinery", 16], ["Automotive", 12], ["Metal goods", 11], ["Other", 9]],
    imp=[["European Union", 12], ["United States", 9], ["Rest of world", 79]],
    drv=["Chinese output discipline and export volumes, the single biggest global variable", "Indian infrastructure and housing demand",
         "Iron ore and coking coal input costs - the steel spread", "Safeguard and anti-dumping duties", "CBAM on EU-bound exports and US Section 232", "Scrap availability and EAF share"],
    stats=[["India crude steel output", "~150 Mt", "FY26"], ["India net trade position", "net importer since FY24", "FY26"],
           ["Construction share of demand", "~52%", "2025"], ["CBAM status", "in-scope good from Jan 2026", "policy"]],
    src="World Steel Association, Ministry of Steel, JPC, CME contract specification",
)

c(
    id="hrc", n="HRC Steel", sym="HRC", fam="base", tier="B",
    hook="The one steel product with a genuinely liquid futures contract, which makes it the proxy for everything else.",
    trade=dict(venue="CME · LME", bench="CME US Midwest Domestic HRC (Platts TSI)", lot="20 short tons",
               terms="USD per short ton", settle="Cash-settled against the monthly index average",
               curve="Steep and volatile; reflects mill lead times", liq="The most liquid steel contract in the world"),
    ind=dict(hedge=3, contract="No Indian contract", basis="Offshore USD, and priced off US Midwest fundamentals. Usable as a directional proxy for a global steel view; not usable for Ind AS 109 hedge accounting against Indian purchases.",
             dep=5, note="Watch it as the leading indicator for Indian flat-steel pricing rather than as a hedge."),
    prod=[["China", 53], ["Rest of world", 47]],
    use=[["Automotive, appliance, pipe, construction", 100]],
    imp=[["Rest of world", 100]],
    drv=["US mill capacity and lead times", "Section 232 tariffs", "Scrap and pig iron cost", "Auto and appliance build rates"],
    stats=[["Liquidity", "the only deeply traded steel contract", "structural"]],
    src="CME contract specification, Platts",
)

c(
    id="scrap", n="Ferrous Scrap", sym="Scr", fam="base", tier="B",
    hook="The feedstock of the electric-arc route, and the reason a decarbonising steel industry needs less coking coal.",
    trade=dict(venue="LME · CME", bench="LME Steel Scrap CFR Turkey; CME Busheling", lot="10 t",
               terms="USD per tonne", settle="Cash-settled against the index",
               curve="Tracks Turkish and Asian EAF demand", liq="LME Turkey scrap is the liquid seaborne benchmark"),
    ind=dict(hedge=3, contract="No Indian contract", basis="LME CFR Turkey is offshore USD and prices a different trade route than India's imports from the Gulf, UK and West Africa. Usable proxy, meaningful basis.",
             dep=25, note="India is a large scrap importer and the National Steel Scrap Recycling Policy is trying to change that. EAF and induction-furnace share is the structural driver."),
    prod=[["European Union", 20], ["United States", 18], ["Japan", 8], ["Rest of world", 54]],
    use=[["EAF and induction steelmaking", 90], ["BOF charge", 10]],
    imp=[["Turkey", 20], ["India", 12], ["Rest of world", 68]],
    drv=["Turkish EAF utilisation", "Global steel demand", "Collection rates and vehicle scrappage policy", "Export restrictions in the EU"],
    stats=[["India scrap imports", "~9 Mt", "FY26"]],
    src="Ministry of Steel, BIR, LME contract specification",
)

c(
    id="ferroalloy", n="Ferroalloys", sym="FeA", fam="base", tier="B",
    hook="Silicomanganese, ferrochrome and ferrosilicon - small line items that decide stainless and special-steel margins.",
    trade=dict(venue="No liquid exchange; index assessment and tender", bench="Fastmarkets / Argus assessments; quarterly ferrochrome benchmark",
               lot="Cargo", terms="USD per tonne or per pound of contained chrome", settle="Physical",
               curve="None", liq="Illiquid"),
    ind=dict(hedge=0, contract="None", basis="Unhedgeable financially. Power cost is the dominant input, so an Indian producer's real hedge is a captive power tie-up. Managed through tenders and inventory.",
             dep=30, note="India is a significant ferroalloy exporter; South Africa and Kazakhstan dominate chrome."),
    prod=[["China", 55], ["South Africa", 12], ["India", 9], ["Kazakhstan", 6], ["Rest of world", 18]],
    use=[["Carbon and alloy steel", 60], ["Stainless steel", 40]],
    imp=[["China", 30], ["Rest of world", 70]],
    drv=["Stainless steel output", "Power tariffs in producing regions", "South African chrome ore export policy", "Chinese production controls"],
    stats=[["Power intensity", "very high - effectively an electricity export", "structural"]],
    src="USGS MCS 2026, Indian Ferro Alloy Producers Association",
)

c(
    id="limestone", n="Limestone", sym="Lst", fam="base", tier="B",
    hook="The cheapest input in the book, and the one nobody imports.",
    trade=dict(venue="No exchange", bench="Mine-gate cost", lot="n/a", terms="INR per tonne",
               settle="Physical", curve="None", liq="No market - captive"),
    ind=dict(hedge=0, contract="None", basis="No price risk worth hedging. The risk is lease tenure, mining-lease auction premia and environmental clearance, not price.",
             dep=0, note="Captive mines are the norm for Indian cement makers. Royalty and District Mineral Foundation levies are the policy exposure."),
    prod=[["China", 45], ["India", 8], ["Rest of world", 47]],
    use=[["Cement", 75], ["Steel flux and lime", 15], ["Other", 10]],
    imp=[["Rest of world", 100]],
    drv=["Lease auction premia", "Royalty and DMF rates", "Environmental clearance timelines"],
    stats=[["Limestone per tonne of clinker", "~1.5 t", "structural"]],
    src="Indian Bureau of Mines",
)

c(
    id="cement", n="Cement", sym="Cem", fam="base", tier="A",
    hook="A regional, non-traded commodity where the real exposure is coal, petcoke and diesel, not the cement price.",
    trade=dict(venue="No exchange", bench="Regional realisation per bag / per tonne", lot="n/a",
               terms="INR per tonne", settle="Physical", curve="None",
               liq="Not traded - freight economics limit the market radius to roughly 300 km"),
    ind=dict(hedge=0, contract="None", basis="Cement itself is unhedgeable. The hedgeable part of a cement P&L is upstream: petcoke and imported coal (offshore USD), diesel freight (crude proxy) and power. A cement client's hedging conversation is entirely about the input stack, which is a useful reframe because most treasurers arrive asking about the wrong variable.",
             dep=0, note="India is the world's second-largest producer with no material import exposure on the finished good."),
    prod=[["China", 51], ["India", 9], ["Vietnam", 3], ["Rest of world", 37]],
    use=[["Housing", 60], ["Infrastructure", 25], ["Commercial and industrial", 15]],
    imp=[["Rest of world", 100]],
    drv=["Indian housing and infrastructure spend", "Petcoke and imported thermal coal prices", "Diesel and rail freight rates", "Regional capacity additions and price discipline", "Monsoon seasonality"],
    stats=[["India capacity", "~700 Mt", "FY26"], ["Energy share of cost", "~40-50% including freight", "indicative"],
           ["Market radius", "~300 km by road", "structural"]],
    src="Cement Manufacturers Association, company annual reports",
)

c(
    id="tio2", n="Titanium Dioxide", sym="TiO2", fam="base", tier="B",
    hook="The white pigment in every litre of paint - and a market China now sets the price in.",
    trade=dict(venue="No exchange", bench="Producer price lists and index assessments", lot="Container",
               terms="USD per tonne", settle="Physical", curve="None",
               liq="Illiquid; contract and spot negotiation"),
    ind=dict(hedge=0, contract="None", basis="Unhedgeable financially. Anti-dumping duty on Chinese TiO2 is the live Indian policy variable and cuts the other way from price - a duty that protects domestic producers raises the paint makers' cost. Managed through supplier diversification and forward purchase.",
             dep=60, note="Asian Paints, Berger and Kansai are the concentrated exposures; roughly the largest single raw material in a paint formulation."),
    prod=[["China", 55], ["United States", 10], ["Rest of world", 35]],
    use=[["Paints and coatings", 60], ["Plastics", 25], ["Paper and other", 15]],
    imp=[["European Union", 20], ["India", 8], ["Rest of world", 72]],
    drv=["Chinese production and export pricing", "Anti-dumping duties in India and the EU", "Ilmenite and rutile feedstock cost", "Construction and auto refinish demand"],
    stats=[["Share of paint raw material cost", "typically the largest single item", "indicative"]],
    src="USGS MCS 2026, DGTR notifications, company annual reports",
)

# ===========================================================================
# BATTERY & CRITICAL MATERIALS
# ===========================================================================

c(
    id="lithium", n="Lithium", sym="Li", fam="critical", tier="A",
    hook="Mined in Australia and Chile, refined in China - and India has neither leg.",
    trade=dict(venue="CME · SGX · GFEX (China)", bench="CME Lithium Hydroxide and Carbonate (Fastmarkets CIF China/Japan/Korea)",
               lot="1 t", terms="USD per tonne", settle="Cash-settled against the index",
               curve="Whipsawed - a 2022 spike then an 80%+ collapse; the contract is young and the curve is not a reliable forecast",
               liq="Growing but still thin; GFEX carbonate is the deepest onshore Chinese pool"),
    ind=dict(hedge=2, contract="No Indian contract",
             basis="Offshore USD, thin, and priced CIF China/Japan/Korea. Indian cell imports arrive as finished cells, not as lithium, so the exposure is one derivative removed from the hedgeable instrument. The practical mitigants are supply agreements with price collars and the PLI-driven push to domestic cell manufacturing.",
             dep=100, note="India has no meaningful refining. The Reasi (J&K) resource remains undeveloped. Battery cost passes into EVs, grid storage and telecom backup."),
    prod=[["Australia", 38], ["Chile", 24], ["China", 18], ["Argentina", 10], ["Rest of world", 10]],
    use=[["Batteries", 87], ["Ceramics and glass", 5], ["Lubricating greases and other", 8]],
    imp=[["China (refining feedstock)", 65], ["Rest of world", 35]],
    drv=["EV production rates in China, Europe and the US", "Grid-scale storage build-out", "New brine and hard-rock supply coming online",
         "Chinese refining capacity and any export controls", "Chemistry mix - LFP versus NMC", "Recycling volumes, still small"],
    stats=[["China share of refining", "65-70%", "2025"], ["Battery share of demand", "~87%", "2025"], ["India refining capacity", "negligible", "2026"]],
    src="IEA Critical Minerals Outlook, USGS MCS 2026",
)

c(
    id="cobalt", n="Cobalt", sym="Co", fam="critical", tier="B",
    hook="A DRC by-product with an ESG file thicker than its order book.",
    trade=dict(venue="LME · CME", bench="LME Cobalt (Fastmarkets standard grade)", lot="1 t",
               terms="USD per tonne", settle="Cash-settled against the index",
               curve="Long surplus since the Kisanfu and KFM ramp-ups", liq="Thin"),
    ind=dict(hedge=2, contract="No Indian contract", basis="Offshore, thin. DRC export quotas introduced in 2025 are the live supply variable. Most Indian exposure is embedded in imported cells.",
             dep=100, note="Artisanal mining and child-labour due diligence is a bigger client conversation than the price."),
    prod=[["DRC", 74], ["Indonesia", 12], ["Rest of world", 14]],
    use=[["Batteries", 72], ["Superalloys", 12], ["Other", 16]],
    imp=[["China", 70], ["Rest of world", 30]],
    drv=["DRC export quota policy", "Indonesian nickel by-product supply", "LFP substitution away from cobalt", "Supply-chain due diligence rules"],
    stats=[["DRC share of mine supply", "~74%", "2025"]],
    src="USGS MCS 2026, IEA",
)

c(
    id="graphite", n="Graphite", sym="Gr", fam="critical", tier="B",
    hook="The anode material, and one of the export licences China chose to tighten first.",
    trade=dict(venue="No liquid exchange", bench="Index assessment for flake and spherical grades", lot="Container",
               terms="USD per tonne", settle="Physical", curve="None", liq="Illiquid"),
    ind=dict(hedge=0, contract="None", basis="Unhedgeable. This is an availability risk, not a price risk: Chinese export licensing on synthetic and natural graphite anode material can stop a cell line regardless of price. Mitigation is qualification of non-Chinese sources, which takes quarters.",
             dep=95, note="India has natural flake resources but no spheroidisation or coating capacity."),
    prod=[["China", 77], ["Madagascar", 6], ["Mozambique", 5], ["Rest of world", 12]],
    use=[["Battery anodes", 45], ["Refractories", 30], ["Other", 25]],
    imp=[["Rest of world", 100]],
    drv=["Chinese export licensing", "EV cell production", "Synthetic graphite power and needle-coke cost", "Non-Chinese qualification timelines"],
    stats=[["China share of anode material", "over 90%", "2025"]],
    src="USGS MCS 2026, IEA",
)

c(
    id="ree", n="Rare Earths", sym="REE", fam="critical", tier="A",
    hook="Not rare, but refined almost nowhere else - and the export-control lever China has used hardest.",
    trade=dict(venue="No Western exchange", bench="Chinese domestic listed prices and Asian Metal / Argus assessments for NdPr oxide and magnets",
               lot="Container", terms="USD per kg (oxide); USD per kg (sintered magnet)", settle="Physical",
               curve="None", liq="Opaque and administered - Chinese production quotas set supply by decree"),
    ind=dict(hedge=0, contract="None",
             basis="There is no hedge. The exposure is a licence queue, not a price. The 2025 export-control expansion on rare-earth magnets stopped Indian auto and appliance lines that had no visibility into their tier-2 suppliers' magnet sourcing. The advisory work is supply-chain mapping to identify where magnets enter the bill of materials, followed by qualification of Japanese or Vietnamese alternatives and inventory policy - a resilience engagement, not a treasury one.",
             dep=95, note="India has monazite resources through IREL but negligible separation and magnet-making capacity. The National Critical Mineral Mission is the policy response."),
    prod=[["China", 69], ["United States", 12], ["Myanmar", 8], ["Australia", 5], ["Rest of world", 6]],
    use=[["Permanent magnets (NdFeB)", 40], ["Catalysts", 20], ["Polishing and glass", 15], ["Metallurgy and other", 25]],
    imp=[["Japan", 25], ["United States", 15], ["Rest of world", 60]],
    drv=["Chinese export licensing and quota decisions", "EV traction-motor and wind-turbine demand", "Myanmar supply disruption",
         "Ex-China separation capacity coming online (Lynas, MP Materials)", "Magnet-free motor design substitution"],
    stats=[["China share of separation", "~90%", "2025"], ["China share of magnet manufacture", "~90%", "2025"],
           ["NdFeB in an EV traction motor", "1-2 kg", "indicative"]],
    src="USGS MCS 2026, IEA Critical Minerals, Ministry of Mines National Critical Mineral Mission",
)

c(
    id="antimony", n="Antimony & Tungsten", sym="SbW", fam="critical", tier="B",
    hook="Two small metals China restricted in 2024, and prices went vertical because nobody had a second source.",
    trade=dict(venue="No exchange", bench="Rotterdam and Chinese index assessments", lot="Tonne lots",
               terms="USD per tonne", settle="Physical", curve="None", liq="Very illiquid"),
    ind=dict(hedge=0, contract="None", basis="Unhedgeable. Antimony trioxide is a flame retardant used in plastics and textiles; tungsten carbide is in every cutting tool. Both are China-controlled. Inventory and requalification are the only levers.",
             dep=95, note="Relevant to cutting-tool, electronics and flame-retardant plastics users - often as an unexamined tier-3 dependency."),
    prod=[["China", 48], ["Tajikistan", 15], ["Russia", 10], ["Rest of world", 27]],
    use=[["Flame retardants", 45], ["Lead-acid battery alloys", 20], ["Cutting tools (tungsten)", 35]],
    imp=[["Rest of world", 100]],
    drv=["Chinese export licensing", "Military and ammunition demand", "Solar glass clarifier demand for antimony", "Cutting-tool and mining consumption for tungsten"],
    stats=[["Antimony price move on 2024 export controls", "multi-fold", "2024-25"]],
    src="USGS MCS 2026",
)

c(
    id="uranium", n="Uranium", sym="U", fam="critical", tier="B",
    hook="Priced in long-term contracts, not spot - which is why the spot headline rarely matches what a utility pays.",
    trade=dict(venue="CME (UxC U3O8 future)", bench="UxC and TradeTech spot and long-term indicators",
               lot="250 lb U3O8", terms="USD per pound U3O8", settle="Cash-settled against the UxC index",
               curve="Long-term contract price is the meaningful number; spot is a thin residual market",
               liq="Thin on exchange; the real market is bilateral utility contracting"),
    ind=dict(hedge=1, contract="No Indian contract", basis="India's civil nuclear fuel is procured under government-to-government and NPCIL contracts, not market instruments. Effectively no corporate exposure today; it becomes relevant if small modular reactors open to private power producers.",
             dep=70, note="Watch as a forward-looking item tied to nuclear policy liberalisation rather than a live exposure."),
    prod=[["Kazakhstan", 43], ["Canada", 15], ["Namibia", 11], ["Australia", 8], ["Rest of world", 23]],
    use=[["Nuclear power generation", 100]],
    imp=[["Rest of world", 100]],
    drv=["Reactor restarts and new build, especially China", "Kazatomprom production guidance", "Russian enrichment sanctions", "Utility contracting cycles", "Data-centre power demand driving SMR interest"],
    stats=[["Kazakhstan share", "~43%", "2025"]],
    src="World Nuclear Association, USGS MCS 2026",
)

c(
    id="chips", n="Semiconductors", sym="Si", fam="critical", tier="A",
    hook="Not a commodity in the tradeable sense - but the 2021 shortage cost Indian carmakers more than any metal move that decade.",
    trade=dict(venue="No exchange", bench="Foundry price lists; memory contract prices (DRAM, NAND) are the only semi-commoditised leg",
               lot="Wafer or unit", terms="USD per unit / per wafer", settle="Physical, on allocation",
               curve="None", liq="No market. Allocation, not price, is the clearing mechanism in shortage"),
    ind=dict(hedge=0, contract="None",
             basis="Unhedgeable and mispriced as a treasury problem. In a shortage the loss is unbuilt vehicles, not expensive chips - a volume risk that hits revenue, not COGS. The right instrument is a business-interruption model and a multi-tier supplier map, not a derivative. Taiwan concentration makes this a geopolitical scenario line as much as a supply-chain one.",
             dep=95, note="India's fab programme (Dholera, Sanand ATMP) changes the picture late-decade, not now."),
    prod=[["Taiwan", 60], ["South Korea", 17], ["China", 8], ["United States", 6], ["Rest of world", 9]],
    use=[["Computing and data centre", 35], ["Communications", 25], ["Automotive", 15], ["Industrial", 13], ["Consumer", 12]],
    imp=[["China", 30], ["Rest of world", 70]],
    drv=["Taiwan Strait geopolitics - the dominant tail risk", "AI and data-centre capex cycle", "Automotive content per vehicle",
         "Export controls on advanced nodes", "Legacy-node capacity, which is what autos actually use"],
    stats=[["Taiwan share of leading-edge fabrication", "~90%", "2025"], ["Semiconductor content per car", "rising, ~$600-1,000", "2025"],
           ["2021 shortage cost", "global auto production loss of ~10m units", "2021"]],
    src="SEMI, WSTS, company disclosures",
)

c(
    id="poly", n="Polysilicon", sym="PSi", fam="critical", tier="A",
    hook="The input to every solar module, made almost entirely in one Chinese province with cheap coal power.",
    trade=dict(venue="GFEX (China) · no Western exchange", bench="Chinese domestic polysilicon price; PVInsights and Bernreuter assessments",
               lot="Tonne", terms="USD or RMB per kg", settle="Physical",
               curve="GFEX listed a polysilicon future in 2024; still primarily a physical market",
               liq="Thin outside China"),
    ind=dict(hedge=1, contract="No Indian contract",
             basis="Effectively unhedgeable from India. The exposure for Indian module makers is compounded by the ALMM domestic-content rules and the basic customs duty on cells and modules, so landed cost is a policy function as much as a market one. Chinese overcapacity has crushed the price, which is good for Indian developers and bad for Indian cell makers - the two sides of the same client base need opposite advice.",
             dep=100, note="Waaree, Premier Energies, Adani Solar and Tata Power Solar are the exposures. Xinjiang forced-labour sourcing rules constrain which supply is usable for export markets."),
    prod=[["China", 93], ["Germany", 3], ["United States", 2], ["Rest of world", 2]],
    use=[["Solar PV", 95], ["Semiconductor grade", 5]],
    imp=[["Rest of world", 100]],
    drv=["Chinese capacity utilisation and price discipline", "Solar installation rates", "Metallurgical silicon and power cost",
         "Xinjiang forced-labour import rules in the US and EU", "Indian ALMM and customs duty policy"],
    stats=[["China share of production", "~93%", "2025"], ["Polysilicon per MW of module", "~2.5 t", "indicative"]],
    src="Bernreuter Research, IEA PVPS, MNRE ALMM notifications",
)

c(
    id="fluorspar", n="Fluorspar", sym="CaF2", fam="critical", tier="B",
    hook="The head of the fluorine chain that ends in refrigerants, PTFE and lithium battery electrolyte salts.",
    trade=dict(venue="No exchange", bench="Acid-grade fluorspar index assessment CIF", lot="Cargo",
               terms="USD per tonne", settle="Physical", curve="None", liq="Illiquid"),
    ind=dict(hedge=0, contract="None", basis="Unhedgeable. India has minimal domestic fluorspar and imports acid-grade material from China, Mexico, South Africa and Vietnam. SRF, Navin Fluorine and Gujarat Fluorochemicals carry it as a direct availability risk, mitigated by long-term supply agreements.",
             dep=95, note="China's export posture on fluorochemical intermediates is the swing factor; HFC phase-down under Kigali reshapes downstream demand."),
    prod=[["China", 63], ["Mexico", 15], ["Mongolia", 7], ["South Africa", 4], ["Rest of world", 11]],
    use=[["Hydrofluoric acid and fluorochemicals", 65], ["Metallurgical flux", 25], ["Other", 10]],
    imp=[["Rest of world", 100]],
    drv=["Chinese mine and export policy", "Refrigerant demand and the Kigali HFC phase-down schedule", "Battery electrolyte (LiPF6) demand", "Aluminium smelting flux demand"],
    stats=[["China share", "~63%", "2025"]],
    src="USGS MCS 2026, company annual reports",
)

# ===========================================================================
# OIL & REFINED PRODUCTS
# ===========================================================================

c(
    id="crude", n="Crude Oil (Brent)", sym="BRN", fam="oil", tier="A",
    hook="The world's price benchmark, and the top line of India's import bill - but not the grade India actually buys.",
    trade=dict(
        venue="ICE (Brent) · CME (WTI) · DME/Gulf Mercantile (Oman) · MCX (India)",
        bench="ICE Brent futures, cash-settled against the Brent Index; Dated Brent for physical",
        lot="1,000 barrels",
        terms="USD per barrel",
        settle="ICE Brent is cash-settled; CME WTI is physically delivered at Cushing, Oklahoma. MCX crude is cash-settled against NYMEX WTI.",
        curve="Contango when supply is long and storage pays; backwardation in tight markets. The 1-month/12-month spread is the standard balance gauge.",
        liq="The deepest commodity market in the world - Brent and WTI together clear more notional than any other physical commodity"),
    ind=dict(
        hedge=4,
        contract="MCX Crude Oil (100 bbl) and Crude Oil Mini (10 bbl), INR per barrel, cash-settled against NYMEX WTI",
        basis="Here is the trap. The MCX contract settles against WTI, but India's import basket is roughly three-quarters sour, Dubai/Oman-linked crude. Hedging an Indian refiner's feedstock with a WTI-settled instrument leaves the Brent-Dubai (and WTI-Dubai) spread completely unhedged - a spread that has swung several dollars a barrel through the Russian-discount era. Any hedge-effectiveness test under Ind AS 109 has to carry that basis explicitly, and a surprising number of Indian hedge programmes do not.",
        dep=89,
        note="India imports ~88-89% of its crude. Russia's share of Indian imports has run around 31-35%, which introduces a sanctions and payment-channel risk on top of the price risk."),
    prod=[["United States", 20], ["Saudi Arabia", 11], ["Russia", 11], ["Canada", 6], ["Iraq", 5], ["China", 4], ["Rest of world", 43]],
    use=[["Transport fuels", 55], ["Petrochemical feedstock", 15], ["Industrial and power", 15], ["Heating and other", 15]],
    imp=[["China", 22], ["India", 12], ["European Union", 12], ["United States", 9], ["Rest of world", 45]],
    drv=["OPEC+ production policy - roughly 40% of world supply sits under one decision", "Strait of Hormuz and Red Sea security",
         "US shale response function and rig counts", "Chinese demand and strategic reserve buying", "Russian sanctions, price caps and the shadow fleet",
         "Global inventory levels and floating storage", "USD and the rate cycle"],
    stats=[["India import dependence", "~88.6%", "FY26"], ["Russia share of Indian imports", "~31%", "FY26"],
           ["India crude import bill", "the largest single import line", "FY26"], ["Indian basket linkage", "~75% Dubai/Oman sour", "structural"]],
    src="PPAC, IEA Oil Market Report, EIA, ICE and MCX contract specifications",
)

c(
    id="dubai", n="Dubai / Oman Crude", sym="DUB", fam="oil", tier="A",
    hook="The sour benchmark Asia actually prices against - and the one Indian refiners should be hedging.",
    trade=dict(venue="DME / Gulf Mercantile Exchange · CME (Dubai swaps) · ICE",
               bench="Platts Dubai assessment; DME Oman futures", lot="1,000 barrels",
               terms="USD per barrel", settle="DME Oman is physically delivered FOB Mina Al Fahal; Dubai swaps cash-settle against the Platts assessment",
               curve="The Brent-Dubai EFS spread is the key structural indicator - it decides whether Atlantic Basin barrels flow east",
               liq="Deep in the swaps market; the futures leg is thinner than Brent"),
    ind=dict(hedge=3, contract="No Indian contract - MCX settles against WTI",
             basis="The correct benchmark for Indian refinery feedstock and the one with no onshore instrument. Hedging requires an offshore USD Dubai swap under RBI permission, plus the FX leg. Most Indian corporates default to the MCX WTI contract because it is easier, and inherit the grade basis as an unmanaged residual. Quantifying that residual is a concrete, defensible piece of advisory work.",
             dep=89, note="Reliance, IOC, BPCL, HPCL, ONGC and every petrochemical cracker in the country sit on this curve."),
    prod=[["Saudi Arabia", 25], ["Iraq", 15], ["UAE", 13], ["Kuwait", 8], ["Rest of Middle East", 39]],
    use=[["Asian refining feedstock", 100]],
    imp=[["China", 30], ["India", 20], ["Japan and Korea", 20], ["Rest of Asia", 30]],
    drv=["Saudi official selling prices (OSPs), set monthly", "Brent-Dubai EFS and arbitrage economics", "Asian refining margins",
         "Russian Urals discount, which competes directly for the same refiners", "Middle East security"],
    stats=[["Share of Indian crude basket", "~75%", "structural"], ["Pricing mechanism", "Saudi OSP set monthly against the Dubai/Oman average", "structural"]],
    src="PPAC, Platts methodology, DME contract specification",
)

c(
    id="diesel", n="Diesel / Gasoil", sym="HO", fam="oil", tier="A",
    hook="The fuel that moves India - every tonne of cement, steel and grain rides on it.",
    trade=dict(venue="ICE (Low Sulphur Gasoil) · CME (ULSD) · Platts Singapore (Gasoil 10ppm)",
               bench="ICE LS Gasoil for Europe; Singapore Gasoil 10ppm for Asia", lot="100 t (ICE gasoil); 42,000 gal (CME ULSD)",
               terms="USD per tonne (ICE); USD per gallon (CME)", settle="ICE gasoil physically deliverable ARA; most Asian exposure hedges via Singapore swaps",
               curve="Tracks refining margins and winter heating demand; the diesel crack is the single most watched refining spread",
               liq="Deep in Europe and Singapore"),
    ind=dict(hedge=3, contract="No liquid Indian diesel contract",
             basis="Indian pump diesel prices are administratively smoothed by the oil marketing companies - they do not track the Singapore crack daily. So a bulk consumer (cement, logistics, mining) faces a price that is politically damped on the way up and sticky on the way down, and a Singapore gasoil swap hedges the wrong series. For most Indian diesel consumers the honest answer is that a financial hedge fits poorly and the real lever is contractual: fuel-escalation clauses in freight and haulage contracts, indexed to the published retail price.",
             dep=0, note="Refined domestically from ~89%-imported crude, so the underlying exposure is crude plus refining margin plus excise policy."),
    prod=[["Refined globally", 100]],
    use=[["Road freight", 40], ["Agriculture and irrigation", 15], ["Rail and marine", 10], ["Industry and gensets", 20], ["Other", 15]],
    imp=[["Rest of world", 100]],
    drv=["Crude price and the diesel crack", "Global refinery outages and turnarounds", "Russian product sanctions and rerouting",
         "Indian excise duty decisions", "Monsoon and agricultural pumping demand", "Freight and construction activity"],
    stats=[["Share of Indian petroleum product consumption", "~38-40%", "FY26"], ["Excise duty", "a material and politically variable share of retail price", "policy"]],
    src="PPAC, IEA, ICE contract specification",
)

c(
    id="jet", n="Jet Fuel / ATF", sym="JET", fam="oil", tier="A",
    hook="Around 35-40% of an Indian airline's operating cost, taxed differently in every state, and hedged by almost nobody.",
    trade=dict(
        venue="Platts Singapore (Jet Kero) · ICE · CME - all via swaps rather than a dominant future",
        bench="Platts Jet Kerosene FOB Singapore; MOPAG for the Gulf",
        lot="1,000 t typical swap",
        terms="USD per barrel or per tonne",
        settle="Cash-settled against the monthly average of the Platts assessment",
        curve="Follows the jet crack, which is driven by aviation recovery and refinery yield flexibility",
        liq="Liquid in the Singapore swaps market; airlines are the natural short-side hedgers"),
    ind=dict(
        hedge=3,
        contract="No Indian ATF contract with meaningful liquidity",
        basis="This is the sharpest hedging gap in Indian corporate risk. Indian ATF is priced fortnightly by the oil marketing companies off the previous period's international average, then has state VAT of anywhere between roughly 1% and 30% layered on top. So an airline hedging with Singapore jet swaps captures the international leg but not the fortnightly reset lag and not the state-tax mix, which shifts with route network. Add the USD leg and the RBI offshore-derivative permission, and you have a three-part basis that has to be modelled explicitly - which is exactly why Indian carriers have historically hedged far less than global peers, and why a properly built ATF hedge programme is a flagship engagement.",
        dep=0,
        note="IndiGo is the concentrated exposure. Aircraft leases are USD-denominated, so the same client has an FX exposure on a different tenor that should be looked at in the same programme."),
    prod=[["Refined globally", 100]],
    use=[["Commercial aviation", 90], ["Military and other", 10]],
    imp=[["Rest of world", 100]],
    drv=["Crude price and the jet crack", "Global air traffic recovery and capacity", "Refinery yield switching between jet and diesel",
         "Indian state VAT decisions and any move to bring ATF under GST", "Fortnightly OMC price reset mechanics"],
    stats=[["Share of Indian airline operating cost", "~35-40%", "indicative"], ["State VAT range", "roughly 1% to 30%", "2026"],
           ["Price reset", "fortnightly, by OMCs", "structural"]],
    src="PPAC, IATA, DGCA, airline annual reports",
)

c(
    id="lpg", n="LPG", sym="LPG", fam="oil", tier="B",
    hook="Half of India's cooking fuel, imported, subsidised - a policy price wearing a commodity's clothes.",
    trade=dict(venue="CME · ICE · Platts (Saudi CP)", bench="Saudi Aramco Contract Price (CP) for propane and butane; Mont Belvieu for the US",
               lot="1,000 t", terms="USD per tonne", settle="Cash-settled against CP or Mont Belvieu",
               curve="Seasonal - northern-hemisphere winter heating demand", liq="Liquid in swaps"),
    ind=dict(hedge=3, contract="No Indian contract",
             basis="Saudi CP swaps offshore in USD. The oil marketing companies carry the under-recovery when the subsidised retail price diverges from import parity, so the corporate exposure is a government-receivable timing risk as much as a price risk.",
             dep=60, note="IOC, BPCL and HPCL carry it. Ujjwala-scheme volumes make this politically load-bearing."),
    prod=[["United States", 25], ["Middle East", 30], ["Rest of world", 45]],
    use=[["Domestic cooking", 60], ["Petrochemical feedstock", 25], ["Industrial and auto", 15]],
    imp=[["India", 18], ["China", 15], ["Japan", 8], ["Rest of world", 59]],
    drv=["Saudi CP announcements, monthly", "US NGL production and export capacity", "Northern winter", "Indian subsidy and Ujjwala policy"],
    stats=[["India import dependence", "~60%", "FY26"], ["World's largest LPG importer", "India", "2025"]],
    src="PPAC, IEA",
)

c(
    id="naphtha", n="Naphtha", sym="NAP", fam="oil", tier="B",
    hook="The cracker feedstock that ties petrochemical margins directly to the oil price.",
    trade=dict(venue="Platts (MOPJ, C+F Japan) · ICE swaps", bench="Naphtha C+F Japan (MOPJ); Naphtha CIF NWE",
               lot="1,000 t", terms="USD per tonne", settle="Cash-settled against the assessment",
               curve="The naphtha crack is the key cracker-margin input; ethane substitution in the US caps it structurally",
               liq="Liquid in Asian swaps"),
    ind=dict(hedge=3, contract="No Indian contract",
             basis="Offshore USD swaps. Reliance and the Indian crackers run naphtha-based capacity, so the exposure is the naphtha-to-ethylene spread rather than naphtha outright - hedging the feedstock alone can make earnings more volatile, not less, if the product price moves with it. That spread framing is the correct advisory posture.",
             dep=0, note="India is broadly balanced, exporting surplus naphtha while crackers consume it."),
    prod=[["Refined globally", 100]],
    use=[["Steam cracker feedstock", 60], ["Gasoline blending", 30], ["Solvents and other", 10]],
    imp=[["South Korea", 20], ["Japan", 15], ["Rest of world", 65]],
    drv=["Crude price", "US ethane advantage, which structurally caps naphtha crackers", "Asian cracker run rates", "Gasoline blending demand"],
    stats=[["Naphtha per tonne of ethylene", "~3 t", "structural"]],
    src="Platts methodology, company annual reports",
)

c(
    id="petcoke", n="Petcoke", sym="PC", fam="oil", tier="A",
    hook="A refinery by-product that became Indian cement's fuel of choice - and a recurring target of air-quality litigation.",
    trade=dict(venue="No exchange", bench="Argus and Platts assessments, US Gulf Coast FOB fuel-grade",
               lot="Cargo", terms="USD per tonne", settle="Physical", curve="None", liq="Illiquid"),
    ind=dict(hedge=1, contract="None",
             basis="Unhedgeable financially. Cement makers manage it with a coal/petcoke fuel-mix switch, which is a real option worth quantifying: the switching threshold in rupees per million kcal is a number a client can act on. Layer on the regulatory risk - petcoke use has been restricted by court order in the NCR and remains a live air-quality file - and the exposure is part price, part policy.",
             dep=35, note="UltraTech, Ambuja, Shree and Dalmia are the exposures. US Gulf refineries are the dominant import source."),
    prod=[["United States", 40], ["China", 15], ["India", 10], ["Rest of world", 35]],
    use=[["Cement kilns", 55], ["Calcined - aluminium anodes", 25], ["Power and other", 20]],
    imp=[["India", 25], ["China", 15], ["Rest of world", 60]],
    drv=["US refinery coker runs", "Indian cement demand and kiln fuel mix", "Thermal coal price - the substitute", "Air-quality regulation and court orders", "Freight"],
    stats=[["India import dependence", "~35%", "FY26"], ["Calorific advantage over thermal coal", "roughly 8,000 vs 5,000 kcal/kg", "structural"]],
    src="PPAC, Argus, CPCB notifications, company annual reports",
)

c(
    id="bitumen", n="Bitumen", sym="Bit", fam="oil", tier="B",
    hook="Roads. India builds tens of thousands of kilometres a year and imports a third of the binder.",
    trade=dict(venue="No exchange", bench="Refinery ex-works price lists; import parity", lot="Cargo or tanker",
               terms="INR per tonne domestically; USD per tonne imported", settle="Physical",
               curve="None; strongly seasonal - construction stops in the monsoon", liq="Illiquid"),
    ind=dict(hedge=0, contract="None", basis="Unhedgeable. NHAI contracts increasingly carry price-adjustment clauses indexed to published bitumen rates, which is the effective hedge for road EPC contractors. Checking whether a client's contract book actually carries those clauses, and whether they reset fast enough, is the practical review.",
             dep=30, note="L&T and the road EPC contractors are the exposures; IOC is the dominant domestic supplier."),
    prod=[["Refined globally", 100]],
    use=[["Road construction", 90], ["Roofing and other", 10]],
    imp=[["India", 10], ["Rest of world", 90]],
    drv=["Crude price and refinery configuration", "NHAI and state road-building budgets", "Monsoon timing", "Import parity from Iran, Singapore and the Gulf"],
    stats=[["India import dependence", "~30%", "FY26"]],
    src="PPAC, NHAI, IOC disclosures",
)

c(
    id="gasoline", n="Gasoline", sym="RB", fam="oil", tier="B",
    hook="India's fastest-growing fuel, and the one ethanol blending is deliberately eating into.",
    trade=dict(venue="CME (RBOB) · Platts Singapore (Mogas 92/95)", bench="RBOB for the US; Mogas 92 FOB Singapore for Asia",
               lot="42,000 gallons (RBOB)", terms="USD per gallon; USD per barrel in Asia",
               settle="RBOB physically delivered; Asian exposure via swaps", curve="Seasonal - US driving season sets the summer crack",
               liq="Deep in the US; liquid Asian swaps"),
    ind=dict(hedge=3, contract="No Indian contract",
             basis="Offshore only, and Indian retail prices are administratively smoothed, so the same mismatch as diesel applies. The more relevant Indian variable is the ethanol blending mandate, which is displacing gasoline volume at ~20%.",
             dep=0, note="India is a net exporter of gasoline. Reliance and Nayara are long the crack."),
    prod=[["Refined globally", 100]],
    use=[["Passenger vehicles and two-wheelers", 95], ["Other", 5]],
    imp=[["Rest of world", 100]],
    drv=["Crude and the gasoline crack", "US driving season", "Indian two-wheeler and car sales", "Ethanol blending mandate progress"],
    stats=[["India ethanol blending", "E20 target achieved", "2025-26"]],
    src="PPAC, EIA, MoPNG ethanol blending programme",
)

# ===========================================================================
# GAS, POWER & COAL
# ===========================================================================

c(
    id="lng", n="LNG (JKM)", sym="JKM", fam="gas", tier="A",
    hook="The spot cargo price that decides whether Indian gas utilities and fertiliser plants can run economically.",
    trade=dict(
        venue="ICE · CME (JKM futures) · Platts JKM assessment",
        bench="Platts Japan Korea Marker (JKM); ICE JKM future",
        lot="10,000 MMBtu",
        terms="USD per MMBtu",
        settle="Cash-settled against the monthly average JKM assessment",
        curve="Sharply seasonal with northern winter; the JKM-TTF spread decides whether Atlantic cargoes head to Asia",
        liq="The most liquid LNG contract; open interest grew fast after the 2022 European crisis"),
    ind=dict(
        hedge=3,
        contract="No Indian LNG contract",
        basis="Offshore USD. India's LNG cost is a blend of oil-indexed long-term contracts (Qatar, Australia, US) and spot JKM cargoes, so a pure JKM hedge covers only the spot slice - the long-term slice is indexed to a lagged Brent slope and needs a Brent hedge instead. Splitting a client's gas book into its two pricing regimes and hedging each with the right instrument is a clean, high-value piece of work; several Indian gas buyers hedge the whole book with one instrument and wonder why effectiveness testing fails.",
        dep=50,
        note="Petronet LNG, GAIL, Gujarat Gas, IGL and the gas-based fertiliser plants are the exposures. Gujarat Gas's industrial customers switch to propane or coal gasifiers when spot LNG runs hot, so volume risk compounds price risk."),
    prod=[["United States", 22], ["Qatar", 20], ["Australia", 20], ["Russia", 7], ["Rest of world", 31]],
    use=[["Power generation", 40], ["Industrial", 30], ["City gas and residential", 20], ["Fertiliser and other", 10]],
    imp=[["China", 20], ["Japan", 17], ["South Korea", 12], ["India", 7], ["European Union", 25], ["Rest of world", 19]],
    drv=["Northern-hemisphere winter severity", "European storage levels and TTF, which compete for the same cargoes",
         "US export terminal commissioning and outages", "Qatari North Field expansion volumes", "Chinese industrial demand and domestic production",
         "Panama and Suez transit constraints", "Indian price-elasticity - Indian buyers step away above roughly $10-12/MMBtu"],
    stats=[["India import dependence for gas", "~50%", "FY26"], ["Indian buyer price sensitivity", "demand destruction above ~$10-12/MMBtu", "indicative"],
           ["Contract mix", "long-term oil-indexed plus spot JKM", "structural"]],
    src="IEA Gas Market Report, PPAC, Platts methodology, ICE contract specification",
)

c(
    id="natgas", n="Natural Gas (Henry Hub)", sym="HH", fam="gas", tier="A",
    hook="The US benchmark - relevant to India as the cost basis for the LNG cargoes it buys on US-linked contracts.",
    trade=dict(venue="CME (Henry Hub) · ICE · MCX", bench="CME Henry Hub future", lot="10,000 MMBtu (CME); 1,250 MMBtu (MCX)",
               terms="USD per MMBtu", settle="CME physically deliverable at Henry Hub; MCX cash-settled against NYMEX",
               curve="Extremely seasonal; winter strips carry large premia", liq="Deep"),
    ind=dict(hedge=4, contract="MCX Natural Gas (1,250 MMBtu) and Natural Gas Mini, INR, cash-settled against NYMEX",
             basis="An MCX Henry Hub hedge is only relevant to a client whose LNG contract is Henry-Hub-indexed (US offtake, typically HH x 1.15 + liquefaction fee). For Qatari or Australian oil-indexed cargoes it is the wrong instrument entirely. Establishing which index each contract in the book actually references is step one of any Indian gas hedging review - and it is more often unclear than not.",
             dep=50, note="India's domestic APM gas is administered, not market-priced, which is a third pricing regime again."),
    prod=[["United States", 25], ["Russia", 15], ["Iran", 6], ["China", 6], ["Qatar", 4], ["Rest of world", 44]],
    use=[["Power generation", 40], ["Industrial", 30], ["Residential and commercial", 20], ["Feedstock", 10]],
    imp=[["European Union", 25], ["China", 15], ["Japan", 12], ["Rest of world", 48]],
    drv=["US weather and heating/cooling degree days", "Associated gas from shale oil drilling", "LNG export terminal feedgas demand",
         "Storage injection and withdrawal season", "Data-centre power demand as a new structural driver"],
    stats=[["US share of world production", "~25%", "2025"], ["India domestic production share of consumption", "~50%", "FY26"]],
    src="EIA, IEA, CME and MCX contract specifications",
)

c(
    id="apmgas", n="Domestic APM Gas", sym="APM", fam="gas", tier="B",
    hook="India's administered gas price - set by formula, capped by policy, and immune to hedging.",
    trade=dict(venue="No exchange", bench="Government notified price, revised periodically; ceiling linked to a share of the Indian crude basket",
               lot="n/a", terms="USD per MMBtu", settle="Allocation by priority sector",
               curve="None", liq="Not traded - administratively allocated"),
    ind=dict(hedge=0, contract="None",
             basis="Unhedgeable by design. The risk is allocation policy: how much APM gas a city gas distributor receives at the administered price versus how much it must buy at market rates. That allocation has been cut repeatedly, and each cut is a direct margin event for IGL and MGL. The advisory work is scenario-modelling allocation cuts, not hedging.",
             dep=0, note="Because the ceiling references the Indian crude basket, APM gas is indirectly oil-linked - a subtle point that matters when modelling correlation."),
    prod=[["India (ONGC, OIL)", 100]],
    use=[["City gas distribution (CNG and PNG domestic)", 45], ["Fertiliser", 30], ["Power", 15], ["Other", 10]],
    imp=[["n/a", 100]],
    drv=["Government price notification and formula revisions", "Sector allocation priority decisions", "ONGC and OIL field output decline", "New KG basin volumes"],
    stats=[["Pricing", "administered formula with a ceiling", "policy"], ["Priority allocation", "CGD domestic and CNG first", "policy"]],
    src="MoPNG / PPAC notifications, PNGRB",
)

c(
    id="coal", n="Thermal Coal", sym="NEWC", fam="gas", tier="A",
    hook="India's most-produced commodity and still its second-largest import by volume.",
    trade=dict(venue="ICE (Newcastle) · CME · Platts and Argus assessments",
               bench="Newcastle 6,000 kcal FOB Australia; Indonesian 4,200 kcal FOB for the Indian import grade",
               lot="1,000 t", terms="USD per tonne", settle="Cash-settled against the index",
               curve="Seasonal on Asian summer and winter demand", liq="Newcastle is the liquid seaborne benchmark"),
    ind=dict(
        hedge=3,
        contract="No Indian coal contract",
        basis="The liquid benchmark is Newcastle 6,000 kcal; India imports mostly Indonesian 4,200 kcal low-CV coal for power and higher grades for cement and sponge iron. Those two prices decoupled sharply through the 2022 energy crisis, so a Newcastle hedge against an Indonesian purchase carries a calorific-value basis of real size. A calorific-adjusted hedge ratio is the correct construction and is straightforward to build once someone bothers.",
        dep=25,
        note="Coal India supplies roughly three-quarters of domestic need at notified prices; e-auction premia are the marginal domestic price signal. Adani Power, Tata Power and JSW Energy carry the imported leg."),
    prod=[["China", 52], ["India", 12], ["Indonesia", 9], ["United States", 6], ["Australia", 6], ["Rest of world", 15]],
    use=[["Power generation", 65], ["Cement", 10], ["Steel (non-coking) and sponge iron", 12], ["Industrial and other", 13]],
    imp=[["China", 25], ["India", 20], ["Japan", 12], ["Rest of world", 43]],
    drv=["Chinese and Indian power demand and hydro availability", "Indonesian domestic market obligation and export policy",
         "Australian weather and rail capacity", "Gas prices - coal and gas compete for the same power dispatch", "Indian monsoon and peak summer load", "Coal India production and rake availability"],
    stats=[["India output", "~1,050 Mt", "FY26"], ["Coal India share of domestic supply", "~75%", "FY26"],
           ["India import volume", "~250 Mt", "FY26"], ["Coal share of Indian generation", "~70%", "FY26"]],
    src="Ministry of Coal, CEA, IEA Coal Report, ICE contract specification",
)

c(
    id="metcoal", n="Coking Coal", sym="CKC", fam="gas", tier="A",
    hook="India is the largest seaborne importer, buys 85% of it from Australia, and has no domestic substitute.",
    trade=dict(
        venue="SGX (dominant) · CME · DCE (China)",
        bench="SGX coking coal future, cash-settled against Platts Premium Hard Coking Coal FOB Australia",
        lot="100 t",
        terms="USD per tonne",
        settle="Cash-settled against the Platts FOB Australia index",
        curve="Driven by steel demand, Australian weather and mine outages, and freight",
        liq="SGX is the liquid seaborne benchmark; the contract complements iron ore for steel-margin hedging"),
    ind=dict(
        hedge=3,
        contract="No Indian contract",
        basis="A genuinely usable hedge exists and Indian steelmakers underuse it. SGX premium HCC FOB Australia matches the actual Indian import grade and origin closely - basis here is far smaller than for thermal coal or nickel. The obstacles are the offshore USD leg, RBI permission, and a board that has never approved commodity derivatives. Combined with an iron ore hedge on the same venue, a steelmaker can construct a synthetic steel-spread hedge, which is the single most valuable structure available to Tata Steel, JSW, SAIL and JSPL - and none of them runs it at scale.",
        dep=85,
        note="Australia supplies the large majority of Indian imports. Cyclone season (roughly November to April) is a recurring supply event that is predictable enough to position around."),
    prod=[["Australia", 52], ["United States", 17], ["Canada", 10], ["Rest of world", 21]],
    use=[["Coke for blast-furnace steelmaking", 90], ["PCI and other", 10]],
    imp=[["India", 25], ["Japan and South Korea", 20], ["China", 18], ["Rest of world", 37]],
    drv=["Global blast-furnace steel output", "Australian weather - cyclones and Queensland flooding", "Indian and Chinese import demand",
         "Freight and the Australian dollar", "Long-run substitution toward scrap-based electric-arc steel"],
    stats=[["Australia share of seaborne exports", "over half", "2024"], ["India share of seaborne imports", "largest single importer", "2025"],
           ["India import dependence", "~85%", "FY26"], ["Coking coal per tonne of BF steel", "~0.7 t", "structural"]],
    src="Ministry of Steel, Platts methodology, SGX contract specification",
)

c(
    id="elec", n="Electricity", sym="PWR", fam="gas", tier="A",
    hook="A commodity that cannot be stored, and in India one whose price is half market and half regulated tariff.",
    trade=dict(
        venue="IEX and PXIL (India) · EEX and Nord Pool (Europe) · PJM and ERCOT (US)",
        bench="IEX Day-Ahead Market area clearing price; Real-Time and Term-Ahead segments",
        lot="1 MWh (15-minute blocks on IEX)",
        terms="INR per kWh (paise per unit) on IEX",
        settle="Physical delivery through the grid; financially settled contracts are limited in India",
        curve="Extreme intraday and seasonal shape; Indian prices are capped at Rs 10/kWh by regulation",
        liq="IEX day-ahead is liquid; Indian electricity derivatives only began listing in 2025 and remain shallow"),
    ind=dict(
        hedge=2,
        contract="Electricity futures listed on MCX and NSE from 2025; open interest still building",
        basis="Indian power has just become hedgeable, and almost nobody has adopted it. Most industrial consumers still buy under long-term PPAs or state tariffs where the risk is regulatory, not market - so the first question is whether a client's power cost is even exposed to the exchange price. For open-access and merchant consumers it now is, and the new futures are a genuinely new tool. The Rs 10/kWh price cap truncates the upside distribution, which matters for any VaR calculation: the tail is administratively clipped.",
        dep=0,
        note="Indian grid is roughly 70% coal-fired, so power price and coal price are tightly linked. Aluminium smelters, ferroalloys and electrolysis-based chemicals are the concentrated exposures."),
    prod=[["India generation mix - coal", 70], ["Renewables", 15], ["Hydro", 8], ["Nuclear and gas", 7]],
    use=[["Industrial", 42], ["Domestic", 25], ["Agriculture", 17], ["Commercial and other", 16]],
    imp=[["n/a", 100]],
    drv=["Coal availability and stock at plants", "Peak summer demand and monsoon timing", "Hydro and renewable generation", "Regulatory price caps and DISCOM payment health", "Open access policy"],
    stats=[["Coal share of Indian generation", "~70%", "FY26"], ["IEX price cap", "Rs 10/kWh", "regulatory"],
           ["Electricity derivatives", "listed 2025, thin", "2026"]],
    src="CEA, IEX, CERC, SEBI and CERC derivative notifications",
)

c(
    id="ttf", n="Europe TTF Gas", sym="TTF", fam="gas", tier="B",
    hook="Europe's gas benchmark, and the price that competes for every LNG cargo India wants.",
    trade=dict(venue="ICE · EEX", bench="ICE Dutch TTF future", lot="1 MWh per day per contract month",
               terms="EUR per MWh", settle="Physical delivery at the TTF virtual hub",
               curve="Steeply seasonal; storage-driven", liq="Deep - Europe's primary gas hedging venue"),
    ind=dict(hedge=3, contract="No Indian contract", basis="Relevant to Indian buyers indirectly: TTF sets the opportunity cost of a US cargo. Directly relevant to Indian companies with European operations (Tata Steel Netherlands, pharma and chemical plants in the EU), where it is a genuine EUR-denominated cost hedged on ICE.",
             dep=0, note="EUR exposure means the hedge has a currency leg into EUR, not USD - a different RBI conversation."),
    prod=[["Norway", 30], ["United States (LNG)", 25], ["Rest of world", 45]],
    use=[["Power", 30], ["Industrial", 30], ["Heating", 40]],
    imp=[["European Union", 100]],
    drv=["European storage trajectory", "Norwegian pipeline maintenance", "Weather", "Asian competition for cargoes", "Russian residual flows"],
    stats=[["Price unit", "EUR/MWh", "structural"]],
    src="ICE contract specification, ENTSOG",
)

# ===========================================================================
# PETROCHEMICALS & NGLs
# ===========================================================================

def petchem(id, n, sym, tier, hook, venue, bench, terms, hedge, basis, dep, note,
            prod, use, imp, drv, stats, src, lot="Cargo / container", settle="Physical against index",
            curve="Tracks the spread over its feedstock", liq="Index-linked contract market; thin exchange volume"):
    c(id=id, n=n, sym=sym, fam="petchem", tier=tier, hook=hook,
      trade=dict(venue=venue, bench=bench, lot=lot, terms=terms, settle=settle, curve=curve, liq=liq),
      ind=dict(hedge=hedge, contract="No Indian contract" if hedge < 4 else "MCX listed", basis=basis, dep=dep, note=note),
      prod=prod, use=use, imp=imp, drv=drv, stats=stats, src=src)


c(
    id="plastics", n="Polymers (PE / PP / PVC)", sym="PE", fam="petchem", tier="A",
    hook="The aggregate polymer line in almost every Indian cost base - packaging, pipe, auto interiors, paint pails.",
    trade=dict(
        venue="DCE and CZCE (China, the only liquid polymer futures) · CME (thin) · index assessment elsewhere",
        bench="Platts and ICIS CFR Far East Asia / CFR India assessments; DCE LLDPE and PP futures for China",
        lot="5 t (DCE)",
        terms="USD per tonne CFR; RMB per tonne on DCE",
        settle="Physical or cash-settled against the assessment",
        curve="Tracks the spread over naphtha or ethane feedstock; new cracker capacity has kept it compressed",
        liq="Liquid only in China. Outside China this is a contract-and-assessment market, not a futures market"),
    ind=dict(
        hedge=1,
        contract="No Indian polymer contract",
        basis="Effectively unhedgeable from India. DCE contracts are RMB-denominated, onshore-Chinese and closed to most foreign participants; CFR India assessments have no derivative. So a converter buying 40,000 t of polymer a year has no instrument at all. The practical structures are contractual - quarterly formula pricing indexed to a published assessment, or a crude-linked pass-through clause with customers, since polymer correlates to crude at roughly 0.6-0.8 over a quarter. Quantifying that correlation and designing a crude proxy hedge with an explicit basis budget is legitimate advisory work and is one of the more common Indian mid-cap requests.",
        dep=20,
        note="Reliance, IOC, GAIL and Haldia supply most domestic polymer. Converters - packaging, pipes, auto components, paints - are the short side."),
    prod=[["China", 35], ["United States", 15], ["Middle East", 15], ["India", 5], ["Rest of world", 30]],
    use=[["Packaging", 40], ["Construction and pipe", 20], ["Automotive", 10], ["Consumer and electrical", 15], ["Agriculture and other", 15]],
    imp=[["China", 25], ["India", 8], ["Rest of world", 67]],
    drv=["Crude and naphtha feedstock cost", "New cracker capacity, overwhelmingly Chinese and Middle Eastern", "Chinese demand and export pricing",
         "Anti-dumping duties in India", "Packaging and FMCG volumes", "Recycled-content mandates and EPR rules"],
    stats=[["Correlation to crude", "roughly 0.6-0.8 over a quarter", "indicative"], ["India polymer demand growth", "high single digit", "FY26"]],
    src="ICIS, Platts, Chemicals & Petrochemicals Dept, company annual reports",
)

petchem("ethylene", "Ethylene", "C2H4", "B",
        "The most-produced organic chemical on earth and the first molecule out of a cracker.",
        "No liquid exchange; CFR NE Asia assessment", "Platts CFR Northeast Asia ethylene", "USD per tonne",
        1, "No hedge outside index-linked contracts. The relevant number for a cracker operator is the ethylene-naphtha spread, which is the actual margin. Reliance and the Indian crackers manage it through integration rather than derivatives.",
        10, "Integrated producers are naturally hedged; standalone downstream buyers are not.",
        [["China", 30], ["United States", 20], ["Middle East", 15], ["Rest of world", 35]],
        [["Polyethylene", 60], ["Ethylene oxide / glycol", 15], ["PVC (via EDC)", 12], ["Styrene and other", 13]],
        [["China", 40], ["Rest of world", 60]],
        ["Naphtha and ethane feedstock cost", "New cracker start-ups", "Chinese downstream demand", "Cracker turnarounds and outages"],
        [["Ethylene per tonne of PE", "~1.02 t", "structural"]], "ICIS, Platts")

petchem("propylene", "Propylene", "C3H6", "B",
        "Polypropylene's feedstock, increasingly made on purpose rather than as a cracker by-product.",
        "No liquid exchange; CFR China assessment", "Platts CFR China propylene", "USD per tonne",
        1, "Index-linked contracts only. Chinese propane dehydrogenation capacity has changed the supply function - propylene now tracks propane as much as naphtha.",
        15, "Relevant to polypropylene converters, acrylics and oxo-alcohol producers.",
        [["China", 40], ["United States", 15], ["Rest of world", 45]],
        [["Polypropylene", 65], ["Acrylonitrile and oxo-alcohols", 20], ["Propylene oxide and other", 15]],
        [["China", 35], ["Rest of world", 65]],
        ["Propane price via PDH economics", "Naphtha cracker operating rates", "Chinese PP capacity additions", "Refinery FCC yields"],
        [["PDH share of supply", "rising", "2025"]], "ICIS, Platts")

petchem("benzene", "Benzene", "Bz", "B",
        "The aromatic that becomes styrene, phenol, nylon and a long list of Indian specialty-chemical intermediates.",
        "No liquid exchange; FOB Korea assessment", "Platts FOB Korea benzene", "USD per tonne",
        1, "Index-linked. Deepak Nitrite and the Indian aromatics chain price off FOB Korea, so the exposure is a landed-cost formula. No derivative; managed through inventory and back-to-back pricing with customers.",
        45, "Deepak Nitrite, SI Group, phenol and aniline producers are the concentrated Indian exposures.",
        [["China", 30], ["South Korea", 12], ["United States", 10], ["Rest of world", 48]],
        [["Styrene", 30], ["Cumene / phenol", 22], ["Cyclohexane / nylon", 18], ["Aniline and other", 30]],
        [["China", 30], ["India", 8], ["Rest of world", 62]],
        ["Naphtha reformer and cracker yields", "Styrene and phenol operating rates", "Gasoline blending demand, which competes for aromatics", "Chinese capacity"],
        [["India import dependence", "~45%", "FY26"]], "ICIS, Platts, company annual reports")

petchem("methanol", "Methanol", "MeOH", "B",
        "Made from gas or coal, and the swing feedstock for formaldehyde, acetic acid and a growing fuel-blending market.",
        "ZCE (China) · index assessment elsewhere", "CFR China methanol assessment; ZCE methanol future", "USD per tonne",
        2, "The Chinese ZCE contract is liquid but onshore and RMB-denominated. Indian buyers price off CFR India assessments with no derivative. GNFC and Deepak Fertilisers produce domestically; the rest is imported from Iran and the Gulf, which adds a payment-channel risk.",
        90, "India imports the large majority of its methanol. Iranian origin creates sanctions-adjacent banking friction.",
        [["China", 55], ["Iran", 10], ["United States", 6], ["Rest of world", 29]],
        [["Formaldehyde", 25], ["MTO / olefins", 22], ["Acetic acid", 10], ["Fuel blending and MTBE", 25], ["Other", 18]],
        [["China", 45], ["India", 8], ["Rest of world", 47]],
        ["Chinese coal-to-methanol economics", "Natural gas price in the Gulf and Iran", "MTO plant operating rates", "Fuel-blending policy"],
        [["India import dependence", "~90%", "FY26"]], "ICIS, Chemicals & Petrochemicals Dept")

petchem("pta", "PTA", "PTA", "B",
        "Purified terephthalic acid - polyester's main input, and therefore the textile chain's cost anchor.",
        "ZCE (China, liquid) · index assessment", "ZCE PTA future; CFR China PTA assessment", "USD per tonne / RMB per tonne",
        2, "ZCE PTA is one of the most liquid commodity futures in the world, but it is onshore Chinese. Indian polyester producers (Reliance, MCPI, JBF) price off CFR India with no accessible derivative. The exposure is really the PTA-paraxylene spread for integrated players.",
        25, "Polyester and textile chain: Reliance, Garden Silk, and downstream spinners.",
        [["China", 65], ["India", 8], ["South Korea", 5], ["Rest of world", 22]],
        [["Polyester fibre and filament", 75], ["PET resin (bottles)", 25]],
        [["China", 20], ["India", 10], ["Rest of world", 70]],
        ["Paraxylene cost", "Chinese polyester operating rates", "Crude and naphtha", "Textile demand and export orders"],
        [["PTA per tonne of polyester", "~0.86 t", "structural"]], "ICIS, ZCE contract specification")

petchem("meg", "Ethylene Glycol", "MEG", "B",
        "Polyester's other input, and the antifreeze molecule.",
        "DCE (China) · index assessment", "DCE ethylene glycol future; CFR China MEG assessment", "USD per tonne",
        2, "DCE contract is onshore Chinese. Indian buyers use CFR India assessments. Reliance's MEG capacity partially integrates the domestic chain.",
        40, "Polyester and PET chain.",
        [["China", 45], ["Middle East", 20], ["United States", 12], ["Rest of world", 23]],
        [["Polyester", 80], ["Antifreeze and other", 20]],
        [["China", 40], ["India", 10], ["Rest of world", 50]],
        ["Ethylene cost", "Chinese coal-to-MEG operating rates", "Polyester demand", "New Middle East capacity"],
        [["MEG per tonne of polyester", "~0.34 t", "structural"]], "ICIS")

petchem("pvc", "PVC", "PVC", "A",
        "Pipes, window profiles and wire insulation - and one of India's largest single chemical import lines.",
        "DCE (China) · index assessment", "CFR India PVC assessment; DCE PVC future", "USD per tonne",
        1, "No accessible derivative for Indian buyers, and India imports over half its PVC. The 2024-26 anti-dumping and BIS quality-control-order cycle has made landed cost a regulatory variable as much as a market one - a BIS certification lapse at a supplier removes that supply overnight regardless of price. For pipe makers this is inventory-and-sourcing risk management, not hedging. Watch the announced domestic capacity additions, which change the structure late-decade.",
        55, "Supreme Industries, Astral, Finolex, Prince Pipes and the agricultural pipe chain are the exposures. Ethylene and chlorine (caustic co-product) are upstream.",
        [["China", 45], ["United States", 15], ["Rest of world", 40]],
        [["Pipes and fittings", 55], ["Profiles and sheets", 20], ["Wire and cable", 12], ["Other", 13]],
        [["India", 12], ["Rest of world", 88]],
        ["Ethylene and EDC cost", "Chinese carbide-route PVC economics", "US Gulf capacity and hurricanes", "Indian anti-dumping duties and BIS quality control orders", "Agricultural and construction demand, monsoon-linked"],
        [["India import dependence", "~55%", "FY26"], ["Agriculture share of Indian PVC demand", "~40% via pipes", "indicative"]],
        "ICIS, DGTR notifications, BIS QCO orders, company annual reports")

petchem("styrene", "Styrene", "SM", "B",
        "Polystyrene, ABS and synthetic rubber's shared building block.",
        "No liquid exchange; index assessment", "CFR China styrene assessment", "USD per tonne",
        1, "Index-linked only. Indian ABS and polystyrene converters import it; the exposure is a landed formula.",
        85, "Appliance and auto-interior plastics; also feeds SBR for tyres.",
        [["China", 40], ["United States", 15], ["South Korea", 10], ["Rest of world", 35]],
        [["Polystyrene and EPS", 45], ["ABS and SAN", 30], ["SBR and latex", 25]],
        [["China", 30], ["India", 6], ["Rest of world", 64]],
        ["Benzene and ethylene cost", "Chinese capacity", "Appliance and auto demand"],
        [["India import dependence", "~85%", "FY26"]], "ICIS")

petchem("vam", "Vinyl Acetate Monomer", "VAM", "A",
        "A single molecule that is a double-digit share of India's largest adhesives business.",
        "No exchange", "CFR India / CFR SE Asia VAM assessment", "USD per tonne",
        0, "Completely unhedgeable, wholly imported, and unusually concentrated in one Indian company's cost base. Pidilite's VAM exposure is the textbook case for why single-input concentration deserves its own board metric: no derivative, no domestic supply, and a price that has moved by multiples on plant outages in Taiwan, the US and Saudi Arabia. The only levers are inventory policy, supplier diversification, and pricing power at the customer end - and Pidilite has the last one, which is why it survives the exposure. A client without pricing power and the same concentration would not.",
        100, "Pidilite is the concentrated exposure; also relevant to paints, textiles and packaging adhesives.",
        [["United States", 25], ["China", 25], ["Taiwan", 12], ["Saudi Arabia", 10], ["Rest of world", 28]],
        [["Adhesives (PVA emulsions)", 45], ["EVA and films", 25], ["Textiles and paper coating", 20], ["Other", 10]],
        [["India", 8], ["Rest of world", 92]],
        ["Global plant outages - the market is short of redundancy", "Ethylene and acetic acid feedstock", "Solar EVA encapsulant demand, a fast-growing new draw", "Chinese export availability"],
        [["India import dependence", "~100%", "FY26"], ["Share of Pidilite input cost", "material single-digit to low-double-digit %", "indicative"]],
        "ICIS, company annual reports")

petchem("carbonblack", "Carbon Black", "CB", "A",
        "Crude-derived reinforcing filler, roughly a quarter of a tyre by weight.",
        "No exchange", "Producer contract price indexed to carbon black feedstock oil", "USD or INR per tonne",
        1, "No derivative. Carbon black contracts are typically indexed quarterly to carbon black feedstock oil (CBFO), a heavy refinery stream - so a tyre maker's exposure is effectively a lagged crude exposure with a formula in between. That lag is the interesting part: it creates a predictable one-quarter margin squeeze when crude rises fast, which is forecastable and therefore plannable even without a hedge.",
        20, "Apollo, MRF, CEAT, JK Tyre and Balkrishna carry it. PCBL, Himadri and Birla Carbon are the Indian producers - long the spread.",
        [["China", 45], ["India", 10], ["United States", 8], ["Rest of world", 37]],
        [["Tyres", 70], ["Industrial rubber goods", 20], ["Pigments and plastics", 10]],
        [["Rest of world", 100]],
        ["Carbon black feedstock oil price, which tracks crude", "Tyre production volumes", "Chinese export pricing and anti-dumping duties", "Emission norms on production"],
        [["Share of tyre raw material cost", "~10-12%", "indicative"], ["Carbon black per tyre", "~25% of weight", "structural"]],
        "ICIS, ATMA, company annual reports")

petchem("caustic", "Caustic Soda", "NaOH", "B",
        "The chlor-alkali co-product whose economics are set by what happens to the chlorine nobody wants.",
        "No exchange", "Domestic ex-works and CFR India assessments", "INR or USD per tonne",
        0, "Unhedgeable. Power is roughly half the production cost, so caustic is another electricity derivative. The chlorine co-product cannot be stored economically, which means caustic supply is driven by chlorine demand - a genuinely counterintuitive dynamic worth explaining to a client who assumes supply responds to caustic price.",
        15, "Alumina refining, textiles, soaps and paper are the demand side. GACL, DCM Shriram, Grasim and Chemplast are the Indian producers.",
        [["China", 45], ["United States", 12], ["India", 6], ["Rest of world", 37]],
        [["Alumina refining", 20], ["Organic and inorganic chemicals", 25], ["Pulp and paper", 15], ["Textiles and soaps", 20], ["Other", 20]],
        [["Rest of world", 100]],
        ["Power tariffs", "Chlorine demand, especially PVC", "Alumina refinery run rates", "Chinese export availability", "Anti-dumping duties"],
        [["Power share of production cost", "~50%", "indicative"]], "AMAI, ICIS")

petchem("sodaash", "Soda Ash", "SA", "B",
        "Glass, detergent and lithium processing - a quiet market that solar glass has made interesting.",
        "No exchange", "Domestic ex-works and CFR India assessments", "INR or USD per tonne",
        0, "Unhedgeable. Natural (trona) soda ash from Wyoming and Turkey competes with synthetic Solvay-route production; the cost gap is structural, so import parity sets the Indian ceiling.",
        25, "Tata Chemicals and GHCL are domestic producers - long the price. Detergent and glass makers are short it.",
        [["China", 40], ["United States", 25], ["Turkey", 10], ["India", 5], ["Rest of world", 20]],
        [["Glass (container and flat)", 50], ["Detergents", 18], ["Chemicals", 15], ["Solar glass and lithium processing", 10], ["Other", 7]],
        [["Rest of world", 100]],
        ["Solar glass capacity build-out", "Chinese capacity additions", "Natural gas and energy cost for synthetic routes", "Detergent and container glass demand"],
        [["India import dependence", "~25%", "FY26"]], "ANSAC, company annual reports")

petchem("sbr", "Synthetic Rubber", "SBR", "B",
        "The crude-derived half of a tyre's elastomer mix, and the reason rubber prices track oil.",
        "No liquid exchange (SHFE lists butadiene rubber)", "CFR SE Asia SBR and butadiene assessments", "USD per tonne",
        1, "No accessible derivative. Butadiene feedstock ties it to crackers and therefore to crude. Substitution between natural and synthetic rubber is the practical margin lever for tyre makers, and the switching economics are worth modelling.",
        60, "Tyre and footwear makers. Reliance and Indian Synthetic Rubber produce domestically at limited scale.",
        [["China", 35], ["United States", 12], ["South Korea", 10], ["Rest of world", 43]],
        [["Tyres", 60], ["Footwear and industrial goods", 25], ["Latex and adhesives", 15]],
        [["Rest of world", 100]],
        ["Butadiene and crude cost", "Natural rubber price - the substitute", "Tyre production", "Chinese capacity"],
        [["India import dependence", "~60%", "FY26"]], "IISRP, ATMA")

petchem("phenol", "Phenol & Acetone", "Ph", "B",
        "Cumene-route twins - one drives laminates and resins, the other solvents and pharma.",
        "No exchange", "CFR India phenol and acetone assessments", "USD per tonne",
        1, "Index-linked. Deepak Nitrite's phenol-acetone plant reduced Indian import dependence sharply; residual exposure sits with laminate, plywood and pharma users.",
        35, "Phenolic resins for plywood and laminates; acetone for pharma solvents.",
        [["China", 40], ["United States", 15], ["Rest of world", 45]],
        [["Bisphenol-A and epoxy", 40], ["Phenolic resins", 30], ["Caprolactam and other", 30]],
        [["China", 30], ["India", 6], ["Rest of world", 64]],
        ["Benzene and propylene cost", "Chinese BPA capacity", "Plywood and laminate demand", "Anti-dumping duties"],
        [["India import dependence", "~35% and falling", "FY26"]], "ICIS, company annual reports")

petchem("api", "Pharma APIs & KSMs", "API", "A",
        "Active ingredients and key starting materials - India makes the medicines and China makes what goes into them.",
        "No exchange", "Bilateral contract and tender pricing", "USD per kg",
        0, "Unhedgeable, and mis-framed if treated as price risk. The exposure is single-country dependence: China supplies 70% or more of Indian imports for many molecules, and the risk that materialises is availability - an export restriction, an environmental shutdown in Hebei, or a customs slowdown - not a price move. Fermentation-based APIs (antibiotics, some vitamins) are the most concentrated. The Production Linked Incentive scheme for bulk drugs is the policy response and is slowly changing the picture for a specific list of molecules. Advisory work here is supply-chain mapping and dual-sourcing economics, plus scenario modelling of a 60-90 day supply interruption against a product portfolio.",
        70, "Sun, Cipla, Dr Reddy's, Lupin, Aurobindo, Torrent and Zydus all carry it. Divi's and the CDMO names are on the other side, selling into it.",
        [["China", 55], ["India", 20], ["European Union", 10], ["Rest of world", 15]],
        [["Formulation manufacture", 100]],
        [["India", 20], ["United States", 15], ["European Union", 15], ["Rest of world", 50]],
        ["Chinese environmental enforcement and plant shutdowns", "Chinese export policy", "US FDA and EU GMP inspection outcomes at supplier sites",
         "Indian PLI scheme capacity coming online", "Freight and customs clearance times", "Currency - inputs in USD, a large share of revenue in USD too, so there is a natural offset worth quantifying"],
        [["China share of Indian API/KSM imports", "70% or more for many molecules", "2026"],
         ["India share of world generic volume", "~20%", "2025"], ["PLI bulk drug scheme", "targeted at specific KSMs", "policy"]],
        "Department of Pharmaceuticals, DGCIS, company annual reports")

# ===========================================================================
# AGRICULTURE
# ===========================================================================

def ag(id, n, sym, tier, hook, venue, bench, terms, hedge, contract, basis, dep, note,
       prod, use, imp, drv, stats, src, lot="Contract lot", settle="Physical or cash-settled against the spot polling",
       curve="Seasonal around harvest and sowing", liq="Varies by contract"):
    c(id=id, n=n, sym=sym, fam="ag", tier=tier, hook=hook,
      trade=dict(venue=venue, bench=bench, lot=lot, terms=terms, settle=settle, curve=curve, liq=liq),
      ind=dict(hedge=hedge, contract=contract, basis=basis, dep=dep, note=note),
      prod=prod, use=use, imp=imp, drv=drv, stats=stats, src=src)


c(
    id="palm", n="Palm Oil", sym="PO", fam="ag", tier="A",
    hook="India is the world's largest importer of the world's most-produced vegetable oil, and two countries grow almost all of it.",
    trade=dict(
        venue="Bursa Malaysia (FCPO, the global benchmark) · DCE · NCDEX (India, refined palmolein)",
        bench="Bursa Malaysia FCPO crude palm oil future",
        lot="25 t (FCPO); 10 t (NCDEX)",
        terms="MYR per tonne (Bursa); INR per 10 kg (NCDEX)",
        settle="Bursa physically deliverable in Malaysia; NCDEX contracts have had intermittent suspension",
        curve="Seasonal on Malaysian and Indonesian production cycles and the biodiesel mandate calendar",
        liq="FCPO is deeply liquid and the world reference; Indian contracts have been repeatedly suspended by regulators"),
    ind=dict(
        hedge=2,
        contract="NCDEX crude palm oil and refined palmolein - but SEBI suspended agricultural derivatives trading in seven commodities from December 2021, with extensions since",
        basis="This is the sharpest illustration of a risk unique to Indian agri hedging: the regulator can turn the market off. SEBI's suspension of agri derivatives removed the domestic hedging venue for edible oils for years running. That leaves Bursa FCPO, which is offshore, MYR-denominated (not USD - a third currency leg), and prices Malaysian crude palm oil rather than the refined palmolein India actually imports from Indonesia. Currency, grade, origin and regulatory-availability basis all stack. Any client who says 'we hedge palm' should be asked which of those four they are carrying.",
        dep=96,
        note="HUL, Godrej Consumer, AWL Agri, Marico, Britannia, Nestle India and every soap and biscuit maker carry it. Indonesian export levy changes are a recurring shock."),
    prod=[["Indonesia", 58], ["Malaysia", 26], ["Thailand", 4], ["Colombia", 2], ["Rest of world", 10]],
    use=[["Food - cooking oil and processed food", 70], ["Oleochemicals - soaps and surfactants", 20], ["Biodiesel", 10]],
    imp=[["India", 20], ["China", 12], ["European Union", 10], ["Pakistan", 6], ["Rest of world", 52]],
    drv=["Indonesian export levy and domestic biodiesel mandate (B40 and beyond) - the largest single policy lever",
         "Malaysian production cycle and labour availability", "Indian import duty on crude and refined oils",
         "Soybean and sunflower oil prices - substitutes across the whole vegetable-oil complex", "Crude oil price via biodiesel economics",
         "EUDR deforestation traceability requirements for EU-bound flows", "El Nino and La Nina effects on yields"],
    stats=[["India import dependence for edible oil", "~60% overall; palm ~96% imported", "FY26"],
           ["Indonesia + Malaysia share", "~84% of world output", "2025"],
           ["EUDR applicability", "large operators from 30 Dec 2026", "policy"],
           ["Indian agri derivatives", "suspended by SEBI since Dec 2021", "regulatory"]],
    src="USDA FAS, MPOB, SEA of India, DGFT notifications, SEBI circulars",
)

ag("cotton", "Cotton", "CT", "A",
   "India grows more cotton than anyone and still cannot hedge it domestically.",
   "ICE (Cotton No. 2, the world benchmark) · ZCE (China) · MCX (India, cotton and Kapas - suspended)",
   "ICE Cotton No. 2 front month; Cotlook A Index for physical", "US cents per pound; INR per bale in India",
   2, "MCX cotton and NCDEX Kapas contracts have been under SEBI's agri-derivative suspension",
   "Same regulatory problem as edible oils, and it bites harder because cotton is 55-65% of a spinner's cost. ICE Cotton No. 2 is liquid but prices US upland cotton delivered to US warehouses; Indian Shankar-6 trades at its own basis to Cotlook A, which itself trades at a basis to ICE. Add the MSP floor from the Cotton Corporation of India, which truncates the downside in a way no futures curve reflects, and a naive ICE hedge against an Indian purchase is close to uncorrelated in bad years. For most Indian spinners the honest structure is inventory policy plus back-to-back yarn contracts, not a derivative.",
   0, "Vardhman, KPR Mill, Arvind, Welspun Living, Trident and Page Industries carry it. India is a net exporter in surplus years, importer in deficit years - the direction flips.",
   [["India", 24], ["China", 23], ["United States", 13], ["Brazil", 13], ["Rest of world", 27]],
   [["Apparel and home textiles", 85], ["Industrial and medical", 15]],
   [["China", 25], ["Vietnam", 18], ["Bangladesh", 15], ["Rest of world", 42]],
   ["Indian monsoon and Gujarat/Maharashtra sowing", "Pink bollworm infestation, a recurring Indian yield risk",
    "Chinese state reserve buying and selling", "MSP and Cotton Corporation of India procurement, which sets a floor",
    "US export sales and Brazilian crop", "Polyester price - the substitute", "Xinjiang import bans in the US and EU, which reroute trade"],
   [["India share of world output", "~24%", "2025-26"], ["Share of spinner cost", "~55-65%", "indicative"],
    ["Indian derivatives status", "suspended", "regulatory"]],
   "USDA FAS, Cotton Association of India, ICE contract specification, SEBI circulars")

ag("sugar", "Sugar", "SB", "A",
   "A commodity whose Indian price is set by policy - MSP, export quotas and ethanol diversion - more than by the world market.",
   "ICE (No. 11 raw, No. 5 white) · NCDEX (suspended)", "ICE Sugar No. 11 raw", "US cents per pound",
   2, "NCDEX sugar under SEBI suspension",
   "The world price and the Indian price are only loosely connected. India sets a Fair and Remunerative Price for cane, a minimum selling price for sugar, and an export quota - three administered levers that dominate mill economics. On top of that, ethanol diversion policy decides how much cane becomes sugar at all. Hedging ICE No. 11 against an Indian mill's economics would be close to meaningless. The right analysis is policy scenario modelling: what happens to the mill's realisation under each combination of FRP increase, MSP revision, export quota and ethanol procurement price.",
   0, "Balrampur Chini, Shree Renuka, Triveni, Dalmia Bharat Sugar are the exposures; Varun Beverages, Nestle India, Britannia and Hindustan Unilever are on the buy side.",
   [["Brazil", 22], ["India", 18], ["Thailand", 7], ["China", 6], ["Rest of world", 47]],
   [["Direct consumption and food processing", 70], ["Beverages", 20], ["Other", 10]],
   [["Indonesia", 10], ["China", 8], ["Rest of world", 82]],
   ["Brazilian centre-south crush and the sugar-versus-ethanol mix", "Indian export quota decisions and ethanol diversion",
    "Indian monsoon and Maharashtra/UP cane yields", "Thai crop", "Crude price via Brazilian ethanol parity", "FRP and MSP revisions"],
   [["India share of world output", "~18%", "2025-26"], ["Ethanol diversion", "a policy-set share of cane", "FY26"],
    ["Cane price", "administered FRP", "policy"]],
   "ISMA, USDA FAS, Department of Food and Public Distribution, ICE contract specification")

ag("wheat", "Wheat", "W", "B",
   "India's second staple, export-banned since 2022, and priced by procurement policy rather than by Chicago.",
   "CBOT (the world benchmark) · Euronext (Matif) · NCDEX (suspended)", "CBOT wheat front month", "US cents per bushel",
   1, "NCDEX wheat under SEBI suspension",
   "India's wheat market is effectively closed to the world - exports banned since May 2022, imports subject to duty - so CBOT is not a hedge, it is background information. Indian wheat price is set by MSP, FCI procurement and open market sale scheme releases. ITC, Britannia and the flour millers manage it through procurement timing and forward contracts with farmers, not derivatives.",
   0, "ITC, Britannia, Nestle India and the biscuit and flour chain.",
   [["China", 17], ["India", 14], ["Russia", 11], ["United States", 6], ["Rest of world", 52]],
   [["Food - flour and processed", 70], ["Feed", 20], ["Seed and other", 10]],
   [["Egypt", 6], ["Indonesia", 6], ["Rest of world", 88]],
   ["Indian rabi sowing area and February-March heat, which has cut yields repeatedly", "MSP and FCI procurement volumes",
    "Export ban policy", "Black Sea supply and the Russian export tax", "Open Market Sale Scheme releases"],
   [["India export status", "banned since May 2022", "policy"], ["India output", "~110-115 Mt", "FY26"]],
   "Ministry of Agriculture, FCI, USDA FAS")

ag("rice", "Rice", "RR", "B",
   "India is the largest exporter, so Indian export policy is world rice policy.",
   "CBOT (rough rice, thin) · Thai and Vietnamese FOB assessments", "Thai 5% broken white rice FOB",
   "USD per tonne", 1, "No usable Indian contract",
   "Effectively unhedgeable. India's export restrictions on non-basmati white rice in 2023 and their partial rollback moved world prices more than any weather event that year. The exposure for Indian exporters is policy timing, not price.",
   0, "KRBL, LT Foods and the basmati exporters; also relevant to food processors.",
   [["India", 25], ["China", 24], ["Bangladesh", 7], ["Indonesia", 7], ["Rest of world", 37]],
   [["Direct food consumption", 90], ["Processing and other", 10]],
   [["Philippines", 12], ["Nigeria", 6], ["Rest of world", 82]],
   ["Indian export policy - bans, duties and minimum export prices", "Monsoon and kharif sowing", "MSP and FCI stocks", "El Nino"],
   [["India share of world rice exports", "~40%", "2025"]], "Ministry of Agriculture, USDA FAS, APEDA")

ag("maize", "Maize / Corn", "C", "B",
   "Feed grain turned ethanol feedstock - India's blending programme changed its demand curve.",
   "CBOT (world benchmark) · NCDEX (suspended)", "CBOT corn front month", "US cents per bushel",
   1, "NCDEX maize under SEBI suspension",
   "CBOT corn is the world's most liquid grain contract but prices US Midwest corn. India's maize price is now driven by domestic ethanol distillery demand under the blending programme, which has structurally tightened the feed market and pushed India from exporter to importer in some years. Poultry and starch users feel it directly.",
   5, "Poultry feed, starch (Gujarat Ambuja Exports), and ethanol distillers.",
   [["United States", 31], ["China", 24], ["Brazil", 11], ["India", 3], ["Rest of world", 31]],
   [["Animal feed", 60], ["Ethanol and industrial starch", 30], ["Food", 10]],
   [["Mexico", 10], ["Japan", 9], ["Rest of world", 81]],
   ["US Midwest weather", "Indian ethanol blending demand for grain-based distilleries", "Poultry cycle", "Import duty decisions"],
   [["Ethanol programme", "grain-based distillery demand is now a structural draw", "FY26"]], "USDA FAS, Ministry of Agriculture")

ag("soyoil", "Soybean Oil", "BO", "B",
   "The second leg of India's edible oil import bill, and the swing substitute for palm.",
   "CBOT · Bursa (via palm spread) · NCDEX (suspended)", "CBOT soybean oil front month", "US cents per pound",
   2, "NCDEX refined soy oil under SEBI suspension",
   "CBOT soyoil is liquid and USD-denominated, and correlates well with Indian landed soy oil - better than the palm chain does, because origin (Argentina, Brazil, US) is more diverse. It remains an offshore hedge with an FX leg. The palm-soy spread is itself tradeable and is how sophisticated buyers manage substitution.",
   60, "AWL Agri, Ruchi Soya, Marico and the edible oil refiners.",
   [["China", 30], ["United States", 20], ["Brazil", 17], ["Argentina", 13], ["Rest of world", 20]],
   [["Cooking oil and food", 80], ["Biodiesel", 15], ["Industrial", 5]],
   [["India", 20], ["Rest of world", 80]],
   ["South American crop and Argentine export tax policy", "US biofuel policy (RFS and 45Z)", "Palm oil price - the substitute", "Indian import duty"],
   [["India import dependence", "~60%", "FY26"]], "USDA FAS, SEA of India")

ag("sunoil", "Sunflower Oil", "Sun", "B",
   "The Black Sea oil - and a live illustration of how a war reprices an Indian kitchen.",
   "No liquid exchange", "FOB Black Sea sunflower oil assessment", "USD per tonne",
   1, "No Indian contract",
   "Unhedgeable in practice. Ukraine and Russia supply the large majority; the 2022 invasion doubled the landed Indian price within weeks and forced substitution into palm and soy. The exposure is geopolitical availability, and the mitigant is formulation flexibility - the ability to switch oils in a product without reformulating the label.",
   90, "Edible oil refiners and FMCG food makers.",
   [["Ukraine", 30], ["Russia", 27], ["Argentina", 7], ["Rest of world", 36]],
   [["Cooking oil", 90], ["Industrial and other", 10]],
   [["India", 25], ["European Union", 20], ["China", 10], ["Rest of world", 45]],
   ["Black Sea war and export corridor security", "Ukrainian and Russian crop", "Palm and soy substitution", "Indian import duty"],
   [["India import dependence", "~90%", "FY26"]], "USDA FAS, SEA of India")

ag("mustard", "Mustard / Rapeseed", "RS", "B",
   "The domestic oilseed India is trying to grow its way to self-sufficiency with.",
   "NCDEX (mustard seed - suspended) · Euronext rapeseed", "NCDEX mustard seed; Euronext rapeseed", "INR per quintal",
   1, "NCDEX mustard under SEBI suspension",
   "Domestic crop, domestic price, no working derivative. MSP and the National Mission on Edible Oils are the policy drivers.",
   5, "Domestic oil millers; the swing factor for overall Indian edible oil import volume.",
   [["European Union", 25], ["Canada", 20], ["China", 17], ["India", 12], ["Rest of world", 26]],
   [["Cooking oil", 85], ["Meal for feed", 15]],
   [["China", 25], ["Rest of world", 75]],
   ["Indian rabi sowing and MSP", "Canadian canola crop", "Palm and soy substitution"],
   [["India output", "~12 Mt seed", "FY26"]], "Ministry of Agriculture, USDA FAS")

ag("copra", "Copra & Coconut Oil", "Cop", "A",
   "A domestic crop with no derivative that is over a third of one listed company's cost base.",
   "No liquid exchange", "Kochi and Kangeyam market spot prices; MSP for copra", "INR per quintal",
   0, "None - no listed copra or coconut oil contract",
   "There is no financial hedge for copra anywhere. Marico buys a very large share of India's edible-grade copra, so it is simultaneously exposed to the price and large enough to move it. The exposure is managed through procurement timing across the two harvest peaks, storage, and the ability to reprice Parachute at the shelf. Government MSP for copra sets a floor. A concentration like this - single input, no hedge, no substitute, domestic-only supply - is precisely what a board-level input-concentration metric should surface, and almost no Indian risk framework does.",
   0, "Marico is the dominant exposure. Also relevant to soaps, oleochemicals and the FMCG hair-oil category.",
   [["Philippines", 30], ["Indonesia", 28], ["India", 20], ["Rest of world", 22]],
   [["Edible and hair oil", 60], ["Oleochemicals and soaps", 30], ["Other", 10]],
   [["European Union", 25], ["United States", 20], ["Rest of world", 55]],
   ["Kerala, Tamil Nadu and Karnataka harvest cycles", "MSP for copra", "Cyclones and monsoon in the coconut belt",
    "Philippine and Indonesian export supply, which sets the import-parity ceiling", "Substitution into rice bran and other oils"],
   [["India share of world coconut output", "~20%", "2025"], ["Share of Marico input cost", "material - the largest single input", "indicative"],
    ["Hedging instruments available", "none", "structural"]],
   "Coconut Development Board, Ministry of Agriculture, company annual reports")

ag("natrub", "Natural Rubber", "RU", "A",
   "A tropical tree crop with a seven-year lead time, priced in Bangkok and Tokyo, and 40% imported by India.",
   "OSE/TOCOM (Japan, RSS3) · SGX and SICOM (TSR20, the tyre grade) · Bursa · MCX (India)",
   "SICOM TSR20 for the tyre-grade benchmark; TOCOM RSS3 for the traditional contract",
   "USD cents per kg (SICOM); JPY per kg (TOCOM); INR per 100 kg (MCX)",
   3, "MCX has listed rubber contracts with limited liquidity; SICOM TSR20 is the practical hedge",
   "A rare case where a well-matched offshore hedge exists: SICOM TSR20 prices exactly the technically specified grade Indian tyre makers import. It is USD-denominated and offshore, so the RBI permission and FX leg apply, but the grade basis is small. Kerala domestic RSS4 is a different, thinner market with its own price - so a tyre maker with a mixed domestic-and-imported book needs a partial hedge ratio, not a full one. Working out that ratio from the actual procurement mix is a concrete deliverable.",
   40, "Apollo, MRF, CEAT, JK Tyre and Balkrishna. Kerala smallholders supply the domestic leg; ANRPC countries supply the rest.",
   [["Thailand", 33], ["Indonesia", 22], ["Vietnam", 9], ["India", 6], ["Rest of world", 30]],
   [["Tyres", 70], ["Gloves, footwear and industrial goods", 30]],
   [["China", 40], ["India", 8], ["European Union", 8], ["Rest of world", 44]],
   ["Thai and Indonesian weather, leaf disease and tapping economics", "Chinese tyre and vehicle demand",
    "Crude price via synthetic rubber substitution", "Indian import duty and the Rubber Board's stance",
    "EUDR traceability requirements for EU-bound rubber goods", "Long lead time on new planting - supply cannot respond within seven years"],
   [["ANRPC share of world output", "~70%", "2025"], ["India import dependence", "~40%", "FY26"],
    ["Share of tyre raw material cost", "~25-30% including synthetic", "indicative"], ["EUDR", "rubber is an in-scope commodity", "policy"]],
   "ANRPC, Rubber Board of India, ATMA, SGX contract specification")

ag("cocoa", "Cocoa", "CC", "A",
   "Two West African countries grow most of it, and the 2024 price explosion is still working through Indian confectionery costs.",
   "ICE US (New York) · ICE Europe (London)", "ICE New York cocoa; ICE London cocoa", "USD per tonne; GBP per tonne",
   3, "No Indian contract",
   "ICE cocoa is liquid and hedgeable offshore, but the 2024-25 episode showed what happens when a hedger is on the wrong side of a genuine supply failure: margin calls on short hedges bankrupted physical traders even as the physical position gained. That liquidity risk on the hedge itself is a real treasury consideration, not a theoretical one, and it belongs in any hedge-policy document that authorises futures.",
   75, "Nestle India, Mondelez India, Britannia and the chocolate category. Small domestic crop in Kerala, Andhra and Tamil Nadu.",
   [["Cote d'Ivoire", 38], ["Ghana", 15], ["Ecuador", 9], ["Indonesia", 5], ["Rest of world", 33]],
   [["Chocolate confectionery", 80], ["Beverages, bakery and cosmetics", 20]],
   [["European Union", 35], ["United States", 15], ["Rest of world", 50]],
   ["West African weather, black pod and swollen shoot disease", "Cote d'Ivoire and Ghana farmgate price setting",
    "Grinding data as the demand indicator", "EUDR traceability, which West African smallholder supply struggles to meet",
    "Speculative positioning - the market is small enough to be moved by it"],
   [["West Africa share", "~55-60%", "2025"], ["Price move 2023-24", "roughly a trebling", "2024"],
    ["India import dependence", "~75%", "FY26"], ["EUDR", "cocoa is an in-scope commodity", "policy"]],
   "ICCO, Directorate of Cashewnut and Cocoa Development, ICE contract specification")

ag("coffee", "Coffee", "KC", "A",
   "India grows shade-arabica and robusta in Karnataka and exports most of it - which makes it long, not short.",
   "ICE US (Arabica, contract C) · ICE Europe (Robusta)", "ICE Arabica C; ICE Robusta",
   "US cents per pound (Arabica); USD per tonne (Robusta)", 3, "No Indian contract",
   "Liquid offshore hedges exist for both grades. Indian growers and exporters are long, so the hedge direction is a short - the opposite of most Indian commodity exposure and a useful reminder that hedge policy has to specify direction, not just instrument. Tata Consumer's roasting business is on the buy side, so a group with both faces a natural internal offset that is often not netted.",
   0, "Tata Coffee/Tata Consumer, CCL Products and the Karnataka growers. Nestle India is on the buy side.",
   [["Brazil", 38], ["Vietnam", 17], ["Colombia", 8], ["Indonesia", 7], ["India", 4], ["Rest of world", 26]],
   [["Roast and ground", 60], ["Instant/soluble", 30], ["Other", 10]],
   [["European Union", 30], ["United States", 18], ["Rest of world", 52]],
   ["Brazilian frost and drought - the dominant single risk", "Vietnamese robusta crop", "EUDR traceability for EU-bound beans",
    "Certified stocks on ICE", "Brazilian real, which drives grower selling", "Speculative positioning"],
   [["India output", "~360,000 t", "2025-26"], ["India export share of output", "~70%", "FY26"], ["EUDR", "coffee is an in-scope commodity", "policy"]],
   "Coffee Board of India, ICO, ICE contract specification")

ag("tea", "Tea", "Tea", "B",
   "Sold at auction, not on an exchange - and a market where quality dispersion defeats any single price.",
   "No exchange - auction system", "Kolkata, Guwahati, Coimbatore and Mombasa auction averages", "INR per kg",
   0, "None", "Unhedgeable. Auction pricing plus enormous quality dispersion means there is no single tea price to hedge. Managed through garden ownership, blending flexibility and auction strategy.",
   0, "Tata Consumer, HUL (Brooke Bond, Lipton) on the buy side; the Assam and Nilgiri gardens on the sell side.",
   [["China", 47], ["India", 21], ["Kenya", 8], ["Sri Lanka", 5], ["Rest of world", 19]],
   [["Domestic consumption", 80], ["Export", 20]],
   [["Pakistan", 12], ["Russia", 10], ["Rest of world", 78]],
   ["Assam and Nilgiri weather and pest pressure", "Kenyan crop, the main export competitor", "Plantation wage revisions", "Auction offtake and export demand"],
   [["India share of world output", "~21%", "2025"], ["India domestic consumption share", "~80% of output", "2025"]],
   "Tea Board of India, FAO")

ag("milk", "Dairy", "Milk", "A",
   "India is the world's largest producer, imports almost none, and has no way to hedge any of it.",
   "CME (Class III milk, butter, cheese) · EEX", "CME Class III milk; GDT auction for skim milk powder", "USD per cwt",
   0, "None in India",
   "India's dairy market is domestic, fragmented across cooperatives, and unhedgeable. CME contracts price US milk with no useful relationship to Indian procurement prices. The exposure for a processor is the farmgate procurement price, which moves with fodder cost, monsoon and cooperative competition. Managed through procurement contracts and product-mix shifts between liquid milk, powder and value-added products - the last being the real margin lever.",
   0, "Nestle India, Britannia, Hindustan Unilever, Amul (unlisted), Hatsun, Dodla and Heritage Foods.",
   [["India", 24], ["European Union", 18], ["United States", 12], ["Rest of world", 46]],
   [["Liquid milk", 45], ["Value-added products", 35], ["Powder and commodities", 20]],
   [["China", 15], ["Rest of world", 85]],
   ["Monsoon and fodder availability", "Lumpy skin disease and herd health", "Cooperative procurement price competition",
    "Flush versus lean season", "Import duty on skim milk powder, which insulates the domestic market"],
   [["India share of world milk output", "~24%", "2025"], ["Import dependence", "negligible", "FY26"]],
   "NDDB, Department of Animal Husbandry, FAO")

ag("ethanol", "Ethanol", "EtOH", "A",
   "A fuel whose price the government sets, bought by state refiners from sugar mills and grain distillers.",
   "CME (US ethanol) · B3 (Brazil) · no Indian contract",
   "Government-notified procurement price by feedstock route (C-heavy molasses, B-heavy, juice, damaged grain, maize)",
   "INR per litre", 0, "None",
   "Not a market price at all in India - the Oil Marketing Companies buy at a notified rate that differs by feedstock. So the risk is entirely policy: the rate revision, the allocation among mills, and the blending target trajectory. For a sugar mill this has become the single most important line in the P&L and it is 100% administratively determined. Scenario modelling of procurement-price revisions against a mill's feedstock mix is the useful analysis, and it is a governance and policy question, not a hedging one.",
   0, "Balrampur Chini, Shree Renuka, Triveni, Dalmia Bharat Sugar and the grain-based distillers; IOC, BPCL and HPCL on the buy side.",
   [["United States", 50], ["Brazil", 27], ["European Union", 5], ["India", 5], ["Rest of world", 13]],
   [["Fuel blending", 85], ["Industrial and potable", 15]],
   [["Rest of world", 100]],
   ["Blending mandate trajectory beyond E20", "OMC procurement price notifications by route", "Cane and maize availability",
    "Diversion policy between sugar and ethanol", "Crude price, which sets the economic rationale"],
   [["Blending achieved", "E20", "2025-26"], ["Price mechanism", "administered by feedstock route", "policy"]],
   "MoPNG, Department of Food and Public Distribution, ISMA")

ag("pulp", "Pulp & Paper", "Plp", "B",
   "Wood fibre India does not grow enough of, priced off Latin American hardwood.",
   "No liquid exchange", "BHKP and NBSK index assessments, CIF China and CIF Europe", "USD per tonne",
   1, "No Indian contract",
   "Index-linked contracts only. India imports a large share of its wood pulp from Latin America and Southeast Asia. Agroforestry and captive plantations are the structural mitigant that Indian mills have pursued; ITC's plantation programme is the notable example.",
   50, "ITC (paperboards), JK Paper, West Coast Paper, Century.",
   [["Brazil", 25], ["United States", 15], ["Canada", 10], ["Rest of world", 50]],
   [["Printing and writing paper", 30], ["Packaging board", 40], ["Tissue", 15], ["Specialty and other", 15]],
   [["China", 35], ["India", 5], ["Rest of world", 60]],
   ["Brazilian and Chilean pulp mill capacity", "Chinese buying", "Chinese and Indian packaging demand", "Freight", "Waste paper availability as substitute"],
   [["India import dependence", "~50% of wood pulp", "FY26"]], "IPMA, FAO, RISI")

ag("tobacco", "Leaf Tobacco", "Tob", "B",
   "An auction-platform crop under a statutory board, and a business where taxation dwarfs commodity risk.",
   "No exchange - Tobacco Board auction platforms", "Tobacco Board auction average by grade", "INR per kg",
   0, "None", "Unhedgeable and largely irrelevant next to the real exposure, which is GST and excise policy on cigarettes. A one-off tax change moves ITC's economics by an order of magnitude more than a leaf price move.",
   0, "ITC and Godfrey Phillips. India is the world's second-largest producer and a significant exporter.",
   [["China", 38], ["India", 11], ["Brazil", 11], ["Rest of world", 40]],
   [["Cigarettes", 70], ["Bidi, chewing and other", 30]],
   [["Rest of world", 100]],
   ["Tobacco Board auction volumes and crop size", "GST and excise rates on tobacco products", "Export demand", "Andhra Pradesh and Karnataka weather"],
   [["India rank", "second-largest producer", "2025"]], "Tobacco Board of India, FAO")

ag("spices", "Spices", "Spc", "B",
   "A category India dominates in production and where quality and pesticide-residue compliance beat price as the risk.",
   "NCDEX (turmeric, jeera, coriander - some suspended) · domestic spot markets",
   "NCDEX turmeric and jeera futures; Kochi and Guntur spot", "INR per quintal",
   2, "NCDEX contracts exist for several spices, with intermittent SEBI suspensions",
   "Some Indian spice derivatives remain live, which makes this one of the few agri categories with a functioning domestic hedge. The larger risk is not price but export rejection on pesticide residue and, since 2024, ethylene oxide contamination findings in export markets - a compliance failure that closes a market regardless of price.",
   0, "MDH, Everest (unlisted), Tata Consumer, ITC and the spice exporters.",
   [["India", 43], ["China", 12], ["Rest of world", 45]],
   [["Domestic consumption", 85], ["Export", 15]],
   [["United States", 15], ["Rest of world", 85]],
   ["Monsoon and regional crop cycles", "Export market residue standards and recalls", "Speculative activity in NCDEX contracts", "Global food-service demand"],
   [["India share of world spice output", "~43%", "2025"]], "Spices Board of India, FAO, NCDEX")

ag("shrimp", "Shrimp & Prawns", "Shr", "B",
   "India's largest agri-export by value, sold almost entirely into two markets that keep changing the tariff.",
   "No exchange", "Urner Barry and export contract assessments", "USD per pound",
   0, "None",
   "Unhedgeable. The exposure is trade policy: US antidumping and countervailing duty reviews, plus general tariff action, decide realisation more than the shrimp price does. Ecuadorian competition on cost is the structural pressure. The advisory question is market diversification and duty-scenario modelling.",
   0, "Avanti Feeds, Apex Frozen Foods, Coastal Corporation and the Andhra aquaculture cluster.",
   [["Ecuador", 25], ["India", 18], ["Vietnam", 12], ["Indonesia", 10], ["Rest of world", 35]],
   [["Export - food service and retail", 90], ["Domestic", 10]],
   [["United States", 30], ["China", 22], ["European Union", 15], ["Rest of world", 33]],
   ["US antidumping and countervailing duty rates", "US tariff policy", "Ecuadorian production growth", "Disease outbreaks in ponds", "Feed (fishmeal and soy) cost"],
   [["India share of US shrimp imports", "largest single supplier", "2025"]], "MPEDA, NOAA, USDA")

ag("castor", "Castor Seed & Oil", "Cas", "B",
   "India grows the overwhelming majority of the world's castor, which makes it a price-setter rather than a price-taker.",
   "NCDEX (castor seed) · domestic spot", "NCDEX castor seed future; Gujarat spot", "INR per quintal",
   3, "NCDEX castor seed contract is live",
   "One of the few Indian agri commodities with a functioning domestic futures market. India's near-monopoly means the domestic price is the world price, so the NCDEX contract is a genuinely well-matched hedge - a rare case of no meaningful basis. Useful to point out to clients who assume Indian agri hedging is universally broken.",
   0, "Castor oil derivatives feed lubricants, cosmetics and polyurethanes; Jayant Agro and the Gujarat processors.",
   [["India", 85], ["Mozambique", 5], ["China", 4], ["Rest of world", 6]],
   [["Sebacic acid and lubricants", 40], ["Cosmetics and pharma", 25], ["Polyurethanes and coatings", 35]],
   [["China", 40], ["European Union", 20], ["Rest of world", 40]],
   ["Gujarat sowing and monsoon", "Chinese buying for sebacic acid", "NCDEX speculative positioning", "Substitution in lubricant formulations"],
   [["India share of world output", "~85%", "2025"], ["Hedge quality", "domestic contract with minimal basis", "structural"]],
   "Solvent Extractors Association, NCDEX, Ministry of Agriculture")

ag("lumber", "Lumber & Timber", "Lbr", "B",
   "Construction and furniture wood, imported as logs from Southeast Asia and Africa.",
   "CME (random length lumber, US only)", "CME lumber; Indian log import assessments", "USD per thousand board feet",
   1, "No Indian contract",
   "CME lumber prices North American softwood and is irrelevant to Indian hardwood log imports. EUDR applies to wood for EU-bound furniture and plywood exports, which is the live compliance item.",
   40, "Greenply, Century Plyboards and the furniture and plywood chain.",
   [["United States", 15], ["Canada", 10], ["Russia", 8], ["Rest of world", 67]],
   [["Construction", 45], ["Furniture", 30], ["Plywood and panels", 25]],
   [["China", 25], ["India", 6], ["Rest of world", 69]],
   ["Southeast Asian and African log export policy", "EUDR traceability", "Indian construction and furniture demand", "Freight"],
   [["EUDR", "wood is an in-scope commodity", "policy"]], "FAO, ITTO")

# ===========================================================================
# FERTILIZER
# ===========================================================================

def fert(id, n, sym, tier, hook, venue, bench, hedge, basis, dep, note, prod, use, imp, drv, stats, src):
    c(id=id, n=n, sym=sym, fam="fert", tier=tier, hook=hook,
      trade=dict(venue=venue, bench=bench, lot="Cargo", terms="USD per tonne",
                 settle="Physical against index; some CME swaps", curve="Seasonal on northern and Indian sowing windows",
                 liq="Thin - CME urea and UAN swaps exist but most volume is physical tender"),
      ind=dict(hedge=hedge, contract="No Indian contract", basis=basis, dep=dep, note=note),
      prod=prod, use=use, imp=imp, drv=drv, stats=stats, src=src)


fert("urea", "Urea", "Urea", "A",
     "The world's most-used fertiliser, made from natural gas, and in India sold at a price the government fixes.",
     "CME (urea swaps, thin) · tender market", "Argus and Profercy assessments - Middle East granular FOB, Brazil CFR, NOLA",
     1, "India's urea economics are almost entirely administered: the farmgate price is fixed by statute, and the gap between production cost and that price is covered by subsidy. So a domestic producer's exposure is not the urea price but the subsidy payment cycle - how quickly the Department of Fertilizers releases funds, which drives working capital and short-term borrowing. For the importing arm (IPL, RCF as canalising agents) the tender price does matter, and CME urea swaps are thin but usable. Splitting a fertiliser client's book into administered and market legs is the essential first step; treating it as one commodity exposure produces nonsense.",
     20, "Chambal, RCF, NFL, GNFC, Deepak Fertilisers. Natural gas is the feedstock, pooled and priced under a government mechanism, which is a second administered layer.",
     [["China", 25], ["India", 15], ["Russia", 10], ["United States", 8], ["Rest of world", 42]],
     [["Cereal and staple crops", 80], ["Cash crops and other", 15], ["Industrial (urea-formaldehyde, DEF)", 5]],
     [["India", 12], ["Brazil", 12], ["United States", 10], ["Rest of world", 66]],
     ["Chinese export restrictions - the single largest swing factor in recent years", "European gas prices, which set marginal production cost",
      "Indian subsidy budget and tender timing", "Monsoon and sowing area", "Russian and Iranian sanctions on fertiliser trade"],
     [["India urea import dependence", "~20% and falling as new plants commission", "FY26"],
      ["Farmgate price", "statutorily fixed", "policy"], ["Gas per tonne of urea", "~25-28 MMBtu", "structural"]],
     "FAI, Department of Fertilizers, Argus, IFA")

fert("ammonia", "Ammonia", "NH3", "A",
     "The molecule at the head of the entire nitrogen chain, and the one green hydrogen wants to replace.",
     "No liquid exchange", "Tampa CFR and Middle East FOB assessments", 1,
     "Index-linked and tender-priced. Ammonia is where the nitrogen chain's gas exposure becomes visible: roughly 30-35 MMBtu of gas per tonne. Indian producers on pooled gas are partially insulated; merchant importers are not. Green ammonia projects under the National Green Hydrogen Mission introduce a completely different cost structure and a long-dated offtake question that clients are starting to ask about.",
     30, "Coromandel, Deepak Fertilisers, Chambal, GSFC and the complex-fertiliser makers. Also an industrial input for explosives and refrigeration.",
     [["China", 30], ["Russia", 9], ["United States", 9], ["India", 8], ["Rest of world", 44]],
     [["Urea and nitrogen fertiliser", 70], ["Phosphates (DAP)", 10], ["Industrial - explosives, fibres, refrigerant", 20]],
     [["India", 15], ["Rest of world", 85]],
     ["Natural gas prices in the US, Europe and the Gulf", "Chinese and Russian export policy", "Tampa CFR monthly settlement",
      "Green ammonia project timelines", "Phosphate plant demand"],
     [["Gas per tonne of ammonia", "~30-35 MMBtu", "structural"], ["India import dependence", "~30%", "FY26"]],
     "FAI, IFA, Argus")

fert("dap", "Phosphate (DAP)", "DAP", "A",
     "India imports most of its phosphate and buys it from a short list of sellers, mostly under annual negotiation.",
     "No liquid exchange", "DAP CFR India assessment; Morocco and Saudi FOB", 1,
     "No hedge. Indian DAP is imported under negotiated contracts with OCP (Morocco), Ma'aden (Saudi) and Russian suppliers, and sold at a government-controlled maximum retail price with Nutrient Based Subsidy covering the gap. So the exposure is a squeeze between an internationally set landed cost and a domestically set selling price, buffered by a subsidy rate the government revises with a lag. When world DAP prices spike, Indian importers eat the gap until the NBS rate catches up - which has happened repeatedly and is a working-capital event of real size. That lag is quantifiable and is exactly the kind of thing a CFO wants modelled.",
     60, "Coromandel, Chambal, Paradeep Phosphates, GSFC. Chinese export restrictions on phosphates from 2021 onward reshaped this market.",
     [["China", 30], ["Morocco", 15], ["United States", 10], ["Russia", 8], ["Rest of world", 37]],
     [["Fertiliser - phosphate nutrient", 95], ["Industrial and feed", 5]],
     [["India", 25], ["Brazil", 15], ["Rest of world", 60]],
     ["Chinese phosphate export quotas - the dominant variable since 2021", "Ammonia and sulphur input costs",
      "Indian Nutrient Based Subsidy rate revisions and timing", "Monsoon and kharif sowing", "Moroccan and Saudi capacity"],
     [["India DAP import dependence", "~60%", "FY26"], ["Pricing", "MRP controlled, gap covered by NBS", "policy"]],
     "FAI, Department of Fertilizers, IFA, Argus")

fert("potash", "Potash (MOP)", "MOP", "A",
     "India grows none of it and imports 100%, from a producer group that negotiates an annual contract price.",
     "No liquid exchange", "Annual India and China contract settlements; Brazil CFR spot", 1,
     "Unhedgeable and unusually structured: the world price for Indian buyers is effectively set once a year in a negotiation between Indian Potash Limited and Canpotex, BPC or Uralkali. That annual settlement is a single point of exposure with no instrument against it. Belarusian sanctions after 2022 removed a major supplier and reshaped the negotiation. The advisory value is in scenario-modelling settlement outcomes against the subsidy budget and the sowing calendar.",
     100, "Indian Potash Limited is the canalising importer; Coromandel and the complex-fertiliser makers use MOP as an input.",
     [["Canada", 32], ["Russia", 20], ["Belarus", 15], ["China", 10], ["Rest of world", 23]],
     [["Fertiliser - potassium nutrient", 95], ["Industrial", 5]],
     [["Brazil", 20], ["China", 18], ["India", 12], ["United States", 12], ["Rest of world", 38]],
     ["Annual India and China contract settlements", "Belarusian and Russian sanctions and rail routing",
      "Canpotex production discipline", "Indian subsidy budget", "Brazilian soybean demand"],
     [["India import dependence", "100%", "structural"], ["Price mechanism", "annual negotiated contract", "structural"]],
     "FAI, IFA, Department of Fertilizers")

fert("sulphur", "Sulphur & Sulphuric Acid", "S", "B",
     "A refinery and gas-processing by-product whose supply does not respond to its own price.",
     "No liquid exchange", "Middle East FOB and CFR India assessments", 1,
     "No hedge. Because sulphur is an involuntary by-product of oil refining and sour gas processing, supply is set by refinery runs, not by sulphur demand - so the price is unusually spiky when phosphate demand rises. Indian phosphate producers carry it as an unhedgeable input.",
     90, "Coromandel, Paradeep Phosphates, GSFC and the sulphuric acid chain.",
     [["China", 18], ["United States", 12], ["Russia", 11], ["Canada", 8], ["Rest of world", 51]],
     [["Phosphate fertiliser", 60], ["Metal leaching and industrial", 25], ["Other chemicals", 15]],
     [["Morocco", 20], ["India", 12], ["Rest of world", 68]],
     ["Refinery and sour gas processing runs", "Phosphate fertiliser demand", "Middle East export availability", "Freight"],
     [["India import dependence", "~90%", "FY26"], ["Supply elasticity", "near zero - involuntary by-product", "structural"]],
     "FAI, IFA, Argus")

# ===========================================================================
# FREIGHT & SHIPPING
# ===========================================================================

def frt(id, n, sym, tier, hook, bench, hedge, basis, note, drv, stats, src, use, prod=None, imp=None):
    c(id=id, n=n, sym=sym, fam="freight", tier=tier, hook=hook,
      trade=dict(venue="Baltic Exchange (index) · EEX and SGX (FFA clearing)", bench=bench,
                 lot="Days or tonnes, by route", terms="USD per day (time charter) or Worldscale points",
                 settle="Forward Freight Agreements cash-settle against the Baltic index average",
                 curve="Highly seasonal and violently mean-reverting", liq="FFAs are liquid on the main dry bulk and tanker routes"),
      ind=dict(hedge=hedge, contract="No Indian contract", basis=basis, dep=0, note=note),
      prod=prod or [["Global shipping capacity", 100]], use=use, imp=imp or [["Global", 100]],
      drv=drv, stats=stats, src=src)


frt("drybulk", "Dry Bulk Freight", "BDI", "A",
    "The cost of moving coal, iron ore and grain - and a line item Indian importers almost never hedge.",
    "Baltic Dry Index; Capesize 5TC, Panamax 4TC and Supramax 10TC time-charter averages",
    3, "Forward Freight Agreements on the Baltic routes are genuinely liquid and cash-settle in USD against a published index. For an Indian coal or fertiliser importer moving several million tonnes a year, freight can be 15-30% of landed cost and it is more volatile than the commodity itself - Capesize rates routinely move by a factor of three within a year. Almost no Indian importer hedges it. This is one of the clearest unexploited hedging opportunities in the Indian corporate book, and the instrument already exists.",
    "Adani Power, Tata Power, JSW Energy, the cement makers, the fertiliser importers and the steel mills all carry it inside landed cost. Great Eastern Shipping and SCI are on the other side.",
    ["Chinese iron ore and coal import volumes", "Grain trade flows and South American harvest timing",
     "Newbuild orderbook and scrapping rates", "Panama Canal draft restrictions and Red Sea routing",
     "Port congestion", "Bunker fuel price and IMO emissions rules"],
    [["Share of landed coal cost", "~15-30%", "indicative"], ["Rate volatility", "Capesize rates can move 3x within a year", "structural"],
     ["FFA liquidity", "liquid on main routes", "structural"]],
    "Baltic Exchange, Clarksons, company annual reports",
    [["Iron ore", 30], ["Coal", 25], ["Grain", 15], ["Bauxite, fertiliser and minor bulks", 30]])

frt("crudetanker", "Crude Tankers", "BDTI", "B",
    "The floating pipeline - and since 2022 a market reshaped by sanctions and a shadow fleet.",
    "Baltic Dirty Tanker Index; VLCC TD3C Middle East to China route",
    3, "FFAs available. Indian refiners buying on a delivered basis carry freight inside the crude price; those buying FOB carry it explicitly and could hedge it. Russian-origin cargoes carry an additional insurance and shadow-fleet premium that no index captures cleanly.",
    "Reliance, IOC, BPCL, HPCL. Great Eastern Shipping is long the rate.",
    ["OPEC+ output, which sets tonne-mile demand", "Russian crude rerouting and sanctions on vessels",
     "Red Sea and Hormuz security", "Newbuild deliveries and an ageing fleet", "Floating storage economics in contango"],
    [["Route benchmark", "TD3C Middle East Gulf to China", "structural"]],
    "Baltic Exchange, Clarksons", [["Crude oil transport", 100]])

frt("container", "Container Freight", "Box", "A",
    "The exporter's cost line, and the one that quadrupled twice this decade on events nobody modelled.",
    "Shanghai Containerized Freight Index (SCFI); Drewry World Container Index; Freightos FBX",
    2, "Container FFAs exist (SCFI-linked on SGX) but are far thinner than dry bulk. Most exporters manage this through contract-rate negotiation with carriers rather than derivatives, and the 2021 and 2024 episodes showed that contracted rates get repudiated when spot spikes. The practical mitigation is a mix of contract and spot allocation plus an explicit freight-escalation clause with the end customer - and checking whether a client's export contracts actually have one is a five-minute review that has saved real money.",
    "Every Indian exporter: textiles, pharma, chemicals, engineering goods, shrimp. Red Sea diversion added roughly two weeks and a large surcharge to Europe-bound routes.",
    ["Red Sea security and Cape of Good Hope routing", "Carrier alliance capacity discipline", "Newbuild deliveries",
     "US and EU import demand cycles", "Port congestion and labour action", "Front-loading ahead of tariff deadlines"],
    [["Rate move 2021", "roughly 5x on Asia-Europe", "2021"], ["Red Sea diversion", "~10-14 extra days to Europe", "2024-26"]],
    "Drewry, Freightos, Baltic Exchange, FIEO", [["Manufactured goods export", 100]])

frt("bunker", "Marine Fuel", "FO", "B",
    "Very low sulphur fuel oil - the shipping industry's cost base and now an emissions-regulated one.",
    "Platts Singapore VLSFO 0.5%; Rotterdam and Fujairah assessments",
    3, "Bunker swaps are liquid in Singapore, USD-denominated, offshore. Shipping companies hedge them; charterers with fuel-inclusive contracts often should and do not. The FuelEU Maritime and EU ETS extension to shipping add a compliance cost on top of the fuel price for EU-touching voyages.",
    "Great Eastern Shipping, SCI, and any Indian exporter on a fuel-inclusive freight contract.",
    ["Crude price and refinery fuel oil yields", "IMO sulphur and carbon regulation", "Scrubber economics and the high-low sulphur spread",
     "EU ETS extension to maritime and FuelEU Maritime", "Bunkering hub competition"],
    [["EU ETS maritime", "phased in from 2024", "policy"]],
    "Platts, IMO, company annual reports", [["Ship propulsion", 100]])

# ===========================================================================
# ENVIRONMENTAL MARKETS
# ===========================================================================

c(
    id="eua", n="EU Carbon Allowance", sym="EUA", fam="env", tier="A",
    hook="The price Indian steel and aluminium exporters started paying for their emissions on 1 January 2026.",
    trade=dict(
        venue="ICE Endex (dominant) · EEX (primary auctions)",
        bench="ICE EUA December future",
        lot="1,000 allowances (1,000 t CO2e)",
        terms="EUR per tonne CO2e",
        settle="Physical delivery of allowances into a Union Registry account",
        curve="Contango reflecting the cost of carry; the December contract is the liquidity point",
        liq="Deep and genuinely liquid - the largest carbon market in the world"),
    ind=dict(
        hedge=3,
        contract="No Indian contract. ICE Endex, EUR-denominated.",
        basis="This is a new and genuinely hedgeable exposure that Indian exporters acquired by regulation rather than by choice. Under the CBAM definitive regime, an Indian steel or aluminium exporter to the EU must surrender certificates priced off the EU ETS, so the company now has a EUR-denominated carbon cost with a liquid futures market against it. Two subtleties matter: CBAM certificates for 2027 purchase are priced off the 2026 quarterly-average ETS price, not spot, so the correct hedge is an average-price structure rather than a simple future; and the exposure is EUR, so the currency leg goes into EUR rather than the usual USD - a different conversation with the bank and a different RBI permission profile. The Omnibus package cut the quarterly certificate-holding requirement from 80% to 50%, which relieves working capital but does not change the price exposure.",
        dep=0,
        note="Tata Steel, JSW Steel, Hindalco, JSPL and any Indian exporter of in-scope goods (iron and steel, aluminium, cement, fertiliser, hydrogen, electricity). First surrender is due 30 September 2027 for 2026 emissions."),
    prod=[["EU ETS cap - administratively set", 100]],
    use=[["Power sector compliance", 40], ["Industry compliance", 35], ["Aviation and maritime", 10], ["Financial participants", 15]],
    imp=[["European Union", 100]],
    drv=["The EU ETS cap trajectory and the Market Stability Reserve", "European gas prices, which drive coal-to-gas switching in power",
         "Industrial output in Europe", "Free allocation phase-out schedule, which is what makes CBAM bite",
         "ETS2 launch for buildings and transport", "Speculative and compliance-buyer positioning"],
    stats=[["CBAM definitive regime start", "1 January 2026", "policy"], ["Certificate sales begin", "1 February 2027", "policy"],
           ["First surrender deadline", "30 September 2027", "policy"], ["Quarterly holding requirement", "cut from 80% to 50% under Omnibus", "policy"],
           ["2027 certificate pricing basis", "2026 quarterly-average ETS price", "policy"]],
    src="European Commission DG TAXUD, ICE Endex contract specification, EU Omnibus package",
)

c(
    id="ccts", n="India CCTS Carbon Credits", sym="CCC", fam="env", tier="A",
    hook="India's own compliance carbon market, live from 2026 - the domestic mirror of the exposure CBAM created.",
    trade=dict(
        venue="Power exchanges (IEX, PXIL) under the Bureau of Energy Efficiency framework",
        bench="Carbon Credit Certificate (CCC) traded price",
        lot="1 CCC = 1 t CO2e",
        terms="INR per tonne CO2e",
        settle="Registry transfer against the compliance obligation",
        curve="No forward curve yet - the market is new",
        liq="Nascent. Obligated entities in nine sectors began compliance-cycle trading in 2026"),
    ind=dict(
        hedge=1,
        contract="Traded on Indian power exchanges under the CCTS compliance mechanism",
        basis="This is the exposure most Indian industrial clients do not yet have on their risk register. The Carbon Credit Trading Scheme sets greenhouse gas intensity targets for obligated entities in aluminium, cement, pulp and paper, chlor-alkali, iron and steel, textiles, petrochemicals, petroleum refineries and fertiliser. Miss the target and you buy certificates; beat it and you sell them. It is an emerging INR-denominated commodity position sitting inside a manufacturing P&L, and the market is too new for a reliable price history - which means no VaR, no hedge, and a genuine need for scenario work instead. For a client already modelling CBAM, the natural question is whether an Indian carbon price paid domestically can be credited against the EU certificate obligation, which is a live policy question worth tracking.",
        dep=0,
        note="Obligated sectors overlap almost exactly with the CBAM in-scope list, which is not a coincidence. Compliance targets and the trading cycle are set by the Bureau of Energy Efficiency."),
    prod=[["Indian obligated entities - administratively allocated", 100]],
    use=[["Compliance surrender by obligated entities", 100]],
    imp=[["India", 100]],
    drv=["BEE target-setting stringency by sector", "Industrial output and energy intensity improvements",
         "Interaction with the earlier PAT ESCert regime", "Whether the offset mechanism opens to voluntary buyers", "Any CBAM recognition of domestic carbon price paid"],
    stats=[["Compliance mechanism start", "2026 compliance cycle", "policy"], ["Obligated sectors", "nine, overlapping the CBAM list", "policy"],
           ["Price history", "insufficient for statistical modelling", "2026"]],
    src="Bureau of Energy Efficiency, Ministry of Power CCTS notifications, Energy Conservation (Amendment) Act",
)

c(
    id="rec", n="Renewable Energy Certificates", sym="REC", fam="env", tier="B",
    hook="India's tradeable proof of green power, used to meet Renewable Purchase Obligations.",
    trade=dict(venue="IEX and PXIL", bench="REC trading session clearing price", lot="1 REC = 1 MWh",
               terms="INR per REC", settle="Registry transfer", curve="None - monthly trading sessions",
               liq="Modest; prices have been floor-and-ceiling bound by CERC"),
    ind=dict(hedge=1, contract="Traded on Indian power exchanges",
             basis="A domestic INR instrument with a real compliance driver: obligated entities must meet a Renewable Purchase Obligation and can do so with RECs instead of physical renewable power. The price has historically been bracketed by CERC-set floors and ceilings, which truncates the distribution. For a corporate with an RE100 or internal renewable commitment, the question is whether RECs count toward it - often they do not for scope 2 market-based reporting standards, which is a mismatch worth flagging before a client buys them expecting credit.",
             dep=0, note="Relevant to any obligated entity and to corporates with renewable procurement targets."),
    prod=[["Indian renewable generators", 100]],
    use=[["RPO compliance", 80], ["Voluntary corporate procurement", 20]],
    imp=[["India", 100]],
    drv=["RPO trajectory set by state regulators", "Renewable capacity additions", "CERC price floor and ceiling decisions", "Corporate voluntary demand"],
    stats=[["Unit", "1 REC = 1 MWh", "structural"]], src="CERC, IEX, MNRE",
)

c(
    id="vcm", n="Voluntary Carbon Credits", sym="VCM", fam="env", tier="B",
    hook="A market with a credibility problem, and India is one of its largest suppliers.",
    trade=dict(venue="OTC bilateral · CME (GEO futures, thin) · registries (Verra, Gold Standard)",
               bench="No single benchmark; project-type-specific pricing", lot="1 credit = 1 t CO2e",
               terms="USD per tonne CO2e", settle="Registry retirement", curve="None",
               liq="Illiquid and fragmented by project type and vintage"),
    ind=dict(hedge=0, contract="None",
             basis="Not a hedgeable market and not really a commodity - a credit's price depends on project type, vintage, co-benefits and registry, so no two are fungible. Integrity concerns about avoided-deforestation credits collapsed prices and demand from 2023. For Indian corporates the relevant use is voluntary net-zero claims, and the risk is reputational: buying credits that are later discredited is worse than buying none. Article 6 of the Paris Agreement and the corresponding-adjustment question also determine whether Indian-origin credits can be exported at all.",
             dep=0, note="India is a large supplier of renewable and cookstove credits. Watch the interaction with CCTS, which may absorb domestic supply."),
    prod=[["India", 15], ["China", 12], ["Brazil", 10], ["Rest of world", 63]],
    use=[["Corporate voluntary retirement", 90], ["CORSIA aviation compliance", 10]],
    imp=[["Rest of world", 100]],
    drv=["Corporate net-zero commitment credibility standards (SBTi, VCMI)", "Registry methodology revisions",
         "Article 6 corresponding adjustments and host-country authorisation", "CORSIA eligible-credit decisions", "Media and NGO scrutiny of project integrity"],
    stats=[["Market state", "post-2023 credibility contraction", "2026"]], src="Verra, Gold Standard, Ecosystem Marketplace, ICAO CORSIA",
)

# ===========================================================================
# SCORING LAYER
#
# vol  : price volatility rating 1-5. A judgement rating, used only where the
#        daily pipeline has no real price series. Where data/latest.json carries
#        a series, index.html overrides this with EWMA(0.94) realised vol.
# conc : supply concentration 1-5. COMPUTED from the producer shares above via
#        a Herfindahl index, not hand-set. 'Rest of world' is treated as fully
#        fragmented and contributes nothing. Override only where the producer
#        list is a placeholder (refined globally, administered supply) or where
#        India's sourcing is materially more concentrated than world supply -
#        each override carries a reason.
# inp  : upstream inputs - the processing dependency graph.
# ===========================================================================

# id: (vol_rating, [upstream inputs])
VOL_INP = {
    # precious
    "gold": (3, []), "silver": (4, []), "pallad": (5, []), "platinum": (4, []), "diamonds": (3, []),
    # base
    "copper": (4, []), "alum": (4, ["alumina", "elec"]), "alumina": (4, ["bauxite", "caustic"]),
    "bauxite": (2, []), "zinc": (4, []), "lead": (3, []), "nickel": (5, []), "tin": (4, []),
    "ironore": (4, []), "steel": (3, ["ironore", "metcoal", "elec", "scrap"]), "hrc": (4, ["steel"]),
    "scrap": (3, []), "ferroalloy": (3, ["elec"]), "limestone": (1, []),
    "cement": (2, ["limestone", "petcoke", "coal", "elec"]), "tio2": (3, []),
    # critical
    "lithium": (5, []), "cobalt": (4, []), "graphite": (3, []), "ree": (4, []), "antimony": (5, []),
    "uranium": (3, []), "chips": (3, ["poly", "copper", "pallad"]), "poly": (4, ["elec"]), "fluorspar": (3, []),
    # oil
    "crude": (4, []), "dubai": (4, []), "diesel": (4, ["crude"]), "jet": (4, ["crude"]),
    "lpg": (4, ["crude", "natgas"]), "naphtha": (4, ["crude"]), "petcoke": (4, ["crude"]),
    "bitumen": (3, ["crude"]), "gasoline": (4, ["crude"]),
    # gas
    "lng": (5, ["natgas"]), "natgas": (5, []), "apmgas": (1, []), "coal": (4, []), "metcoal": (5, []),
    "elec": (3, ["coal", "natgas"]), "ttf": (5, []),
    # petchem
    "plastics": (3, ["ethylene", "propylene"]), "ethylene": (3, ["naphtha", "natgas"]),
    "propylene": (3, ["naphtha", "lpg"]), "benzene": (4, ["naphtha"]), "methanol": (4, ["natgas", "coal"]),
    "pta": (3, ["benzene"]), "meg": (3, ["ethylene"]), "pvc": (3, ["ethylene", "caustic"]),
    "styrene": (4, ["benzene", "ethylene"]), "vam": (4, ["ethylene"]), "carbonblack": (3, ["crude"]),
    "caustic": (3, ["elec"]), "sodaash": (3, ["limestone", "elec"]), "sbr": (3, ["crude", "naphtha"]),
    "phenol": (3, ["benzene", "propylene"]), "api": (3, ["benzene", "methanol"]),
    # ag
    "palm": (4, []), "cotton": (4, []), "sugar": (4, []), "wheat": (4, []), "rice": (3, []),
    "maize": (3, []), "soyoil": (4, []), "sunoil": (5, []), "mustard": (3, []), "copra": (4, []),
    "natrub": (4, []), "cocoa": (5, []), "coffee": (5, []), "tea": (3, []), "milk": (3, []),
    "ethanol": (2, ["sugar", "maize"]), "pulp": (3, []), "tobacco": (2, []), "spices": (4, []),
    "shrimp": (3, []), "castor": (4, []), "lumber": (3, []),
    # fert
    "urea": (4, ["natgas", "ammonia"]), "ammonia": (5, ["natgas"]), "dap": (4, ["ammonia", "sulphur"]),
    "potash": (3, []), "sulphur": (5, ["crude"]),
    # freight
    "drybulk": (5, ["bunker"]), "crudetanker": (5, ["bunker"]), "container": (5, ["bunker"]),
    "bunker": (4, ["crude"]),
    # env
    "eua": (4, []), "ccts": (3, []), "rec": (2, []), "vcm": (3, []),
}

# id: (conc_rating, reason) - only where the computed HHI is not usable or not representative
CONC_OVERRIDE = {
    "diesel": (3, "Refined domestically; concentration inherited from crude sourcing, not from refining"),
    "jet": (3, "Refined domestically; the concentration that matters is the crude basket behind it"),
    "gasoline": (3, "Refined domestically"),
    "naphtha": (3, "Refined domestically"),
    "bitumen": (3, "Refined domestically plus concentrated import routes"),
    "lpg": (3, "Middle East contract-price concentration rather than named-producer concentration"),
    "elec": (2, "Domestic grid; the concentration risk sits in the coal supply behind it"),
    "apmgas": (2, "Single administered domestic source, but no import-disruption channel"),
    "cement": (1, "Domestic, regional, no import exposure"),
    "limestone": (1, "Captive domestic mines"),
    "milk": (1, "Domestic and highly fragmented across cooperatives"),
    "tea": (2, "Domestic auction supply, fragmented across gardens"),
    "tobacco": (1, "Domestic, Tobacco Board auction platform"),
    "rice": (2, "Domestic surplus; the risk is export policy, not supply concentration"),
    "wheat": (2, "Domestic; closed to trade, so world concentration does not transmit"),
    "mustard": (2, "Domestic crop"),
    "maize": (2, "Domestic crop with growing ethanol draw"),
    "steel": (3, "India is the second-largest producer; concentration is in the coking coal behind it"),
    "hrc": (3, "Inherits steel"),
    "scrap": (3, "Fragmented collection but concentrated seaborne export routes"),
    "ethanol": (1, "Domestic administered procurement"),
    "metcoal": (5, "World seaborne HHI understates India's position: Australia is ~85% of Indian imports, not 52%"),
    "coal": (3, "India produces ~75% domestically; the imported quarter is Indonesia-concentrated"),
    "ironore": (2, "India is ore-sufficient; world seaborne concentration does not transmit to Indian mills"),
    "bauxite": (3, "India is bauxite-sufficient; Guinea concentration reaches India through alumina"),
    "gold": (2, "Mine supply is fragmented; India's exposure is price and duty, not supply availability"),
    "silver": (3, "By-product supply is fragmented across many mines"),
    "spices": (2, "India is the dominant producer - a price-setter, not a price-taker"),
    "castor": (2, "India grows ~85%; domestic supply, so world concentration is not a risk to India"),
    "shrimp": (2, "Domestic aquaculture; the risk is destination tariffs"),
    "sugar": (2, "Domestic production; the risk is policy"),
    "drybulk": (4, "Fragmented fleet ownership but concentrated route and canal chokepoints"),
    "crudetanker": (4, "Route and chokepoint concentration"),
    "container": (5, "Three carrier alliances control the large majority of capacity"),
    "bunker": (3, "Bunkering hub concentration"),
    "eua": (3, "Administratively capped supply - not a physical concentration risk"),
    "ccts": (2, "Administratively allocated domestic supply"),
    "rec": (2, "Domestic renewable generators, fragmented"),
    "vcm": (3, "Fragmented projects, concentrated registry gatekeeping"),
    "uranium": (4, "Kazakh concentration plus enrichment concentration, which the mine shares do not capture"),
    "api": (5, "World production shares understate it: China is 70%+ of India's imports for many molecules"),
    "chips": (4, "Mine-style shares do not apply; Taiwan is ~90% of leading-edge fabrication"),
    "lng": (3, "Diversifying supply base - US, Qatar, Australia - but chokepoint-exposed"),
    "natgas": (4, "US-benchmark price; the concentration for India is the LNG supply behind it"),
    "ttf": (4, "Norwegian pipeline plus US LNG concentration"),
    "plastics": (2, "Largely domestic supply from Reliance, IOC and GAIL"),
    "copper": (3, "Mine supply is only moderately concentrated, but China refines ~44% of world copper - the chokepoint is smelting, not mining, and mine HHI misses it"),
    "lithium": (5, "Mine shares understate the real chokepoint: China refines 65-70% of world lithium chemicals"),
    "tin": (4, "Mine HHI understates it - Myanmar's Wa State suspension and Indonesian export licensing can remove a fifth of supply by decree"),
}

PLACEHOLDER = ("refined globally", "global shipping capacity", "n/a", "india (ongc, oil)",
               "eu ets cap - administratively set", "indian obligated entities - administratively allocated",
               "indian renewable generators")


def hhi_band(prod):
    """Herfindahl over named producers; 'Rest of world' treated as fully fragmented."""
    named = [s for name, s in prod if "rest of world" not in name.lower()
             and name.lower() not in PLACEHOLDER and "generation mix" not in name.lower()]
    if not named:
        return None
    h = sum((s / 100.0) ** 2 for s in named)
    if h >= 0.40:
        return 5
    if h >= 0.25:
        return 4
    if h >= 0.15:
        return 3
    if h >= 0.08:
        return 2
    return 1


def score_all():
    for x in C:
        i = x["id"]
        vol, inp = VOL_INP.get(i, (3, []))
        x["vol"] = vol
        x["inp"] = inp
        computed = hhi_band(x["prod"])
        if i in CONC_OVERRIDE:
            x["conc"], x["concWhy"] = CONC_OVERRIDE[i][0], CONC_OVERRIDE[i][1]
            x["concCalc"] = computed
        else:
            x["conc"] = computed if computed is not None else 3
            x["concWhy"] = "Computed from the producer shares above (Herfindahl band)"
            x["concCalc"] = computed
        # one-line supply origin, used as the map tooltip
        top = [f"{n} {s}%" for n, s in x["prod"][:3]
               if "rest of world" not in n.lower() and n.lower() not in PLACEHOLDER]
        x["origin"] = " · ".join(top) if top else x["trade"]["venue"]
        if x["ind"]["dep"]:
            x["origin"] += f" · India imports {x['ind']['dep']}%"


def emit_js():
    """DATA.commodities literal for index.html: [name, vol, conc, importDep, inputs, origin]."""
    order = sorted(C, key=lambda x: (list(FAMILIES).index(x["fam"]), x["n"]))
    lines = []
    for x in order:
        inp = "[" + ",".join(f'"{i}"' for i in x["inp"]) + "]"
        origin = x["origin"].replace('"', "'")
        lines.append(f'    "{x["id"]}":["{x["n"]}",{x["vol"]},{x["conc"]},{x["ind"]["dep"]},{inp},"{origin}"]')
    js = "  commodities: {\n" + ",\n".join(lines) + "\n  },"
    path = os.path.join(ROOT, "data", "_commodities_block.js")
    with open(path, "w", encoding="utf-8") as f:
        f.write(js)
    return path


if __name__ == "__main__":
    score_all()
    payload = {
        "_meta": {
            "note": "Commodity reference sheet. Structure adapted from the Commodities 101 fact-sheet breakdown, with an India hedgeability layer added. Shares are indicative and dated - verify against the cited source before client-facing use. These are reference facts and are deliberately separate from the scoring array in index.html (DATA.commodities), which is what the risk models consume.",
            "asof": "2026-07-30",
            "hedgeScale": HEDGE_SCALE,
            "count": len(C),
        },
        "families": FAMILIES,
        "commodities": {x["id"]: x for x in C},
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print(f"wrote {OUT}  ({len(C)} commodities)")
    # integrity: every declared input must resolve to a known commodity
    ids = {x["id"] for x in C}
    for x in C:
        for i in x["inp"]:
            if i not in ids:
                raise SystemExit(f"ERROR {x['id']}: unknown input '{i}'")
    print("wrote", emit_js())
