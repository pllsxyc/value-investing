from django.conf import settings
from django.db import models


class DcfTag(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dcf_tags')
    name = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['user', 'name'], name='unique_dcf_tag_per_user'),
        ]

    def __str__(self):
        return self.name


class DcfCalculation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dcf_calculations')
    company_name = models.CharField(max_length=120)
    ticker = models.CharField(max_length=32, blank=True)
    tags = models.ManyToManyField(DcfTag, related_name='calculations', blank=True)
    current_fcf = models.DecimalField(max_digits=18, decimal_places=2)
    growth_rate = models.DecimalField(max_digits=7, decimal_places=4)
    discount_rate = models.DecimalField(max_digits=7, decimal_places=4)
    terminal_growth_rate = models.DecimalField(max_digits=7, decimal_places=4)
    forecast_years = models.PositiveSmallIntegerField(default=5)
    net_debt = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    non_operating_assets = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    shares_outstanding = models.DecimalField(max_digits=18, decimal_places=2)
    enterprise_value = models.DecimalField(max_digits=18, decimal_places=2)
    equity_value = models.DecimalField(max_digits=18, decimal_places=2)
    value_per_share = models.DecimalField(max_digits=18, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.company_name
