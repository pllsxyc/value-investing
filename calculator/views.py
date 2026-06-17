from collections import OrderedDict
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render

from .forms import DcfCalculationForm, RegisterForm, TagCreateForm
from .models import DcfCalculation, DcfTag


class AppLoginView(LoginView):
    template_name = 'registration/login.html'


def calculate_dcf(data):
    current_fcf = data['current_fcf']
    growth_rate = data['growth_rate'] / Decimal('100')
    discount_rate = data['discount_rate'] / Decimal('100')
    terminal_growth_rate = data['terminal_growth_rate'] / Decimal('100')
    forecast_years = data['forecast_years']
    net_debt = data['net_debt']
    non_operating_assets = data['non_operating_assets']
    shares_outstanding = data['shares_outstanding']

    cash_flows = []
    present_value_sum = Decimal('0')
    fcf = current_fcf

    for year in range(1, forecast_years + 1):
        fcf *= Decimal('1') + growth_rate
        present_value = fcf / ((Decimal('1') + discount_rate) ** year)
        present_value_sum += present_value
        cash_flows.append({
            'year': year,
            'fcf': fcf,
            'present_value': present_value,
        })

    terminal_value = (fcf * (Decimal('1') + terminal_growth_rate)) / (discount_rate - terminal_growth_rate)
    terminal_present_value = terminal_value / ((Decimal('1') + discount_rate) ** forecast_years)
    enterprise_value = present_value_sum + terminal_present_value
    equity_value = enterprise_value - net_debt + non_operating_assets
    value_per_share = equity_value / shares_outstanding

    return {
        'cash_flows': cash_flows,
        'terminal_value': terminal_value,
        'terminal_present_value': terminal_present_value,
        'enterprise_value': enterprise_value,
        'equity_value': equity_value,
        'value_per_share': value_per_share,
    }


def get_grouped_favorites(user):
    """按标签分组收藏记录，只返回有收藏的分组，并尽量保持标签创建顺序。"""
    if not user.is_authenticated:
        return OrderedDict()

    groups = OrderedDict()
    for item in DcfCalculation.objects.filter(user=user):
        groups.setdefault(item.tag or '未分类', []).append(item)

    tag_order = list(DcfTag.objects.filter(user=user).values_list('name', flat=True))
    ordered = OrderedDict()
    for name in tag_order:
        if name in groups:
            ordered[name] = groups.pop(name)
    # 其余分组（如已删除标签或“未分类”）追加在后面
    for name, items in groups.items():
        ordered[name] = items
    return ordered


DEFAULT_INITIAL = {
    'current_fcf': 100,
    'growth_rate': 10,
    'discount_rate': 10,
    'terminal_growth_rate': 3,
    'forecast_years': 5,
    'net_debt': 0,
    'non_operating_assets': 0,
}


def calculator(request):
    tag_form = TagCreateForm()

    if request.method == 'POST' and request.POST.get('action') == 'create_tag':
        if not request.user.is_authenticated:
            return redirect('login')
        tag_form = TagCreateForm(request.POST)
        if tag_form.is_valid():
            name = tag_form.cleaned_data['name']
            _, created = DcfTag.objects.get_or_create(user=request.user, name=name)
            messages.success(request, '标签已创建。' if created else '标签已存在。')
            return redirect('calculator')
        form = DcfCalculationForm(user=request.user, initial=DEFAULT_INITIAL)
    elif request.method == 'POST':
        # 计算结果实时由前端 JS 展示；提交只用于「保存到收藏」，因此需要登录。
        if not request.user.is_authenticated:
            return redirect('login')
        form = DcfCalculationForm(request.POST, user=request.user)
        if form.is_valid():
            result = calculate_dcf(form.cleaned_data)
            calculation_data = {field: form.cleaned_data[field] for field in form.Meta.fields}
            DcfCalculation.objects.create(
                user=request.user,
                enterprise_value=result['enterprise_value'],
                equity_value=result['equity_value'],
                value_per_share=result['value_per_share'],
                **calculation_data,
            )
            messages.success(request, f'已保存「{form.cleaned_data["company_name"]}」到收藏。')
            return redirect('calculator')
    else:
        form = DcfCalculationForm(user=request.user, initial=DEFAULT_INITIAL)

    grouped_favorites = get_grouped_favorites(request.user)
    if request.user.is_authenticated:
        tags = list(DcfTag.objects.filter(user=request.user))
        for tag in tags:
            tag.favorite_count = len(grouped_favorites.get(tag.name, []))
    else:
        tags = []
    return render(request, 'calculator/calculator.html', {
        'form': form,
        'tag_form': tag_form,
        'tags': tags,
        'grouped_favorites': grouped_favorites,
    })


@login_required
def favorites(request):
    calculations = DcfCalculation.objects.filter(user=request.user)
    return render(request, 'calculator/favorites.html', {'calculations': calculations})


@login_required
def delete_favorite(request, pk):
    if request.method == 'POST':
        deleted, _ = DcfCalculation.objects.filter(user=request.user, pk=pk).delete()
        messages.success(request, '收藏已删除。' if deleted else '收藏不存在。')
    next_url = request.POST.get('next')
    if next_url == 'favorites':
        return redirect('favorites')
    return redirect('calculator')


@login_required
def delete_tag(request, pk):
    if request.method == 'POST':
        tag = DcfTag.objects.filter(user=request.user, pk=pk).first()
        if not tag:
            messages.error(request, '标签不存在。')
        else:
            count = DcfCalculation.objects.filter(user=request.user, tag=tag.name).count()
            if count:
                messages.error(request, f'标签“{tag.name}”下还有 {count} 条收藏，请先删除这些收藏后再删除标签。')
            else:
                tag.delete()
                messages.success(request, '标签已删除。')
    return redirect('calculator')


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('calculator')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})
