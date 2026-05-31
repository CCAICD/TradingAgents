# a-stock-data 外部数据工具包审计报告

> 审计时间：2026-05-31
> 审计仓库：https://github.com/simonlin1212/a-stock-data
> 审计目的：评估是否可作为本项目 A 股数据层的主要参考来源

---

## 一、项目概览

**项目名称：** a-stock-data

**项目定位：** A 股全栈数据工具包 — 7 层架构 · 27 端点 · 13 数据源 · 零第三方数据封装依赖

**项目形态：** Skill.md + 内嵌 Python 代码（非传统 Python 包）

**最新版本：** V3.2.1（2026-05-30）

**作者：** Simon 林

**Stars：** 3k

**Forks：** 643

---

## 二、许可证结论

**许可证：** Apache License 2.0

**结论：**
- ✅ 可以自由使用、修改、分发
- ✅ 可以用于商业用途
- ⚠️ 需要保留 LICENSE 文件和 attribution
- ⚠️ 修改后的文件需要标注变更说明
- ✅ 适合放入本项目 third_party 或改造为 provider adapter

**许可证要求：**
1. 必须保留原始 LICENSE 文件
2. 必须保留 copyright notice（Copyright 2026 Simon Lin）
3. 修改后的文件需要标注变更说明
4. 如果有 NOTICE 文件，需要保留

---

## 三、项目形态判断

**形态：** SKILL.md + 内嵌 Python 代码

**特点：**
- 不是传统 Python 包，不能直接 `import`
- 是结构化 Markdown + 内嵌 Python 代码段
- 设计目标是让 AI 编程助手直接读取和执行
- 每个端点是一个独立的 Python 函数

**适合直接 import：** ❌ 否

**适合直接让 Agent 调用 SKILL.md：** ❌ 否

**适合抽取函数作为参考实现：** ✅ 是

**推荐方式：**
- 将稳定函数抽取为本项目 provider adapter
- 保留来源和许可证说明
- 适配本项目统一 schema

---

## 四、数据源层级整理

### 4.1 行情层（Market Data）

| 数据源 | 数据 | IP 封禁风险 |
|--------|------|------------|
| mootdx（通达信） | K线（多周期）+ 五档盘口 + 逐笔成交 + 实时报价 46 字段 | **不封 IP** |
| 腾讯财经 | PE(TTM) / PB / 总市值 / 流通市值 / 换手率 / 涨跌停价 / 指数 / ETF | **不封 IP** |
| 百度K线 | 日K线 + MA5/MA10/MA20 均价直接返回 | 极低 |

### 4.2 研报层（Research Reports）

| 数据源 | 数据 | IP 封禁风险 |
|--------|------|------------|
| 东财 reportapi | 研报列表 + 评级 + 三年 EPS 预测 | 中（已走 em_get 限流） |
| 东财 PDF 下载 | 完整研报 PDF（已处理 Referer 鉴权） | 中 |
| 同花顺一致预期 | 机构一致预期 EPS（直连 basic.10jqka.com.cn） | 低（需 UA） |
| iwencai NL 搜索 | 自然语言跨主题研报检索 | 低（需 Key） |

### 4.3 信号层（Signals）

| 数据源 | 数据 | IP 封禁风险 |
|--------|------|------------|
| 同花顺热点 | 当日强势股 + 题材归因 reason tags | 极低（零鉴权） |
| 同花顺北向（实时） | 沪股通 / 深股通分钟级流向（262 个时间点） | 极低 |
| 同花顺北向（历史） | 本地自缓存日级历史 | 无 |
| 百度概念板块 | 行业 / 概念 / 地域三维归属 + 当日涨跌幅 | 极低 |
| 东财资金流向 | 主力 / 大单 / 中单 / 小单 / 超大单分钟级净流入 | 中（已走 em_get 限流） |
| 龙虎榜席位 | 上榜记录 + 买卖席位 TOP5 + 机构动向 | 中 |
| 全市场龙虎榜 | 每日全市场上榜股票 + 净买额排名 + 上榜原因 | 中 |
| 限售解禁日历 | 历史解禁 + 未来 90 天待解禁预警 | 中 |
| 行业板块排名 | 东财行业涨跌/上涨下跌家数 | 中 |

