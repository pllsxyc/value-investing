from decimal import Decimal

from django.test import TestCase

from .views import calculate_dcf


class DcfCalculationTests(TestCase):
    def test_calculate_dcf(self):
        result = calculate_dcf({
            'current_fcf': Decimal('100'),
            'growth_rate': Decimal('10'),
            'discount_rate': Decimal('10'),
            'terminal_growth_rate': Decimal('3'),
            'forecast_years': 5,
            'net_debt': Decimal('0'),
            'non_operating_assets': Decimal('0'),
            'shares_outstanding': Decimal('100'),
        })

        self.assertEqual(len(result['cash_flows']), 5)
        self.assertGreater(result['enterprise_value'], Decimal('1900'))
        self.assertLess(result['enterprise_value'], Decimal('2000'))
        self.assertGreater(result['value_per_share'], Decimal('19'))
