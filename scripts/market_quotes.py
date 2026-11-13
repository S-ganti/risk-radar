"""Public quote snapshots. No credentials, fabricated prices or live guarantees.

Run periodically in CI, or use serve.py for on-demand local refresh.
Yahoo availability is best-effort; physical benchmarks without a feed stay unavailable.
"""
import concurrent.futures
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/market-quotes.json'
STOCKS = dict(x.split(':') for x in '''reliance:RELIANCE tcs:TCS hdfcbank:HDFCBANK bhartiairtel:BHARTIARTL icicibank:ICICIBANK sbi:SBIN infosys:INFY hul:HINDUNILVR itc:ITC lic:LICI bajajfinance:BAJFINANCE bajajfinserv:BAJAJFINSV lt:LT hcltech:HCLTECH kotakbank:KOTAKBANK sunpharma:SUNPHARMA maruti:MARUTI mm:M&M ultratech:ULTRACEMCO axisbank:AXISBANK ntpc:NTPC titan:TITAN adaniports:ADANIPORTS wipro:WIPRO tatamotors:TATAMOTORS tatasteel:TATASTEEL jswsteel:JSWSTEEL hindalco:HINDALCO nestleindia:NESTLEIND asianpaints:ASIANPAINT coalindia:COALINDIA powergrid:POWERGRID adanient:ADANIENT ongc:ONGC interglobe:INDIGO iocl:IOC bpcl:BPCL gail:GAIL petronet:PETRONET gujgas:GUJGASLTD igl:IGL tatapower:TATAPOWER adanipower:ADANIPOWER oilindia:OIL vedanta:VEDL hindzinc:HINDZINC nalco:NATIONALUM sail:SAIL jindalsteel:JINDALSTEL apollotyre:APOLLOTYRE mrf:MRF balkrishna:BALKRISIND coromandel:COROMANDEL chambal:CHAMBLFERT srf:SRF tatachem:TATACHEM deepaknitrite:DEEPAKNTR upl:UPL pidilite:PIDILITIND bergerpaints:BERGEPAINT britannia:BRITANNIA marico:MARICO godrejcp:GODREJCP awl:AWL tataconsumer:TATACONSUM varunbev:VBL balrampur:BALRAMCHIN polycab:POLYCAB havells:HAVELLS dixon:DIXON motherson:MOTHERSON bharatforge:BHARATFORG exide:EXIDEIND amararaja:ARE&M bajajauto:BAJAJ-AUTO heromoto:HEROMOTOCO ambuja:AMBUJACEM gesco:GESHIP concor:CONCOR welspunliving:WELSPUNLIV vardhman:VTL jkpaper:JKPAPER waaree:WAAREEENER cipla:CIPLA aurobindo:AUROPHARMA kalyan:KALYANKJIL supremeind:SUPREMEIND'''.split())
# Explicit benchmark units; futures are not physical spot quotes.
FUTURES = {
 'gold':('GC=F','COMEX gold futures','USD/troy oz'),
 'silver':('SI=F','COMEX silver futures','USD/troy oz'),
 'platinum':('PL=F','NYMEX platinum futures','USD/troy oz'),
 'pallad':('PA=F','NYMEX palladium futures','USD/troy oz'),
 'copper':('HG=F','COMEX copper futures','USD/lb'),
 'crude':('BZ=F','ICE Brent futures','USD/barrel'),
 'natgas':('NG=F','NYMEX Henry Hub futures','USD/MMBtu'),
 'gasoline':('RB=F','NYMEX RBOB gasoline futures','USD/gallon'),
 'wheat':('ZW=F','CBOT wheat futures','US cents/bushel'),
 'maize':('ZC=F','CBOT corn futures','US cents/bushel'),
 'soyoil':('ZL=F','CBOT soybean oil futures','US cents/lb'),
 'sugar':('SB=F','ICE sugar no.11 futures','US cents/lb'),
 'coffee':('KC=F','ICE arabica coffee futures','US cents/lb'),
 'cocoa':('CC=F','ICE cocoa futures','USD/tonne'),
 'cotton':('CT=F','ICE cotton futures','US cents/lb'),
 'rice':('ZR=F','CBOT rough rice futures','USD/cwt'),
}
PERIODIC = {'alum':('alum','USD/tonne'),'ironore':('ironore','USD/dry metric tonne'),
 'coal':('coal','USD/tonne'),'palm':('palm','USD/tonne'),'natrub':('natrub','US cents/kg')}

def utc():
    return datetime.now(timezone.utc).isoformat()

def number(v):
    return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)