### 4.4 资金面 / 筹码层（Capital Flow / Ownership）

| 数据源 | 数据 | IP 封禁风险 |
|--------|------|------------|
| 融资融券明细 | 日级融资余额/买入/偿还 + 融券余额/卖出/偿还 | 中 |
| 大宗交易 | 成交价/量 + 买卖方营业部 + 溢价率 | 中 |
| 股东户数变化 | 季度股东数 + 环比变化 + 户均持股 | 中 |
| 分红送转历史 | 每股派息/送股/转增 + 进度状态 | 中 |
| 个股资金流120日 | 主力/大单/中单/小单日级净流入 | 中 |

### 4.5 新闻层（News）

| 数据源 | 数据 | IP 封禁风险 |
|--------|------|------------|
| 个股新闻 | 东财个股新闻流（直连 search-api-web） | 中 |
| 全球资讯 | 东财全球财经资讯（直连 np-weblist，7×24） | 中 |
| ⚠️ 财联社快讯 | **已下线**（cls.cn 迁 Next.js，旧 API 404） | N/A |

### 4.6 基础数据层（Fundamentals）

| 数据源 | 数据 | IP 封禁风险 |
|--------|------|------------|
| 季报快照 | 37 字段（EPS / ROE / 净利润 / 主营收入...） | 低 |
| F10 公司资料 | 9 大类文本（截断优化，-70% token） | 低 |
| 东财个股信息 | 行业/总股本/流通股/市值/上市日期 | 中 |
| 新浪财报三表 | 资产负债表/利润表/现金流量表 | 低 |

### 4.7 公告层（Filings）

| 数据源 | 数据 | IP 封禁风险 |
|--------|------|------------|
| 巨潮 cninfo | 沪深北交所全量公告 | 低 |
| mootdx F10 | 最新提示（公告、分红、股东大会决议等摘要） | 无 |

---

## 五、端点清单（27 个）

### 5.1 行情层（3 个端点）

| 端点 | 函数名 | 数据源 | 需要 Key | MVP 优先级 |
|------|--------|--------|----------|-----------|
| mootdx 行情 | `get_market_data` | mootdx | 否 | ⭐⭐⭐ 高 |
| 腾讯财经 | `get_tencent_quote` | 腾讯 | 否 | ⭐⭐⭐ 高 |
| 百度K线 | `baidu_kline` | 百度 | 否 | ⭐⭐ 中 |

### 5.2 研报层（4 个端点）

| 端点 | 函数名 | 数据源 | 需要 Key | MVP 优先级 |
|------|--------|--------|----------|-----------|
| 东财 reportapi | `eastmoney_report_list` | 东财 | 否 | ⭐ 低 |
| 东财 PDF 下载 | `eastmoney_report_pdf` | 东财 | 否 | ⭐ 低 |
| 同花顺一致预期 | `ths_consensus_eps` | 同花顺 | 否 | ⭐⭐ 中 |
| iwencai NL 搜索 | `iwencai_search` | iwencai | **是** | ⭐ 低 |

### 5.3 信号层（9 个端点）

