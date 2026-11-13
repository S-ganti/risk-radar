import importlib.util
import unittest
import time
import tempfile
import json
from unittest.mock import patch
from pathlib import Path
spec=importlib.util.spec_from_file_location('market_quotes',Path(__file__).parents[1]/'scripts/market_quotes.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class QuoteTests(unittest.TestCase):
    def payload(self,**kw):
        return {'chart':{'result':[{'meta':{'symbol':'TITAN.NS','regularMarketPrice':105,'regularMarketTime':int(time.time()),'chartPreviousClose':100,**kw}}]}}
    def test_change_uses_previous_close(self):
        self.assertAlmostEqual(m.parse_quote(self.payload(),'TITAN.NS')['change_pct'],5)
    def test_rejects_symbol_mismatch(self):
        with self.assertRaises(ValueError):m.parse_quote(self.payload(),'OTHER.NS')
    def test_rejects_missing_bad_and_future_values(self):
        for kw in [{'regularMarketPrice':None},{'regularMarketPrice':float('nan')},{'regularMarketTime':None},{'regularMarketTime':time.time()+9999}]:
            with self.assertRaises(ValueError):m.parse_quote(self.payload(**kw),'TITAN.NS')
    def test_catalog_covers_all_companies_and_commodities(self):
        rows=m.catalog();self.assertEqual(87,sum(r['kind']=='stock' for r in rows));self.assertEqual(97,sum(r['kind']=='commodity' for r in rows));self.assertEqual(len(rows),len({r['id'] for r in rows}))
    def test_unmapped_commodities_are_not_given_proxy_prices(self):
        api=next(r for r in m.catalog() if r['id']=='commodity:api');self.assertEqual(api['status'],'unavailable');self.assertNotIn('price',api)
    def test_failed_refresh_preserves_observation_time_and_marks_stale(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'quotes.json'
            prior={'id':'stock:titan','symbol':'TITAN.NS','price':100,'asof':'2026-01-01T00:00:00+00:00','status':'delayed_or_eod'}
            path.write_text(json.dumps({'quotes':[prior]}))
            with patch.object(m,'OUT',path),patch.object(m,'catalog',return_value=[{'id':'stock:titan','entity_id':'titan','symbol':'TITAN.NS'}]):
                r=m.refresh(offline=True)['quotes'][0]
                self.assertEqual(r['asof'],prior['asof']);self.assertEqual(r['price'],100);self.assertEqual(r['status'],'stale')
    def test_new_symbol_does_not_inherit_old_price(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'quotes.json';path.write_text(json.dumps({'quotes':[{'id':'stock:x','symbol':'OLD.NS','price':100,'asof':'2026-01-01'}]}))
            with patch.object(m,'OUT',path),patch.object(m,'catalog',return_value=[{'id':'stock:x','entity_id':'x','symbol':'NEW.NS'}]):
                r=m.refresh(offline=True)['quotes'][0];self.assertNotIn('price',r);self.assertEqual(r['status'],'unavailable')
if __name__=='__main__':unittest.main()
