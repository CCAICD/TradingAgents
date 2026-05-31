# DATA_SOURCES.md — 数据源规划

> 本文档规划项目的数据源。当前尚未实现任何 A 股数据源接入。

---

## 一、数据源总原则

1. **数据必须有元信息。** 每个数据源返回的数据必须包含：`source`、`fetched_at`、`as_of_time`、`status`、`error_message`。
2. **数据过期必须先更新。** 系统应先自动更新，不要先询问用户。
3. **更新失败必须如实说明。** 不能隐瞒数据源故障。
4. **不允许编造数据。** 数据缺失时必须如实说明。
5. **原始数据 raw payload 尽量保留。** 便于追溯和调试。

---

## 二、A 股计划数据源

### 行情数据

| 数据源 | 用途 | 优先级 |
|--------|------|--------|
| mootdx | K线、分钟线、逐笔、实时价格、五档盘口、finance、F10 | 主要 |
| 腾讯财经 | PE、PB、市值、换手率、涨跌停价 | 辅助 |
| akshare | 行情备用、板块、新闻、涨停池等 | 备用 |

### 新闻数据

| 数据源 | 用途 | 优先级 |
|--------|------|--------|
| akshare 个股新闻 | 个股催化、利空 | 主要 |
| akshare 财联社快讯 | 实时快讯 | 主要 |
| akshare 东财全球资讯 | 宏观新闻 | 辅助 |

### 研报数据

| 数据源 | 用途 | 优先级 |
|--------|------|--------|
| 东财 reportapi | 研报标题、评级 | 低优先级 |
| akshare THS 一致预期 | 一致预期数据 | 低优先级 |
| iwencai | 自然语言选股 | 后续可能需要 API key |

### 基本面数据

| 数据源 | 用途 | 优先级 |
|--------|------|--------|
| mootdx finance | 基本面快照 | 主要 |
| mootdx F10 | F10 资料 | 主要 |
| akshare 基本面 | 基本面备用 | 辅助 |
| 标准财报三表 | 深度排雷 | 后续可能补充 |

---

## 三、新闻和基本面定位

- **不作为 A 股短线主驱动**
- 主要用于：
  - 催化解释
  - 政策背景
  - 确定性利空识别
  - 公告风险识别
  - 监管风险识别
  - 基本面排雷
- **重大利空应强降权或一票否决**

---

## 四、数据新鲜度阈值摘要

### 尾盘辅助决策报告

| 数据类型 | 新鲜度阈值 |
|----------|-----------|
| 实时价格 | 2 分钟以内 |
| 分钟 K 线 | 10 分钟以内 |
| 五档盘口 | 2 分钟以内 |
| 成交额/换手率 | 5 分钟以内 |
| 板块涨幅/成交额 | 5-10 分钟以内 |
| 涨停/炸板/连板数据 | 5 分钟以内 |
| 新闻快讯 | 15 分钟以内 |
| 重大利空/公告 | 30 分钟以内 |
| 手动热榜 | 使用最近一次，缺失则提醒用户 |

### 盘后复盘报告

| 数据类型 | 新鲜度阈值 |
|----------|-----------|
| 日 K | 必须更新到最近交易日 |
| 分钟 K | 必须覆盖当日完整交易时段 |
| 成交额/换手率 | 必须更新到收盘 |
| 涨停/跌停/炸板/连板数据 | 收盘后 30 分钟内更新 |
| 板块涨幅/成交额 | 收盘后 30 分钟内更新 |
| 新闻快讯 | 30 分钟内更新 |
| 公告/重大利空 | 2 小时内更新 |

### 次日计划/非交易时间分析

| 数据类型 | 新鲜度阈值 |
|----------|-----------|
| 日 K、板块、涨停、情绪数据 | 必须更新到最近一个交易日 |
| 新闻 | 12 小时以内 |
| 公告/利空 | 12 小时以内 |
| 研报 | 7 天以内 |
| 基本面快照 | 30 天以内或最近财报期 |

### 关键数据失败时