| 端点 | 函数名 | 数据源 | 需要 Key | MVP 优先级 |
|------|--------|--------|----------|-----------|
| 同花顺热点 | `ths_hot_stocks` | 同花顺 | 否 | ⭐⭐⭐ 高 |
| 同花顺北向（实时） | `ths_northbound_realtime` | 同花顺 | 否 | ⭐⭐ 中 |
| 同花顺北向（历史） | `ths_northbound_history` | 同花顺 | 否 | ⭐⭐ 中 |
| 百度概念板块 | `baidu_concept_blocks` | 百度 | 否 | ⭐⭐ 中 |
| 东财资金流向 | `eastmoney_fund_flow` | 东财 | 否 | ⭐⭐⭐ 高 |
| 龙虎榜席位 | `get_dragon_tiger_board` | 东财 | 否 | ⭐⭐ 中 |
| 全市场龙虎榜 | `get_daily_dragon_tiger` | 东财 | 否 | ⭐⭐ 中 |
| 限售解禁日历 | `get_lockup_expiry` | 东财 | 否 | ⭐⭐⭐ 高 |
| 行业板块排名 | `get_industry_ranking` | 东财 | 否 | ⭐⭐⭐ 高 |

### 5.4 资金面 / 筹码层（5 个端点）

| 端点 | 函数名 | 数据源 | 需要 Key | MVP 优先级 |
|------|--------|--------|----------|-----------|
| 融资融券明细 | `margin_trading` | 东财 | 否 | ⭐⭐ 中 |
| 大宗交易 | `block_trade` | 东财 | 否 | ⭐⭐ 中 |
| 股东户数变化 | `holder_num_change` | 东财 | 否 | ⭐⭐ 中 |
| 分红送转历史 | `dividend_history` | 东财 | 否 | ⭐ 低 |
| 个股资金流120日 | `stock_fund_flow_120d` | 东财 | 否 | ⭐⭐ 中 |

### 5.5 新闻层（2 个端点）

| 端点 | 函数名 | 数据源 | 需要 Key | MVP 优先级 |
|------|--------|--------|----------|-----------|
| 个股新闻 | `eastmoney_stock_news` | 东财 | 否 | ⭐⭐ 中 |
| 全球资讯 | `eastmoney_global_news` | 东财 | 否 | ⭐⭐ 中 |

### 5.6 基础数据层（4 个端点）

| 端点 | 函数名 | 数据源 | 需要 Key | MVP 优先级 |
|------|--------|--------|----------|-----------|
| 季报快照 | `get_quarterly_snapshot` | mootdx | 否 | ⭐⭐ 中 |
| F10 公司资料 | `get_f10_data` | mootdx | 否 | ⭐⭐⭐ 高 |
| 东财个股信息 | `eastmoney_stock_info` | 东财 | 否 | ⭐⭐ 中 |
| 新浪财报三表 | `sina_financial_report` | 新浪 | 否 | ⭐ 低 |

### 5.7 公告层（2 个端点）

| 端点 | 函数名 | 数据源 | 需要 Key | MVP 优先级 |
|------|--------|--------|----------|-----------|
| 巨潮公告 | `cninfo_filings` | 巨潮 | 否 | ⭐⭐⭐ 高 |
| mootdx F10 最新提示 | `get_f10_data`（最新提示类别） | mootdx | 否 | ⭐⭐⭐ 高 |

---

## 六、与本项目需求匹配度

### 6.1 行情层

**匹配度：** ⭐⭐⭐⭐⭐ 高

- mootdx + 腾讯财经可以覆盖本项目规划的行情需求
- 不封 IP，适合高频使用
- 支持 K 线、五档盘口、实时价格、PE/PB/市值

### 6.2 研报层

**匹配度：** ⭐⭐⭐ 中

- 东财 reportapi 可以作为研报来源
- iwencai 需要 API Key，可以作为后续扩展
- 本项目 MVP 阶段研报优先级较低

### 6.3 信号层

**匹配度：** ⭐⭐⭐⭐ 高

- 同花顺热点可以用于主线识别
- 东财资金流向可以用于资金面分析
- 行业板块排名可以用于 Market-Wide Scan
- 解禁日历可以用于 Negative Event Guard

### 6.4 资金面 / 筹码层

**匹配度：** ⭐⭐⭐ 中

- 融资融券、大宗交易、股东户数可以作为辅助数据
- 本项目 MVP 阶段优先级较低

### 6.5 新闻层

