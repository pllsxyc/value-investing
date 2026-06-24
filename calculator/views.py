from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db import DatabaseError, connections
from django.http import JsonResponse
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
            company_name = form.cleaned_data['company_name']
            ticker = (form.cleaned_data.get('ticker') or '').strip()

            # 同一只股票视为同一条收藏：有代码按代码、无代码按公司名匹配（限本人）。
            # 命中则更新（参数 + 重算结果 + 标签），否则新增——避免重复保存产生多条。
            user_calcs = DcfCalculation.objects.filter(user=request.user)
            existing = (user_calcs.filter(ticker=ticker).first() if ticker
                        else user_calcs.filter(company_name=company_name).first())

            computed = {
                'enterprise_value': result['enterprise_value'],
                'equity_value': result['equity_value'],
                'value_per_share': result['value_per_share'],
            }
            if existing is not None:
                for field, value in {**calculation_data, **computed}.items():
                    setattr(existing, field, value)
                existing.save()
                existing.tags.set(form.cleaned_data['tags'])
                messages.success(request, f'已更新收藏「{company_name}」。')
            else:
                calculation = DcfCalculation.objects.create(
                    user=request.user, **calculation_data, **computed,
                )
                calculation.tags.set(form.cleaned_data['tags'])
                messages.success(request, f'已保存「{company_name}」到收藏。')
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


# --- 公司搜索 / 自动填充（只读复用 stock_crawler 的 stock_data 库） ---

def _stock_cursor():
    """返回 stock 只读连接的游标；未配置或连接失败时返回 None（前端降级）。"""
    if 'stock' not in connections.databases:
        return None
    try:
        return connections['stock'].cursor()
    except DatabaseError:
        return None


def _to_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt_num(value, digits=2, suffix=''):
    """把数值格式化成带千分位的展示字符串；None 返回 None（前端跳过该项）。"""
    num = _to_float(value)
    if num is None:
        return None
    return f'{num:,.{digits}f}{suffix}'


def stock_search(request):
    """按公司简称/全称/代码模糊搜索已收录股票，返回候选列表。"""
    query = (request.GET.get('q') or '').strip()
    if not query:
        return JsonResponse({'available': True, 'results': []})

    cursor = _stock_cursor()
    if cursor is None:
        return JsonResponse({'available': False, 'results': []})

    like = f'%{query}%'
    try:
        with cursor:
            cursor.execute(
                """
                SELECT stock_code, stock_name, company_name
                FROM stock_basic
                WHERE stock_name LIKE %s OR company_name LIKE %s OR stock_code LIKE %s
                ORDER BY (stock_code = %s) DESC, (stock_name = %s) DESC, CHAR_LENGTH(stock_name)
                LIMIT 10
                """,
                [like, like, like, query, query],
            )
            rows = cursor.fetchall()
    except DatabaseError:
        return JsonResponse({'available': False, 'results': []})

    results = [
        {'code': code, 'name': name or code, 'company': company or ''}
        for code, name, company in rows
    ]
    return JsonResponse({'available': True, 'results': results})