- 实时价格、分钟 K、日 K、板块数据、涨停状态等关键数据失败：**不能生成尾盘参与建议和强结论**
- 新闻失败：可以继续做资金和结构分析，但不能做完整利空排雷
- 研报失败：可以继续短线分析
- 手动热榜缺失：可以使用已有 Attention Pool，但必须提示热榜不完整

---

## 五、当前实现状态

- 当前只是数据源规划
- 尚未实现 A 股数据源接入
- 尚未实现 Data Freshness Guard
- **尚未实现公告层（Disclosure Layer）数据接入**
- **尚未实现 Disclosure Guard**
- 尚未实现自动更新
- 尚未实现数据源 fallback
- 原项目已有 yfinance 和 Alpha Vantage 数据源（面向美股）

---

## 六、数据存储路径

未来数据源必须写入项目本地目录，不能默认写到用户 home：

| 数据类型 | 存储路径 |
|----------|----------|
| 原始行情数据 | `data/market_data/` |
| 新闻数据 | `data/news/` |
| 热榜原始文本 | `data/manual_hotlists/raw_text/` |
| 热榜结构化数据 | `data/manual_hotlists/structured/` |
| 热榜事件日志 | `data/manual_hotlists/events/` |
| 生成的报告 | `data/reports/` |
| 持仓数据 | `data/portfolio/` |
| Raw payload | `.tradingagents/raw/` |
| 缓存数据 | `.tradingagents/cache/` |
| 日志 | `.tradingagents/logs/` |
| 反思记录 | `.tradingagents/reflections/` |

**注意：** `.tradingagents/` 下的运行数据不应提交到 git。

---

## 七、未来数据字段需求

每只股票至少需要支持以下字段：

| 字段 | 说明 |
|------|------|
| 股票代码 | 如 600519、000001 |
| 股票名称 | 如贵州茅台 |
| 所属市场/板块类型 | 主板、创业板、科创板、北交所 |
| 是否主板 | 布尔值 |
| 是否 ST / *ST | 布尔值 |
| 是否停牌 | 布尔值 |
| 当前价格 | 浮点数 |
| 是否涨停 | 布尔值 |
| 涨停价 | 浮点数 |
| 成交额 | 浮点数（万元或亿元） |
| 换手率 | 百分比 |
| 所属主题/行业 | 列表，可能属于多个主题 |
| 数据更新时间 | 时间戳 |

**注意：** 这些字段为未来实现预留，当前尚未实现。

---

## 八、全市场扫描未来数据需求

Market-Wide Scan 需要以下数据类型：

| 数据类型 | 说明 |
|----------|------|
| 指数行情 | 上证指数、深证成指、创业板指等 |
| 全市场涨跌家数 | 上涨、下跌、平盘家数 |
| 全市场成交额 | 两市总成交额 |
| 涨停池 | 当日涨停股票列表 |
| 跌停池 | 当日跌停股票列表 |
| 炸板率 | 涨停后打开的比例 |
| 连板高度 | 最高连板天数 |
| 板块涨幅 | 各板块涨跌幅排名 |
| 板块成交额 | 各板块成交额排名 |
| 板块涨停数量 | 各板块涨停股票数量 |
| 个股成交额排名 | 全市场成交额前 N 名 |
| 个股涨幅排名 | 全市场涨幅前 N 名 |
| 换手率 | 高换手率股票 |
| 主题/行业归属 | 个股所属主题/行业 |
| 个股与板块相对强弱 | 个股强于/弱于板块 |

**注意：** 这些数据为全市场扫描预留，当前尚未实现。

---

## 九、公告层（Disclosure Layer）

**公告层定位：**

公告层不是普通新闻层。公告层的核心作用是：
1. 识别确定性利空
2. 识别重大公告催化
3. 识别监管、退市、ST、减持、解禁、业绩暴雷等硬风险
4. 在尾盘、盘后、次日计划、持仓建议前做风险排查
5. 对高风险标的执行强降权或一票否决

**主源：巨潮 cninfo**