**匹配度：** ⭐⭐⭐ 中

- 东财个股新闻可以作为新闻来源
- 全球资讯可以替代已下线的财联社快讯
- 本项目新闻层定位是辅助验证和风险排雷

### 6.6 基础数据层

**匹配度：** ⭐⭐⭐⭐ 高

- mootdx F10 可以覆盖基本面数据需求
- 季报快照可以用于基本面排雷

### 6.7 公告层

**匹配度：** ⭐⭐⭐⭐⭐ 高

- 巨潮 cninfo 可以作为公告主源
- mootdx F10 最新提示可以作为补充摘要
- 与本项目公告层规划完全匹配

### 6.8 Market-Wide Scan

**匹配度：** ⭐⭐⭐⭐ 高

- 行业板块排名可以用于市场环境判断
- 全市场龙虎榜可以用于资金流向分析
- 同花顺热点可以用于主线识别

### 6.9 Negative Event Guard

**匹配度：** ⭐⭐⭐⭐⭐ 高

- 解禁日历可以用于解禁风险检查
- 巨潮公告可以用于公告风险检查
- F10 最新提示可以用于补充风险检查

### 6.10 Data Freshness Guard

**匹配度：** ⭐⭐⭐ 中

- a-stock-data 没有统一的数据新鲜度检查机制
- 需要在本项目中实现 Data Freshness Guard
- 但 a-stock-data 的端点可以提供 fetched_at 信息

---

## 七、可复用部分

### 7.1 高优先级可复用

| 端点 | 用途 | 复用方式 |
|------|------|----------|
| mootdx 行情 | K 线、五档盘口、实时价格 | 抽取为 provider adapter |
| 腾讯财经 | PE/PB/市值/换手率/涨跌停价 | 抽取为 provider adapter |
| 巨潮 cninfo | 公告数据 | 抽取为 provider adapter |
| mootdx F10 | 基本面数据、最新提示 | 抽取为 provider adapter |
| 同花顺热点 | 主线识别、强势股 | 抽取为 provider adapter |
| 东财资金流向 | 资金面分析 | 抽取为 provider adapter |
| 行业板块排名 | Market-Wide Scan | 抽取为 provider adapter |
| 限售解禁日历 | Negative Event Guard | 抽取为 provider adapter |

### 7.2 中优先级可复用

| 端点 | 用途 | 复用方式 |
|------|------|----------|
| 东财个股新闻 | 新闻层 | 抽取为 provider adapter |
| 全球资讯 | 新闻层（替代财联社快讯） | 抽取为 provider adapter |
| 同花顺北向 | 资金面分析 | 抽取为 provider adapter |
| 龙虎榜席位 | 资金面分析 | 抽取为 provider adapter |
| 融资融券明细 | 资金面分析 | 抽取为 provider adapter |
| 大宗交易 | 资金面分析 | 抽取为 provider adapter |

### 7.3 低优先级可复用

| 端点 | 用途 | 复用方式 |
|------|------|----------|
| 东财 reportapi | 研报层 | 后续阶段 |
| iwencai NL 搜索 | 研报层 | 需要 API Key，后续阶段 |
| 新浪财报三表 | 基础数据层 | 后续阶段 |
| 分红送转历史 | 资金面层 | 后续阶段 |

---

## 八、不建议直接复用部分

### 8.1 不建议直接复用

| 原因 | 说明 |
|------|------|
| SKILL.md 形态 | 不是传统 Python 包，不能直接 import |
| 内嵌 Python 代码 | 需要抽取为独立函数 |
| 缺少统一 schema | 没有 source/fetched_at/as_of_time/status/error_message |
| 缺少 raw payload 保存 | 没有原始数据保存机制 |
| 缺少 Data Freshness Guard | 没有数据新鲜度检查 |
| 东财接口有限流风险 | 需要统一限流机制 |

### 8.2 需要改造的部分