def stock_autofill(request):
    """按股票代码返回可自动填充的字段（代码、公司名、总股本、经营现金流、净有息债务、非经营性资产）。

    单位：total_share 已是万股，直接用；其余金额为元，÷10000 转万元。
    净有息债务 = (短借+短期应付债券+一年内到期非流动负债+长借+应付债券) − 货币资金。
    非经营性资产 = 交易性金融资产+其他权益工具投资+其他非流动金融资产（不含现金，避免与净债务里
    扣减的现金重复计算）。两者均为按资产负债表科目的估算参考值，前端会提示需人工核对。
    """
    code = (request.GET.get('code') or '').strip()
    if not code:
        return JsonResponse({'available': True, 'found': False})

    cursor = _stock_cursor()
    if cursor is None:
        return JsonResponse({'available': False, 'found': False})

    try:
        with cursor:
            cursor.execute(
                'SELECT stock_code, stock_name FROM stock_basic WHERE stock_code = %s LIMIT 1',
                [code],
            )
            basic = cursor.fetchone()
            if basic is None:
                return JsonResponse({'available': True, 'found': False})
            stock_code, stock_name = basic

            # 总股本（万股）：优先 share_capital 最新一期，兜底 daily_quote。
            cursor.execute(
                'SELECT total_share FROM stock_share_capital WHERE stock_code = %s '
                'AND total_share IS NOT NULL ORDER BY change_date DESC LIMIT 1',
                [stock_code],
            )
            row = cursor.fetchone()
            shares = _to_float(row[0]) if row else None
            if shares is None:
                cursor.execute(
                    'SELECT total_share FROM stock_daily_quote WHERE stock_code = %s '
                    'AND total_share IS NOT NULL ORDER BY trade_date DESC LIMIT 1',
                    [stock_code],
                )
                row = cursor.fetchone()
                shares = _to_float(row[0]) if row else None

            # 经营现金流净额（最近年报，元→万元）作为 FCF 参考值。
            cursor.execute(
                'SELECT report_date, operating_cash_flow FROM stock_financial_summary '
                'WHERE stock_code = %s AND MONTH(report_date) = 12 '
                'AND operating_cash_flow IS NOT NULL ORDER BY report_date DESC LIMIT 1',
                [stock_code],
            )
            fin_row = cursor.fetchone()

            # 资产负债表明细（最近年报，元）：用于估算净有息债务与非经营性资产。
            cursor.execute(
                'SELECT report_date, monetary_funds, trade_finasset, other_equity_invest, '
                'other_noncurrent_finasset, short_loan, short_bond_payable, '
                'noncurrent_liab_1year, long_loan, bond_payable '
                'FROM stock_balance_sheet WHERE stock_code = %s AND MONTH(report_date) = 12 '
                'ORDER BY report_date DESC LIMIT 1',
                [stock_code],
            )
            bs_row = cursor.fetchone()

            # 公司速览（展示用）：基础信息 + 最新行情指标 + 最新年报盈利能力。
            cursor.execute(
                'SELECT market, industry, listing_date FROM stock_basic WHERE stock_code = %s',
                [stock_code],
            )
            basic_extra = cursor.fetchone()
            cursor.execute(
                'SELECT trade_date, market_cap, market_cap_52w_high, market_cap_52w_low, '
                'pe_ttm, pe_static, pb, pcf, dividend_yield, close_price FROM stock_daily_quote '
                'WHERE stock_code = %s ORDER BY trade_date DESC LIMIT 1',
                [stock_code],
            )
            quote_row = cursor.fetchone()
            cursor.execute(
                'SELECT report_date, revenue, net_profit_parent, roe, debt_ratio '
                'FROM stock_financial_summary WHERE stock_code = %s AND MONTH(report_date) = 12 '
                'ORDER BY report_date DESC LIMIT 1',
                [stock_code],
            )
            fin_overview = cursor.fetchone()
    except DatabaseError:
        return JsonResponse({'available': False, 'found': False})

    fcf = None
    fcf_report_date = None
    if fin_row and fin_row[1] is not None:
        ocf = _to_float(fin_row[1])
        if ocf is not None:
            fcf = round(ocf / 10000, 2)
            fcf_report_date = (
                fin_row[0].isoformat() if hasattr(fin_row[0], 'isoformat') else str(fin_row[0])
            )

    net_debt = None
    non_operating_assets = None
    balance_report_date = None
    if bs_row:
        (bs_date, monetary_funds, trade_finasset, other_equity_invest,
         other_noncurrent_finasset, short_loan, short_bond_payable,
         noncurrent_liab_1year, long_loan, bond_payable) = bs_row
        balance_report_date = (
            bs_date.isoformat() if hasattr(bs_date, 'isoformat') else str(bs_date)
        )

        debt_items = [short_loan, short_bond_payable, noncurrent_liab_1year, long_loan, bond_payable]
        debt_values = [_to_float(v) for v in debt_items]
        if any(v is not None for v in debt_values):
            interest_debt = sum(v for v in debt_values if v is not None)
            cash = _to_float(monetary_funds) or 0
            net_debt = round((interest_debt - cash) / 10000, 2)

        asset_items = [trade_finasset, other_equity_invest, other_noncurrent_finasset]
        asset_values = [_to_float(v) for v in asset_items]
        if any(v is not None for v in asset_values):
            non_op = sum(v for v in asset_values if v is not None)
            non_operating_assets = round(non_op / 10000, 2)

    # 公司速览：拼成 {label, value} 列表，值为空的项直接跳过不展示。
    overview_items = []
    as_of = None
    overview_report_date = None
    current_price = None
    if basic_extra:
        market, industry, listing_date = basic_extra
        sector = '·'.join(p for p in (market, industry) if p)
        if sector:
            overview_items.append({'label': '市场/行业', 'value': sector})
        if listing_date is not None:
            ld = listing_date.isoformat() if hasattr(listing_date, 'isoformat') else str(listing_date)
            overview_items.append({'label': '上市日期', 'value': ld})
    if quote_row:
        (q_date, market_cap, cap_high, cap_low, pe_ttm, pe_static, pb, pcf,
         div_yield, close_price) = quote_row
        as_of = q_date.isoformat() if hasattr(q_date, 'isoformat') else (str(q_date) if q_date else None)

        # 当前股价：优先收盘价，缺失时用 市值(亿元)→元 ÷ 总股本(万股)→股 推算。
        price = _to_float(close_price)
        mc = _to_float(market_cap)
        if price is None and mc is not None and shares not in (None, 0):
            price = mc * 1e8 / (shares * 1e4)
        if price is not None:
            current_price = round(price, 2)
        for label, raw, suffix in [
            ('总市值', market_cap, ' 亿元'),
            ('市盈率 TTM', pe_ttm, ''),
            ('市盈率（静）', pe_static, ''),
            ('市净率 PB', pb, ''),
            ('市现率 PCF', pcf, ''),
            ('股息率', div_yield, '%'),
        ]:
            v = _fmt_num(raw, suffix=suffix)
            if v is not None:
                overview_items.append({'label': label, 'value': v})
        cap_lo, cap_hi = _fmt_num(cap_low), _fmt_num(cap_high)
        if cap_lo and cap_hi:
            overview_items.append({'label': '52周市值区间', 'value': f'{cap_lo} ~ {cap_hi} 亿元'})
    if fin_overview:
        (f_date, revenue, net_profit, roe, debt_ratio) = fin_overview
        overview_report_date = (
            f_date.isoformat() if hasattr(f_date, 'isoformat') else str(f_date)
        )
        rev = _to_float(revenue)
        prof = _to_float(net_profit)
        for label, value in [
            ('营业收入', f'{rev / 1e8:,.2f} 亿元' if rev is not None else None),
            ('归母净利润', f'{prof / 1e8:,.2f} 亿元' if prof is not None else None),
            ('ROE', _fmt_num(roe, suffix='%')),
            ('资产负债率', _fmt_num(debt_ratio, suffix='%')),
        ]:
            if value is not None:
                overview_items.append({'label': label, 'value': value})

    overview = {
        'items': overview_items,
        'as_of': as_of,
        'report_date': overview_report_date,
    } if overview_items else None

    return JsonResponse({
        'available': True,
        'found': True,
        'ticker': stock_code,
        'company_name': stock_name or stock_code,
        'shares_outstanding': round(shares, 2) if shares is not None else None,
        'current_fcf': fcf,
        'fcf_report_date': fcf_report_date,
        'net_debt': net_debt,
        'non_operating_assets': non_operating_assets,
        'balance_report_date': balance_report_date,
        'current_price': current_price,
        'overview': overview,
    })


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
