from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import DcfCalculation, DcfTag


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class TagCreateForm(forms.ModelForm):
    class Meta:
        model = DcfTag
        fields = ['name']
        labels = {'name': '新标签'}
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': '例如：消费板块、有色、科技'}),
        }

    def clean_name(self):
        return self.cleaned_data['name'].strip()


class DcfCalculationForm(forms.ModelForm):
    tag = forms.ChoiceField(label='分类标签', help_text='选择一个已创建的标签，收藏会按该标签归类显示在左侧。')

    class Meta:
        model = DcfCalculation
        fields = [
            'tag',
            'company_name',
            'ticker',
            'current_fcf',
            'growth_rate',
            'discount_rate',
            'terminal_growth_rate',
            'forecast_years',
            'net_debt',
            'non_operating_assets',
            'shares_outstanding',
        ]
        labels = {
            'company_name': '公司名称',
            'ticker': '股票代码',
            'current_fcf': '当前自由现金流',
            'growth_rate': '显式期年增长率',
            'discount_rate': '折现率/WACC',
            'terminal_growth_rate': '永续增长率',
            'forecast_years': '预测年数',
            'net_debt': '净有息债务',
            'non_operating_assets': '非经营性资产',
            'shares_outstanding': '总股本',
        }
        help_texts = {
            'company_name': '用于识别并收藏这次估值的公司名称。',
            'ticker': '可选，例如 AAPL、TSLA 或 600519。',
            'current_fcf': '最近一年 FCFF，公司自由现金流，通常为 EBIT×(1-税率)+折旧摊销-资本开支-营运资本增加。',
            'growth_rate': '显式预测期内自由现金流的年复合增长率，例如 10% 填 10。',
            'discount_rate': '未来现金流折现回今天的风险调整回报率；FCFF 通常使用 WACC。',
            'terminal_growth_rate': '公司进入稳态后的长期增长率，通常不应高于长期 GDP 增速加通胀，且必须低于折现率。',
            'forecast_years': '显式预测期长度，通常 5–10 年。',
            'net_debt': '有息债务减现金，计算股权价值时从企业价值中扣除。',
            'non_operating_assets': '不参与主营经营但归属股东的资产，计算股权价值时加回。',
            'shares_outstanding': '总股本，建议使用稀释后股本，用于计算每股价值。',
        }
        widgets = {
            'company_name': forms.TextInput(attrs={'placeholder': '例如：贵州茅台'}),
            'ticker': forms.TextInput(attrs={'placeholder': '可选'}),
            'current_fcf': forms.NumberInput(attrs={'step': '0.01'}),
            'growth_rate': forms.NumberInput(attrs={'step': '0.01'}),
            'discount_rate': forms.NumberInput(attrs={'step': '0.01'}),
            'terminal_growth_rate': forms.NumberInput(attrs={'step': '0.01'}),
            'forecast_years': forms.NumberInput(attrs={'min': '1', 'max': '30'}),
            'net_debt': forms.NumberInput(attrs={'step': '0.01'}),
            'non_operating_assets': forms.NumberInput(attrs={'step': '0.01'}),
            'shares_outstanding': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        tags = DcfTag.objects.filter(user=user) if user and user.is_authenticated else DcfTag.objects.none()
        self.fields['tag'].choices = [(tag.name, tag.name) for tag in tags]
        if not tags.exists():
            self.fields['tag'].choices = []
            self.fields['tag'].required = False
            self.fields['tag'].help_text = '还没有标签，请先在上方创建标签。'

    def clean(self):
        cleaned_data = super().clean()
        discount_rate = cleaned_data.get('discount_rate')
        terminal_growth_rate = cleaned_data.get('terminal_growth_rate')
        forecast_years = cleaned_data.get('forecast_years')
        shares_outstanding = cleaned_data.get('shares_outstanding')
        tag = cleaned_data.get('tag')

        if self.user and self.user.is_authenticated and not tag:
            self.add_error('tag', '请先创建并选择一个标签。')
        if discount_rate is not None and terminal_growth_rate is not None and terminal_growth_rate >= discount_rate:
            self.add_error('terminal_growth_rate', '永续增长率必须低于折现率。')
        if forecast_years is not None and forecast_years < 1:
            self.add_error('forecast_years', '预测年数至少为 1。')
        if shares_outstanding is not None and shares_outstanding <= 0:
            self.add_error('shares_outstanding', '总股本必须大于 0。')
        return cleaned_data
