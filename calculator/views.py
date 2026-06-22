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


def get_sidebar_groups(user):
    """侧栏分组：每个标签一组（含空标签），未分类记录单独成组排在最后。"""
    if not user.is_authenticated:
        return []

    by_tag_id = {}
    untagged = []
    for item in DcfCalculation.objects.filter(user=user).prefetch_related('tags'):
        item_tags = list(item.tags.all())
        if not item_tags:
            untagged.append(item)
        for tag in item_tags:
            by_tag_id.setdefault(tag.id, []).append(item)

    groups = [
        {'tag': tag, 'name': tag.name, 'items': by_tag_id.get(tag.id, [])}
        for tag in DcfTag.objects.filter(user=user)
    ]
    if untagged:
        groups.append({'tag': None, 'name': '未分类', 'items': untagged})
    return groups


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
            calculation_data = {
                field: form.cleaned_data[field]
                for field in form.Meta.fields if field != 'tags'
            }
            calculation = DcfCalculation.objects.create(
                user=request.user,
                enterprise_value=result['enterprise_value'],
                equity_value=result['equity_value'],
                value_per_share=result['value_per_share'],
                **calculation_data,
            )
            calculation.tags.set(form.cleaned_data['tags'])
            messages.success(request, f'已保存「{form.cleaned_data["company_name"]}」到收藏。')
            return redirect('calculator')
    else:
        form = DcfCalculationForm(user=request.user, initial=DEFAULT_INITIAL)

    groups = get_sidebar_groups(request.user)
    has_tags = request.user.is_authenticated and any(g['tag'] for g in groups)
    return render(request, 'calculator/calculator.html', {
        'form': form,
        'tag_form': tag_form,
        'groups': groups,
        'has_tags': has_tags,
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
            count = tag.calculations.count()
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
