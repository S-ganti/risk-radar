import unittest
from engine import hedge

class HedgeRegressionTests(unittest.TestCase):
    def test_invalid_prices_cannot_misalign_returns(self):
        a=[100+i for i in range(40)];b=[200+i for i in range(40)];a[5]=0
        self.assertIn('error',hedge.basis_risk(a,b))
    def test_quantitative_success_is_not_accounting_approval(self):
        result=hedge.assess([100,105,102,110],[100,95,98,90])
        self.assertEqual(result['accounting_status'],'not_assessed')
        self.assertEqual(result['verdict_scope'],'historical_quantitative_benchmarks')