def parse_quote(payload, symbol):
    result = payload.get('chart',{}).get('result')
    if not result:
        raise ValueError('Provider returned no instrument')
    m = result[0]['meta']
    if m.get('symbol','').upper() != symbol.upper():
        raise ValueError('Provider symbol mismatch')
    price, stamp = m.get('regularMarketPrice'), m.get('regularMarketTime')
    if not number(price) or price <= 0 or not number(stamp) or stamp <= 0:
        raise ValueError('Missing or invalid quote/time')
    if stamp > datetime.now(timezone.utc).timestamp() + 300:
        raise ValueError('Future quote timestamp')
    prev = m.get('chartPreviousClose',m.get('previousClose'))
    data={'price':price,'asof':datetime.fromtimestamp(stamp,timezone.utc).isoformat(),
      'currency':m.get('currency'),'provider_name':m.get('longName',m.get('shortName',symbol)),
      'exchange':m.get('exchangeName'),'symbol':symbol,'source':'Yahoo Finance public chart',
      'source_url':'https://finance.yahoo.com/quote/'+quote(symbol,safe=''),
      'status':'delayed_or_eod','previous_close':prev if number(prev) else None,
      'change_pct':(price/prev-1)*100 if number(prev) and prev>0 else None}
    for field in ['regularMarketVolume','regularMarketDayHigh','regularMarketDayLow','fiftyTwoWeekHigh','fiftyTwoWeekLow','marketCap']:
        if number(m.get(field)): data[field]=m[field]
    return data

def fetch_quote(symbol):
    url='https://query1.finance.yahoo.com/v8/finance/chart/'+quote(symbol,safe='')+'?interval=1d&range=1d'
    req=Request(url,headers={'User-Agent':'Mozilla/5.0 RiskRadar/1.0'})
    with urlopen(req,timeout=12) as r:
        return parse_quote(json.load(r),symbol)

def catalog():
    cs=json.loads((ROOT/'data/company-directory.json').read_text(encoding='utf-8'))
    commodities=json.loads((ROOT/'data/commodities.json').read_text(encoding='utf-8'))['commodities']
    records=[]
    for c in cs:
        records.append({'id':'stock:'+c['id'],'entity_id':c['id'],'name':c['name'],'kind':'stock','unit':'INR/share','symbol':STOCKS[c['id']]+'.NS','benchmark':'NSE equity (check provider legal entity after corporate actions)'})
    for key,c in commodities.items():
        r={'id':'commodity:'+key,'entity_id':key,'name':c['n'],'kind':'commodity','status':'unavailable','reason':'No configured public price feed for this physical market'}
        if key in FUTURES:
            symbol,bench,unit=FUTURES[key];r.update(symbol=symbol,benchmark=bench,unit=unit,quote_type='Futures benchmark; basis differs from physical procurement')
        records.append(r)
    for key,symbol,name in [('usdinr','INR=X','USD / INR'),('eurusd','EURUSD=X','EUR / USD'),('nifty','^NSEI','NIFTY 50')]:
        records.append({'id':'macro:'+key,'entity_id':key,'kind':'macro','name':name,'symbol':symbol,'unit':'INR/USD' if key=='usdinr' else 'USD/EUR' if key=='eurusd' else 'index points','benchmark':name})
    return records

def refresh(fetcher=fetch_quote, offline=False):
    now=utc()
    try: old={r['id']:r for r in json.loads(OUT.read_text(encoding='utf-8'))['quotes']}
    except (OSError,ValueError,KeyError): old={}
    def one(row):
        row=dict(row);row['attempted_at']=now
        if row.get('symbol'):
            try:
                if offline: raise ValueError('Offline snapshot; run refresh to fetch quotes')
                row.update(fetcher(row['symbol']));row['fetched_at']=now;row.pop('reason',None)
            except Exception as exc:
                prior=old.get(row['id'],{})
                if number(prior.get('price')) and prior.get('symbol')==row['symbol']:
                    row={**prior,**row,'price':prior['price'],'asof':prior['asof'],'status':'stale','reason':'Refresh failed; last successful quote retained'}
                else: row.update(status='unavailable',reason='Public provider unavailable: '+str(exc)[:130])
        elif row['entity_id'] in PERIODIC:
            key,unit=PERIODIC[row['entity_id']]
            try:
                series=json.loads((ROOT/f'data/series/{key}.json').read_text());d,v=series[-1]
                row.update(price=v,asof=d,status='monthly_reference',unit=unit,benchmark='IMF monthly benchmark via FRED',source='FRED / IMF',source_url='https://fred.stlouisfed.org/',reason='Monthly reference, not a live price')
            except (OSError,ValueError,IndexError): pass
        return row
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        rows=list(pool.map(one,catalog()))
    data={'schema':1,'generated':now,'mode':'public_snapshot','note':'Public quotes can be delayed. Futures are benchmarks, not physical spot prices. Refresh time is not quote time.','quotes':rows}
    tmp=OUT.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');os.replace(tmp,OUT)
    return data

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--offline',action='store_true');args=p.parse_args()
    d=refresh(offline=args.offline);print(f"{sum(number(r.get('price')) for r in d['quotes'])}/{len(d['quotes'])} priced; all unavailable entries explicitly retained")
