import akshare as ak


def fetch_company_profile(stock_code):
    df = ak.stock_profile_cninfo(symbol=stock_code)
    if df.empty:
        return None
    row = df.iloc[0]
    return {
        "stock_code": stock_code,
        "market": row.get("所属市场"),
        "stock_name": row.get("A股简称"),
        "company_name": row.get("公司名称"),
        "industry": row.get("所属行业"),
        "listing_date": row.get("上市日期"),
        "website": row.get("官方网站"),
        "email": row.get("电子邮箱"),
        "phone": row.get("联系电话"),
        "registered_address": row.get("注册地址"),
        "office_address": row.get("办公地址"),
        "main_business": row.get("主营业务"),
        "business_scope": row.get("经营范围"),
        "company_profile": row.get("机构简介"),
    }