| 字段 | 说明 |
|------|------|
| data_type | 公告数据 |
| primary_source | 巨潮 cninfo（优先使用 akshare 封装接口） |
| backup_source | mootdx F10 最新提示（补充摘要） |
| update_frequency | 交易日实时/准实时 |
| freshness_threshold | 尾盘 30-60 分钟；盘后 1-2 小时 |
| storage_path | `data/announcements/` |
| used_by_agent | Negative Event Guard、Fundamental Risk Guard、Decision Summary Agent |
| risk_level_mapping | Level 0-3 |

**目标字段：**
- 股票代码
- 股票简称
- 公告标题
- 公告类型/类别
- 公告日期/时间
- 公告链接
- 市场范围：沪市、深市、北交所 / 沪深京
- source
- fetched_at
- as_of_time
- raw_payload_path

**补充源：mootdx F10**

| 字段 | 说明 |
|------|------|
| data_type | F10 最新提示 |
| primary_source | mootdx F10 |
| backup_source | 无 |
| update_frequency | 交易日 |
| freshness_threshold | 当日 |
| storage_path | `.tradingagents/raw/f10/` |
| used_by_agent | Negative Event Guard（补充摘要） |
| risk_level_mapping | Level 0-3 |

**用途：**
- 使用"最新提示"类别
- 用于公告、分红、股东大会决议、最新事项摘要
- 定位是补充摘要，不是原始公告权威来源

**后续可扩展：**
- 交易所公告
- 问询函/监管函
- 东财公告备用源

**公告风险分层：**