| 改造项 | 说明 |
|--------|------|
| 统一 schema | 所有端点输出必须适配本项目统一 schema |
| Data Freshness Guard | 所有端点必须接入 Data Freshness Guard |
| 东财限流 | 所有东财接口必须走统一限流（可以参考 em_get） |
| raw payload 保存 | 所有端点必须支持 raw payload 保存 |
| 错误处理 | 需要统一错误处理和重试机制 |

---

## 九、风险和注意事项

### 9.1 风险

| 风险 | 说明 | 缓解措施 |
|------|------|----------|
| 东财接口封 IP | 东财有频率风控，会封 IP | 使用 em_get 限流，优先用 mootdx/腾讯 |
| 接口失效 | 部分接口可能已失效 | 定期测试，保留 fallback |
| 缺少错误处理 | 部分端点缺少错误处理 | 统一错误处理机制 |
| 缺少数据新鲜度检查 | 没有 fetched_at/as_of_time | 在本项目中实现 Data Freshness Guard |
| 财联社快讯已下线 | cls.cn 旧 API 全面 404 | 使用东财全球资讯替代 |

### 9.2 注意事项

| 注意事项 | 说明 |
|----------|------|
| 许可证要求 | 必须保留 LICENSE 文件和 attribution |
| 数据源优先级 | mootdx/腾讯优先，东财仅用于独有数据 |
| iwencai 需要 API Key | 只有 iwencai 需要 Key，其他免费 |
| mootdx 需要国内 IP | TCP 直连通达信行情服务器，海外不稳定 |

---

## 十、推荐接入方式

### 10.1 接入策略

1. **a-stock-data 作为外部参考实现和端点说明来源**
   - 不直接让业务 Agent 调用 SKILL.md
   - 将稳定函数抽取为本项目 provider adapter

2. **保留 Apache-2.0 许可证和 attribution**
   - 在 third_party 或 docs/external_sources 中保留来源说明
   - 创建 THIRD_PARTY_NOTICES.md

3. **所有 provider 输出必须适配本项目统一 schema**
   - source
   - fetched_at
   - as_of_time
   - status
   - error_message
   - raw_payload_path

4. **所有 provider 必须接入 Data Freshness Guard**

5. **所有东财接口必须走统一限流**
   - 可以参考 a-stock-data 的 em_get() 实现

### 10.2 接入阶段

| 阶段 | 端点 | 说明 |
|------|------|------|
| MVP 第一批 | mootdx 行情、腾讯财经、巨潮公告、mootdx F10 | 行情+公告+基本面 |
| MVP 第二批 | 同花顺热点、东财资金流向、行业板块排名、解禁日历 | 信号层+风险检查 |
| Phase 3 | 东财个股新闻、全球资讯、同花顺北向 | 新闻层+资金面 |
| Phase 4 | 东财 reportapi、融资融券、大宗交易、股东户数 | 研报层+资金面 |
| 后续 | iwencai、新浪财报三表、分红送转 | 需要 API Key 或低优先级 |

---

## 十一、推荐接入方式详细说明

### 11.1 架构建议

```
tradingagents/
├─ providers/
│  ├─ base_provider.py          # 基础 provider 类，定义统一 schema
│  ├─ market_data/
│  │  ├─ mootdx_provider.py     # mootdx 行情 provider
│  │  ├─ tencent_provider.py    # 腾讯财经 provider
│  │  └─ baidu_provider.py      # 百度K线 provider
│  ├─ news/
│  │  ├─ eastmoney_news_provider.py  # 东财新闻 provider
│  │  └─ global_news_provider.py     # 全球资讯 provider
│  ├─ filings/
│  │  ├─ cninfo_provider.py     # 巨潮公告 provider
│  │  └─ mootdx_f10_provider.py # mootdx F10 provider
│  ├─ signals/
│  │  ├─ ths_hot_provider.py    # 同花顺热点 provider
│  │  ├─ eastmoney_fund_flow_provider.py  # 东财资金流向 provider
│  │  └─ industry_ranking_provider.py     # 行业板块排名 provider
│  └─ fundamentals/
│      ├─ mootdx_quarterly_provider.py  # mootdx 季报 provider
│      └─ eastmoney_info_provider.py    # 东财个股信息 provider
├─ dataflows/
│  ├─ freshness_guard.py        # Data Freshness Guard
│  └─ rate_limiter.py           # 东财限流器
└─ ...
```

