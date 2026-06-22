# TODO

## 待办

- [ ] **股票代码自动带出基本信息**
  在「股票代码」输入框旁加「查询」按钮：输入代码 → 后端代理调用公开数据源 → 自动回填**公司名称**与**总股本（换算成万股）**，未来可进一步带出现金流财报辅助估算 FCFF。
  - 实现要点：在 Django 后端加代理 view（如 `/api/stock/<code>/`），**不要前端直接 fetch**（公开行情接口普遍有 CORS 限制），顺便做缓存与限频。
  - 候选数据源：
    - 东方财富裸接口 `https://push2.eastmoney.com/api/qt/stock/get?secid=1.600519&fields=...`（最轻量，`1.`=沪 `0.`=深，f84=总股本、f85=流通股）
    - AkShare（Python 库，免 token，最全）：`stock_individual_info_em` 取名称/总股本、`stock_cash_flow_sheet_by_report_em` 取现金流量表
    - 巨潮资讯网 `cninfo.com.cn`（官方法定披露，最权威但反爬较严）
  - 注意：裸接口为非官方，可能变更/限频；要稳定用 AkShare 或官方来源。