| Level | 名称 | 说明 | 处理方式 |
|-------|------|------|----------|
| Level 0 | 普通公告 | 董事会、监事会、普通经营公告、普通股东大会 | 正常处理 |
| Level 1 | 需要提示 | 权益分派、股权激励、定增、可转债、重大合同、业绩预告 | 提示关注 |
| Level 2 | 强风险提示 | 大额减持、解禁、业绩大幅下滑、诉讼仲裁、补充更正、澄清致歉、风险提示 | 强风险提示 |
| Level 3 | 强降权或一票否决 | 立案调查、监管处罚、财务造假、ST/*ST、特别处理和退市、退市整理期、债务违约、实控人或高管重大风险 | 强降权或一票否决 |

**建议未来存储路径：**
- `data/announcements/` — 公告数据
- `.tradingagents/raw/announcements/` — 原始公告数据
- `.tradingagents/reports/announcement_checks/` — 公告检查报告

**当前实现状态：**
- 公告层已规划
- 尚未实现公告数据接入
- 尚未实现 Disclosure Guard

---

## 十、遗留项目历史数据

**数据来源：**
- `C:\github\tradingagents-old` — 用户之前魔改的 tradingagents 项目
- `C:\github\stock-pool` — 独立的股票池管理系统（暂不迁移，仅作为参考资源）

**数据类型：**
- 热榜 JSONL 数据（16 个交易日，449 条有效记录）
- 票池 active.json（100+ 只股票滚动聚合）
- 股票名称映射（3315 个）

**用途：**
- 初始化 Attention Pool
- 为反思系统提供历史数据
- 不是外部实时数据源，而是用户本地历史数据源

**迁移状态：**
- ✅ tradingagents-old 热榜数据已迁移到 `data/manual_hotlists/legacy_import/`
- ❌ stock-pool 暂不迁移，仅作为参考资源

**必须保留的溯源信息：**
- `original_path`：原始文件路径
- `source_project`：来源项目（tradingagents-old）
- `imported_at`：迁移时间
- `import_batch_id`：迁移批次 ID

**存储路径：**
- `data/manual_hotlists/legacy_import/raw/tradingagents-old/` — 原始热榜 JSONL 副本
- `data/manual_hotlists/legacy_import/structured/tradingagents-old/` — 标准化 JSONL
- `data/manual_hotlists/legacy_import/structured/tradingagents-old/by_date/` — 按日期的 JSONL
- `data/manual_hotlists/legacy_import/audit/` — 审计报告和无效记录

**迁移脚本：**
- `scripts/migrate_legacy_hotlists.py` — 可重复运行的迁移脚本

**注意：** 
- 旧项目代码只能参考，旧项目规则必须重新审查，不能直接把旧项目混乱逻辑带入新项目
- legacy_import 是历史迁移区，不等于正式每日录入区
- 使用 legacy 数据时必须标记 source_project
- 旧数据不能覆盖新数据

---

## 十一、a-stock-data 外部参考实现

**来源仓库：** https://github.com/simonlin1212/a-stock-data

**项目形态：** Skill.md + 内嵌 Python 代码（非传统 Python 包）

**许可证：** Apache-2.0（可以自由使用，需要保留 attribution）

**覆盖数据层：**
- 行情层（mootdx + 腾讯财经 + 百度K线）
- 研报层（东财 reportapi + 同花顺一致预期 + iwencai）
- 信号层（同花顺热点 + 北向资金 + 概念板块 + 资金流向 + 龙虎榜 + 解禁 + 行业排名）
- 资金面/筹码层（融资融券 + 大宗交易 + 股东户数 + 分红送转 + 资金流）
- 新闻层（东财个股新闻 + 全球资讯）
- 基础数据层（季报快照 + F10 + 个股信息 + 财报三表）
- 公告层（巨潮 cninfo + mootdx F10 最新提示）

**数据源优先级：**
1. mootdx（通达信）— 不封 IP，K线/五档/逐笔/财务/F10
2. 腾讯财经 — 不封 IP，实时价/PE/PB/市值/换手率
3. 同花顺热点/北向 — 极低风险
4. 百度股市通 — 极低风险
5. 新浪财经 — 低风险
6. 巨潮 cninfo — 低风险
7. 同花顺一致预期 — 低风险（需 UA）
8. iwencai — 低风险（需 Key）
9. 东财 — 中风险（有风控会封 IP，已走 em_get 限流）

**推荐使用方式：**
- a-stock-data 作为外部参考实现和端点说明来源
- 不直接让业务 Agent 调用 SKILL.md
- 后续将其稳定函数抽取为本项目 provider adapter
- 保留 Apache-2.0 许可证和 attribution
- 所有 provider 输出必须适配本项目统一 schema
- 所有 provider 必须接入 Data Freshness Guard
- 所有东财接口必须走统一限流

**风险：**
- 东财接口有封 IP 风险，需要统一限流
- 部分接口可能已失效，需要定期测试
- 缺少数据新鲜度检查，需要在本项目中实现
- 财联社快讯已下线，需要使用东财全球资讯替代

**接入前置条件：**
- 建立 provider adapter 架构
- 定义统一 schema（source/fetched_at/as_of_time/status/error_message/raw_payload_path）
- 实现东财限流器（参考 em_get）
- 实现 Data Freshness Guard

**详细审计报告：** `docs/external_sources/A_STOCK_DATA_AUDIT.md`

---

## 十二、Phase 2 热榜数据来源

**数据来源：**
- 手动输入（manual_input）：用户通过 CLI 或脚本导入的热榜文本
- 历史迁移（tradingagents-old）：从 legacy_import 导入的历史热榜数据

**数据类型：**
- 热榜文本（raw_text）：用户提供的原始文本
- 结构化热榜（structured）：解析后的 JSONL 格式
- Attention Pool：基于热榜数据构建的注意力池

**存储路径：**
- `data/manual_hotlists/raw_text/` — 原始热榜文本
- `data/manual_hotlists/structured/` — 结构化热榜 JSONL
- `data/manual_hotlists/events/` — 热榜事件日志
- `data/manual_hotlists/attention_pool/` — Attention Pool 输出
- `data/manual_hotlists/attention_pool/by_date/` — 按日期的 Attention Pool
- `data/manual_hotlists/attention_pool/audit/` — 审计报告

**注意：**
- 这不是实时行情源
- 不提供价格、涨停、成交额等字段
- 仅作为热度输入，不能单独生成尾盘参与建议
- 非主板股票未被剔除，可作为主线强度证据

---

## 十三、stock-pool 本地名称映射

**数据来源：** `C:\github\stock-pool\stock_names.json`

**数据类型：** 本地参考数据，不是实时数据源

**数据量：** 3053 条股票名称映射

**用途：**
- 修复历史热榜中 name 缺失的记录
- 用于 board_type 离线推断

**存储路径：**
- `data/reference/stock_name_map.json` — 轻量映射（code → name）
- `data/reference/stock_name_map.jsonl` — 完整映射（含元数据）

**注意：**
- 不能用于行情判断
- 不能用于交易资格判断
- 只是本地参考数据

---

## 十四、数据新鲜度守卫（Data Freshness Guard）

**定位：** 系统级基础设施，用于检查数据新鲜度、判断是否过期、给出能否生成报告的结论。

**核心原则：**
- 不负责抓取数据，只负责检查状态
- 所有正式报告必须先调用 DataFreshnessGuard
- 数据过期必须降级或阻断，不能默认通过
- 公告失败不能声称"无重大利空"

**标准字段（DataStatus）：**

| 字段 | 说明 |
|------|------|
| dataset_name | 数据集名称 |
| market | 市场标识 |
| source | 数据来源 |
| status | fresh/stale/missing/failed/partial/unknown |
| fetched_at | 最后获取时间 |
| as_of_time | 数据截止时间 |
| max_age_seconds | 新鲜度阈值（null = 不按秒级检查） |
| required | 是否必需 |
| error_message | 错误信息 |
| raw_payload_path | 原始数据路径 |

**provider 未来必须返回：**
- `source`
- `fetched_at`
- `as_of_time`
- `status`
- `error_message`
- `raw_payload_path`

**配置文件：** `config/data_freshness.yaml`

**支持的 report_type：**
- `pre_close_report` — 尾盘辅助决策报告
- `post_close_report` — 盘后复盘报告
- `next_day_plan` — 次日观察计划
- `attention_pool` — Attention Pool 构建

**实现状态：**
- ✅ DataStatus / ReportFreshnessResult 模型
- ✅ DataFreshnessGuard 类
- ✅ 报告阻断/降级逻辑
- ✅ auto_update 预留接口
- ❌ 真实数据源更新
- ❌ 交易日历精确判断

---

## 十五、外部数据源更新检查

**a-stock-data 定位：** 外部参考实现，不是直接依赖。

**更新检查机制：**
- 定期检查上游仓库变化
- 检查内容：commit、release、SKILL.md、README.md、CHANGELOG.md、LICENSE
- 更新检查不等于集成
- 更新后必须重新审计关键端点

**风险分级：**
- Low：README 文档说明变化、示例变化
- Medium：CHANGELOG 提到接口修复、新增数据源、修改限流建议
- High：SKILL.md 中函数实现变化、关键接口变化、LICENSE 变化

**集成策略：**
- ✅ 可以自动检查更新
- ❌ 不允许自动合并上游代码
- ❌ 不允许自动修改 provider
- ❌ 不允许自动修改业务逻辑
- ⚠️ 上游更新后只能生成审计报告和人工确认事项

**检查脚本：** `scripts/check_a_stock_data_updates.py`

**基线文件：** `docs/external_sources/a_stock_data_baseline.json`

**provider adapter 只有在人工确认后才更新。**

---

## 十六、Market-Wide Scan 数据需求

**定位：** 全市场扫描层，用于判断市场环境、情绪状态、板块强弱、主线候选。

**未来需要的数据类型：**

| 数据类型 | 说明 |
|----------|------|
| 指数数据 | 上证指数、深证成指、创业板指、北证50、科创50 |
| 市场涨跌家数 | 上涨、下跌、平盘家数 |
| 成交额 | 两市总成交额、沪市/深市/北交所分拆 |
| 板块涨幅 | 各板块涨跌幅排名 |
| 板块成交额 | 各板块成交额排名 |
| 涨停池 | 当日涨停股票列表 |
| 跌停池 | 当日跌停股票列表 |
| 炸板率 | 涨停后打开的比例 |
| 连板高度 | 最高连板天数 |
| 强势股排名 | 全市场涨幅/成交额前 N 名 |
| 个股与板块相对强弱 | 个股强于/弱于板块 |

**实现状态：**
- ✅ 数据结构 schema
- ✅ 离线样例
- ✅ freshness 对接骨架
- ❌ 真实数据源接入

**注意：** 本阶段只是 schema，尚未接入真实数据源。

---

## 十七、Theme Detection 数据依赖

**定位：** 主线识别层，连接 Market-Wide Scan 和 Attention Pool。

**未来依赖的数据：**

| 数据类型 | 说明 |
|----------|------|
| Market-Wide Scan | 全市场扫描结果 |
| Attention Pool | 热度池数据 |
| 板块数据 | 板块涨幅、成交额、涨停数 |
| 涨停池 | 涨停股票列表 |
| 成交额 | 两市成交额 |
| 强势股排名 | 全市场强势股 |
| 新闻催化 | 政策/行业新闻 |
| 公告风险 | 重大公告、风险提示 |
| 研报/政策 | 可选 |
| 用户手动主题提示 | 可选 |

**实现状态：**
- ✅ 数据结构 schema
- ✅ 评分骨架
- ✅ 离线样例
- ❌ 真实数据接入

---

## 十八、Candidate Selection 数据依赖

**定位：** 标的选择层，连接 Theme Detection 和 Report。

**未来依赖的数据：**

| 数据类型 | 说明 |
|----------|------|
| Theme Detection Result | 主线候选结果 |
| Attention Pool | 热度池数据 |
| 实时价格 | 最新价格 |
| 是否涨停 | 涨停状态 |
| 涨停价 | 涨停价格 |
| 成交额 | 成交额 |
| 换手率 | 换手率 |
| board_type | 板块类型 |
| ST / *ST | ST 状态 |
| 停牌状态 | 是否停牌 |
| 公告风险 | 重大公告、风险提示 |
| 基本面风险 | 业绩暴雷、财务异常 |
| 趋势结构数据 | 平台整理、突破、回踩等 |

**实现状态：**
- ✅ 数据结构 schema
- ✅ 平替规则骨架
- ✅ 候选评分骨架
- ❌ 真实数据接入

---

---

## 十九、Provider Adapter 基础设施

**定位：** 所有外部数据源必须通过 Provider Adapter 接入，不得在业务逻辑中直接调用第三方库。

### 总原则

1. **新数据源必须通过 provider adapter 接入。** 不得在业务逻辑中直接写 `requests` / `mootdx` / 第三方调用。
2. **Provider 必须返回 `ProviderResult`。** 统一返回类型，包含状态、元信息、数据。
3. **`ProviderResult` 必须可转换为 `DataStatus`。** 用于 `DataFreshnessGuard` 检查。
4. **数据必须经过 `DataFreshnessGuard` 才能进入正式报告。** 不得绕过新鲜度检查。
5. **Provider 必须尽量保留原始响应。** 便于审计和复盘。

### ProviderResult 标准字段

| 字段 | 说明 |
|------|------|
| `provider_name` | 供应器名称（如 `local_hotlist`、`mootdx`、`tencent`） |
| `market` | 市场标识（`cn_stock`、`us_stock`、`crypto`） |
| `dataset_name` | 数据集名称（如 `realtime_quote`、`attention_pool`） |
| `source` | 数据来源标识（如 `local_file`、`tcp_tdx`、`http_eastmoney`） |
| `status` | 状态枚举（`success`、`partial`、`empty`、`failed`、`skipped`、`not_implemented`） |
| `fetched_at` | 最后获取时间 |
| `as_of_time` | 数据截止时间 |
| `data` | 原始数据 |
| `normalized_data` | 标准化数据 |
| `raw_payload_path` | 原始载荷存储路径 |
| `error_message` | 错误信息 |
| `warnings` | 警告信息列表 |
| `metadata` | 附加元信息 |

### Raw Payload 保存规则

- 默认保存到 `.tradingagents/raw/cn_stock/<provider_name>/<dataset_name>/<YYYY-MM-DD>/`
- 不保存到用户 home
- 不提交 raw payload 到 git（`.gitignore` 已配置忽略 `.tradingagents/`）
- Provider 必须尽量保留原始响应，便于审计和复盘

### DataStatus 转换规则

| ProviderStatus | DataStatus | 说明 |
|---------------|------------|------|
| `success` | `fresh` | 有 `fetched_at` 且在阈值内 |
| `success` | `unknown` | 无 `fetched_at` 或无法判断 |
| `failed` | `failed` | 必须保留 `error_message` |
| `empty` | `missing` | 数据源返回空 |
| `empty` | `partial` | 部分数据缺失 |
| `not_implemented` | `unknown` 或 `missing` | 尚未实现 |
| `skipped` | `unknown` | 跳过获取 |

**转换时必须保留：** `error_message`、`source`、`raw_payload_path`、`metadata`。

### RateLimiter 规则

1. **所有外部 HTTP provider 必须支持限流。**
2. **东财类接口必须走统一限流。** 参考 `em_get` 模式。
3. **不允许并发乱打容易封 IP 的接口。**
4. **限流配置：** `min_interval_seconds`、`jitter_seconds`、`max_calls_per_minute`。
5. **测试模式：** `test_mode=True` 时不实际等待。

### Provider Registry

- 记录 `implemented` provider（已注册、可调用）
- 记录 `planned` provider（已知但未实现）
- 按 `dataset_name` 查找 provider
- 按 `provider_name` 获取 provider

### 当前实现状态

| 组件 | 状态 |
|------|------|
| ProviderResult schema | ✅ 已实现 |
| BaseCnStockProvider | ✅ 已实现 |
| RawPayloadStore | ✅ 已实现 |
| RateLimiter | ✅ 已实现 |
| ProviderRegistry | ✅ 已实现 |
| LocalHotlistProvider | ✅ 已实现 |
| ProviderResult → DataStatus | ✅ 已实现 |
| cn_stock_providers.yaml | ✅ 已实现 |
| 外部 provider | ❌ 未实现 |
| 真实 API 调用 | ❌ 未调用 |
| a-stock-data 代码接入 | ❌ 未接入 |

### Planned Providers

| Provider | 类型 | 状态 | 数据集 |
|----------|------|------|--------|
| `local_hotlist` | local | ✅ 已实现 | `manual_hotlist`、`attention_pool` |
| `mootdx` | external | ✅ 部分实现 | `daily_kline`、`minute_kline`、`index_kline`、`realtime_quote`、`order_book` |
| `tencent` | external | ❌ 未实现 | `valuation`、`limit_price`、`market_cap`、`turnover_rate` |
| `cninfo` | external | ❌ 未实现 | `announcement` |
| `eastmoney` | external | ❌ 未实现 | `sector_data`、`money_flow`、`news`、`global_news` |
| `ths` | external | ❌ 未实现 | `hot_topics`、`consensus_forecast` |
| `akshare` | external | ❌ 未实现 | 后续 fallback / 补充，不作为第一主路径 |

---

## 二十、mootdx 行情 Provider

**定位：** A 股基础行情数据供应器，通过通达信（TDX）协议获取数据。

**Provider 类：** `tradingagents.markets.cn_stock.data_providers.mootdx_provider.MootdxProvider`

**实现状态：** ✅ 部分实现（Phase 4B）

### 支持的 dataset

| dataset_name | 说明 | 状态 |
|--------------|------|------|
| `daily_kline` | 日 K 线数据 | ✅ 已实现 |
| `minute_kline` | 分钟 K 线数据（1min/5min/15min/30min/60min） | ✅ 已实现 |
| `index_kline` | 指数 K 线数据 | ✅ 已实现 |
| `realtime_quote` | 实时行情快照 | ✅ 已实现 |
| `order_book` | 五档盘口（从 quote 提取） | ✅ 已实现（partial） |

**未实现（后续阶段）：**
- `finance` — 基本面快照
- `f10` — F10 资料
- 逐笔成交
- 资金流

### Raw Payload 路径

```
.tradingagents/raw/cn_stock/mootdx/<dataset_name>/<YYYY-MM-DD>/
```

### Freshness 对接

| dataset | 新鲜度阈值 | 说明 |
|---------|-----------|------|
| `daily_kline` | null | 必须是最新交易日 |
| `minute_kline` | 600s | 10 分钟内 |
| `realtime_quote` | 120s | 2 分钟内 |
| `order_book` | 120s | 2 分钟内 |

### 依赖

- `mootdx>=0.8.0`（已加入 pyproject.toml）
- 国内 IP（TCP 连接通达信服务器）

### 使用规则

1. **必须通过 MootdxProvider 调用。** 不得在业务逻辑中直接调用 mootdx。
2. **lazy import。** mootdx 未安装时，整个 tradingagents 包不会 import 失败。
3. **mootdx 失败不能编造行情。** 必须返回 ProviderResult(status=failed)。
4. **没有实时价格时不能判断涨停、高价、止损止盈。**

### 限制和风险

- mootdx 依赖通达信服务器可用性
- 数据时间 `as_of_time` 可能需要后续进一步校验
- `order_book` 字段以实际 mootdx 返回为准（可能不含完整五档）
- 北交所支持情况需要后续确认
- smoke test 需要国内 IP 和手动 `--allow-network`
- 不提供估值、市值、涨跌停价，这些后续由腾讯 provider 补充
- 不提供公告层，这些后续由 cninfo provider 补充

### 测试

- mock 单元测试：`tests/test_cn_mootdx_provider.py`（34 个）
- smoke test：`scripts/smoke_test_mootdx_provider.py`（需手动 --allow-network）

---

## 二十一、Provider 并发抓取策略

**定位：** 控制数据抓取并发度，防止无控制并行请求导致 IP 被封或服务器压力过大。

### 核心原则

1. **数据抓取允许有限并行，但禁止无控制并行。**
2. **所有 provider 必须遵守 RateLimiter。**
3. **所有 provider 必须支持 max_concurrency 配置。**
4. **默认所有外部 provider 的 max_concurrency 应保守设置。**
5. **Cninfo / Eastmoney / Tencent 默认 max_concurrency = 1。**
6. **Mootdx 默认 max_concurrency = 1。**
7. **LocalHotlistProvider 属于本地文件读取，可以不走外部网络限流（max_concurrency = null）。**
8. **批量接口优先于多线程逐个 symbol 请求。**
9. **同一 provider 内不允许绕过 rate limiter 并发乱打。**
10. **跨 provider 可以未来由 orchestrator 做有限并行，但本阶段不实现真实 orchestrator。**
11. **并发失败不能静默成功。**
12. **任一 provider failed，必须回到 ProviderResult(status=failed) 或 partial。**
13. **抓取失败/过期必须进入 DataFreshnessGuard，不能跳过。**

### 配置字段

```yaml
concurrency:
  max_concurrency: 1      # 最大并发数，null 表示无限制
  batch_preferred: true   # 是否优先使用批量接口
  notes:                  # 备注
    - "说明1"
```

### 各 Provider 默认配置

| Provider | max_concurrency | batch_preferred | 说明 |
|----------|-----------------|-----------------|------|
| local_hotlist | null | false | 本地文件，无网络请求 |
| mootdx | 1 | true | 优先批量接口，避免高频调用 TDX |
| tencent | 1 | true | 端点未验证，保持串行 |
| cninfo | 1 | false | 公告查询必须保守 |
| eastmoney | 1 | true | 严格限流，不允许无控制并行 |
| ths | 1 | false | 默认保守 |

### 未来 Orchestrator 约束

未来实现 provider orchestration 时必须遵守：

1. **跨 provider 并行**：可以有限并行，但每个 provider 内部必须遵守 max_concurrency。
2. **同 provider 并行**：必须遵守 max_concurrency，使用 bounded semaphore 控制。
3. **批量抓取**：必须优先使用 provider batch 能力，减少请求次数。
4. **失败处理**：并行抓取结果必须保持 ProviderResult 可审计，不能静默成功。
5. **DataFreshnessGuard**：所有抓取结果必须经过 DataFreshnessGuard，不能跳过。

---

**文档结束。**

> 本文档由 opencode 于 2026-05-31 创建。