### 11.2 统一 Schema

```python
class ProviderOutput:
    source: str              # 数据源名称
    fetched_at: datetime     # 获取时间
    as_of_time: datetime     # 数据截止时间
    status: str              # success/partial/error
    error_message: str       # 错误信息（如果有的话）
    raw_payload_path: str    # 原始数据保存路径
    data: Any                # 实际数据
```

### 11.3 东财限流器

可以参考 a-stock-data 的 em_get() 实现：

```python
class EastmoneyRateLimiter:
    EM_MIN_INTERVAL = 1.0  # 最小间隔 1 秒
    EM_JITTER_MIN = 0.1    # 随机抖动最小值
    EM_JITTER_MAX = 0.5    # 随机抖动最大值
    
    def get(self, url: str, params: dict = None) -> dict:
        # 串行限流 + 随机抖动 + 会话复用
        ...
```

---

## 十二、推荐接入阶段

### 12.1 Phase 2（手动热榜和 Attention Pool）

**接入端点：**
- mootdx 行情（K 线、五档盘口、实时价格）
- 腾讯财经（PE/PB/市值/换手率/涨跌停价）

**用途：**
- 为 Attention Pool 中的股票提供行情数据
- 支持基础趋势结构分析

### 12.2 Phase 3（A 股报告 MVP）

**接入端点：**
- 巨潮 cninfo（公告数据）
- mootdx F10（基本面数据、最新提示）
- 同花顺热点（主线识别）
- 东财资金流向（资金面分析）
- 行业板块排名（Market-Wide Scan）
- 限售解禁日历（Negative Event Guard）

**用途：**
- 支持尾盘报告、盘后报告
- 支持市场环境判断和主线识别
- 支持风险检查

### 12.3 Phase 4（数据源接入）

**接入端点：**
- 东财个股新闻（新闻层）
- 全球资讯（新闻层）
- 同花顺北向（资金面）
- 龙虎榜席位（资金面）
- 融资融券明细（资金面）
- 大宗交易（资金面）

**用途：**
- 完善新闻层
- 完善资金面分析

### 12.4 后续阶段

**接入端点：**
- 东财 reportapi（研报层）
- iwencai NL 搜索（研报层，需要 API Key）
- 新浪财报三表（基础数据层）
- 分红送转历史（资金面层）

---

## 十三、结论

### 13.1 总体评价

a-stock-data 是一个高质量的 A 股数据工具包，具有以下优点：

1. **数据源覆盖全面**：7 层架构、27 端点、13 数据源
2. **数据源优先级合理**：mootdx/腾讯优先（不封 IP），东财仅用于独有数据
3. **有统一限流机制**：em_get() 可以防止东财封 IP
4. **许可证友好**：Apache-2.0，可以自由使用和修改
5. **活跃维护**：最近更新于 2026-05-30，有 3k stars

### 13.2 推荐接入方式

1. **不直接整包硬拷**
2. **抽取稳定函数为 provider adapter**
3. **保留 Apache-2.0 许可证和 attribution**
4. **适配本项目统一 schema**
5. **接入 Data Freshness Guard**
6. **所有东财接口走统一限流**

### 13.3 风险提示

1. 东财接口有封 IP 风险，需要统一限流
2. 部分接口可能已失效，需要定期测试
3. 缺少数据新鲜度检查，需要在本项目中实现
4. 财联社快讯已下线，需要使用东财全球资讯替代

---

**文档结束。**

> 本文档由 opencode 于 2026-05-31 创建。
