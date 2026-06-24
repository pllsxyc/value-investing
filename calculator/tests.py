from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import DcfCalculation, DcfTag
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


class SaveFavoriteTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u', password='p')
        self.client.force_login(self.user)
        self.tag = DcfTag.objects.create(user=self.user, name='水电')

    def _payload(self, **overrides):
        data = {
            'action': 'calculate',
            'company_name': '长江电力', 'ticker': '600900',
            'current_fcf': '100', 'growth_rate': '10', 'discount_rate': '10',
            'terminal_growth_rate': '3', 'forecast_years': '5',
            'net_debt': '0', 'non_operating_assets': '0', 'shares_outstanding': '100',
            'tags': [self.tag.pk],
        }
        data.update(overrides)
        return data

    def test_resave_same_ticker_updates_not_duplicates(self):
        self.client.post(reverse('calculator'), self._payload())
        self.client.post(reverse('calculator'), self._payload(current_fcf='200'))

        qs = DcfCalculation.objects.filter(user=self.user, ticker='600900')
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().current_fcf, Decimal('200'))

    def test_different_ticker_creates_new(self):
        self.client.post(reverse('calculator'), self._payload())
        self.client.post(reverse('calculator'), self._payload(company_name='贵州茅台', ticker='600519'))
        self.assertEqual(DcfCalculation.objects.filter(user=self.user).count(), 2)

    def test_no_ticker_dedupes_by_company_name(self):
        self.client.post(reverse('calculator'), self._payload(ticker='', company_name='某公司'))
        self.client.post(reverse('calculator'), self._payload(ticker='', company_name='某公司', current_fcf='300'))
        qs = DcfCalculation.objects.filter(user=self.user, company_name='某公司')
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().current_fcf, Decimal('300'))
