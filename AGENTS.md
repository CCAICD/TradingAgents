# AGENTS.md — Coding Agent 必读指南

> **任何 coding agent（opencode、Claude Code、Codex 等）进入本项目时，必须首先完整阅读本文档和 PROJECT_HANDOFF.md，然后才能开始任何操作。**

---

## 一、项目一句话定位

本项目是一个以 A 股为主，兼容美股和加密货币的多市场 Agent 辅助决策系统。
它不自动交易，不连接券商，不执行下单，不预测明天涨跌。
它通过热榜、行情、板块、资金、情绪、趋势结构、新闻风险、基本面排雷、持仓状态和反思记忆，辅助用户做投资/交易决策。

---

## 二、三方协作模式

> **用户在 ChatGPT 和 opencode 之间扮演中间传话人。ChatGPT 是项目架构师和任务指挥者，opencode 是代码执行者和项目维护者。**

### 用户

- 是主要功能决策人
- 是 ChatGPT 和 opencode 之间的中间传话人
- 负责把 ChatGPT 的指令转发给 opencode
- 负责把 opencode 的结果、报错、疑问反馈给 ChatGPT
- 负责提供手动热榜、持仓、人工判断等信息

### ChatGPT

- 是项目架构师和任务指挥者
- 负责需求整合、架构设计、任务拆解、指令编写、结果审查和下一步规划

### opencode / coding agent

- 是代码执行者和项目维护者
- 必须先读 PROJECT_HANDOFF.md 和 AGENTS.md
- 必须按 ChatGPT 指令执行
- 不得擅自扩大需求
- 不得擅自实现未明确要求的功能
- 每次重大改动后必须更新 PROJECT_HANDOFF.md

---

## 三、必读文件顺序

每次进入项目时，应按以下顺序阅读：

1. `PROJECT_HANDOFF.md` — 项目交接文档，包含完整的目标、原则、规划、状态、待确认问题
2. `AGENTS.md`（本文件） — coding agent 行为规范
3. `PROJECT_BRIEF.md` — 项目简要说明
4. `REPORTS.md` — 报告体系定义
5. `MEMORY_AND_REFLECTION.md` — 记忆和反思系统定义
6. `DATA_SOURCES.md` — 数据源规划（如果存在）
7. 相关 `docs/` 下的专题文档（如果存在）

---

## 四、当前阶段

当前处于 **Phase 4D：Cninfo 巨潮公告 Provider 骨架（已完成）**。

### 已完成

- PROJECT_HANDOFF.md 第一版已创建并更新
- AGENTS.md 已创建
- PROJECT_BRIEF.md 已创建
- REPORTS.md 已创建
- MEMORY_AND_REFLECTION.md 已创建
- DATA_SOURCES.md 已创建
- 本地目录结构已创建
- **路径本地化完成**：默认路径已从用户 home 目录改为项目本地 `.tradingagents/`
- 支持 `TRADINGAGENTS_PROJECT_ROOT` 环境变量
- **手动热榜和 Attention Pool 初版实现**（Phase 2-2.6）
- **Data Freshness Guard 骨架**（Phase 3A）
- **a-stock-data 上游更新检查机制**（Phase 3A.5）
- **Market-Wide Scan 数据结构骨架**（Phase 3B）
- **Theme Detection 数据结构骨架**（Phase 3C）
- **Candidate Selection 数据结构骨架**（Phase 3D）
- **Provider 基础设施**（Phase 4A）：ProviderResult/BaseCnStockProvider/RawPayloadStore/RateLimiter/ProviderRegistry/LocalHotlistProvider/freshness 转换
- **mootdx 行情 Provider v0.1**（Phase 4B）：MootdxProvider 支持 daily_kline/minute_kline/index_kline/realtime_quote/order_book；lazy import；mootdx 未安装时优雅失败；34 个 mock 测试通过
- **Tencent Provider 骨架**（Phase 4C）：TencentProvider 支持 valuation/market_cap/turnover_rate/limit_price；返回 not_implemented；15 个 mock 测试通过
- **Cninfo Provider 骨架**（Phase 4D）：CninfoProvider 支持 announcement；返回 not_implemented；公告失败时提及"无重大利空"影响；16 个 mock 测试通过

### 尚未实现

- akshare 板块/新闻/涨停/财联社接入
- Market Regime Agent
- Theme Agent
- Leader Agent
- Structure Agent
- A 股尾盘报告
- A 股盘后报告
- 次日反思报告
- 周/月/季/年反思
- 持仓资金模块
- 多市场 market profile 架构

---

## 五、不可破坏原则

以下原则是项目的根基，**任何改动都不能违反**：

1. **不自动交易。** 本项目不是自动交易系统。
2. **不连接券商。** 任何券商 API 都不接入。
3. **不执行下单。** 所有交易决策由用户手动执行。
4. **不输出无条件买入/卖出。** 输出应以"观察、等待、回避、风险升高、结构确认、持仓处理建议"为主。
5. **不编造数据。** 系统绝对不能编造行情、成交额、涨跌幅、涨停状态、主线强度、止损位、止盈位。
6. **数据过期必须先更新。** 如果自动更新失败，必须如实说明。
7. **更新失败必须如实说明。** 不能隐瞒数据源故障。
8. **A 股规则不能污染美股和加密货币。** A 股特有逻辑（涨跌停、T+1、连板、炸板率、主板过滤）必须放在 `cn_stock` 专属模块中。
9. **原项目美股和加密货币能力必须保留。**
10. **每个结论必须有证据。**
11. **反思经验不能因为一两次成功就升级为永久规则。** 必须经过多次、跨环境验证。
12. **PROJECT_HANDOFF.md 必须持续更新。** 每次重大改动都要更新。

---

## 六、开发行为规则

### 项目本地化路径

项目运行状态默认保存在项目根目录 `.tradingagents/` 下：
- `results_dir`：`.tradingagents/logs`
- `data_cache_dir`：`.tradingagents/cache`
- `memory_log_path`：`.tradingagents/memory/trading_memory.md`
- checkpoint：`.tradingagents/cache/checkpoints/<TICKER>.db`

**coding agent 不应把缓存、日志、raw 数据、checkpoint 提交到 git。** `.gitignore` 已配置忽略这些内容。

### 没有明确指令，不要做的事

- 不要大规模重构
- 不要改核心工作流
- 不要接入新数据源
- 不要删除原有功能
- 不要改变默认行为
- 不要把 A 股规则写入全局模块
- 不要创建未被明确要求的业务逻辑文件

### Provider 并发抓取相关原则

- **不得在 provider 外部自行开线程/async 批量请求**
- **不得绕过 RateLimiter**
- **不得绕过 max_concurrency**
- **不得对 Eastmoney/Cninfo/Tencent 做无控制并发**
- **批量抓取必须优先使用 provider batch 能力**
- **并发抓取结果必须保持 ProviderResult 可审计**
- **外部 provider 默认 max_concurrency=1**
- **未经确认不得提高并发**
- **抓取失败必须返回 ProviderResult(status=failed) 或 partial**
- **抓取结果必须经过 DataFreshnessGuard，不能跳过**

### Attention Pool 和热榜相关原则

- **不要把 Attention Pool 误写成"只包含主板股票"**
- **不要提前删除非主板股票**
- 非主板、涨停、高价股票仍可能是主线强度证据
- 报告层必须区分"市场最强标的"和"用户可参与平替"
- **平替不能硬凑，找不到就明确说明**
- **不要把 Attention Pool 写成唯一选股范围**
- **Attention Pool 是优先范围，不是封闭范围**
- **Market-Wide Scan 是主线识别的前置步骤**
- **池外标的只能通过高置信度例外机制提示**
- **不得把池外普通异动股当成常规推荐**
- **报告层必须区分 Attention Pool 内标的、可参与平替、池外高置信度提示**

### 公告层（Disclosure Layer）相关原则

- **不要把公告层当普通新闻层**
- **公告层属于风险控制和确定性事件检查**
- **不能在公告数据缺失时编造"无利空"**
- **不能因为热度高就绕过公告风险**
- **对 Level 3 公告风险必须强降权或一票否决**
- **mootdx F10 最新提示只能作为补充摘要，不能替代巨潮原始公告**

### Attention Pool 相关原则

- **Attention Pool 初版只做市场注意力聚合**
- **不要把 Attention Pool 结果直接当成买入建议**
- **不要在没有行情数据时判断涨停、高价、止损、止盈**
- **不要剔除非主板股票**
- **可以使用 stock-pool 的名称映射修复历史数据**
- **不得直接复制 stock-pool 旧业务逻辑**
- **修复数据必须保留 audit**
- **board_type 离线推断不能作为最终交易资格判断**
- **历史修复数据应作为增量合并，不能替代原有效数据**
- **Attention Pool audit 必须能解释输入记录数、去重数量、窗口日期和输出股票数**

### 数据新鲜度相关原则

- **任何正式报告前必须检查 DataFreshnessGuard**
- **不得绕过 fresh/stale/missing/failed 状态**
- **不得在公告层 failed 时写"无重大利空"**
- **不得在实时行情 stale 时输出尾盘强参与建议**

### 外部数据源更新相关原则

- **可以运行 check_a_stock_data_updates.py 检查上游变化**
- **不得自动合并上游代码**
- **不得未经确认更新 provider**
- **上游 SKILL.md / LICENSE / 关键端点变化必须提示用户和 ChatGPT**
- **外部源更新必须记录到 PROJECT_HANDOFF.md**

### Market-Wide Scan 相关原则

- **Market-Wide Scan 不能跳过 Data Freshness Guard**
- **Market-Wide Scan 输出不是买卖建议**
- **不得把样例数据当真实市场数据**
- **不得在没有真实行情数据时生成市场强结论**

### Theme Detection 相关原则

- **Theme Detection 输出不是买卖建议**
- **不得把样例主题当真实主线**
- **不得在没有真实数据时输出 S/A/B/C 强判断**
- **池外高置信度只能作为单独提示机制，不能和常规候选混淆**
- **风险 evidence 不能被主题热度覆盖**

### Candidate Selection 相关原则

- **Candidate Selection 输出不是买卖建议**
- **不得使用 buy/sell 字段**
- **不得在没有价格数据时判断高价或涨停**
- **不得硬凑平替**
- **非主板强标的必须保留为主线证据，但可参与层要标记不可参与或需要平替**
- **风险 blocked 标的不能被热度或主题强度覆盖**

### 修改前后的要求

- 修改前先说明将影响哪些文件
- 修改后要说明改了什么、为什么改、是否需要更新文档
- 发现文档和代码不一致时，要提醒用户，并建议同步更新 PROJECT_HANDOFF.md

### 文档更新要求

每次重大改动后，必须检查以下文档是否需要更新：

- `PROJECT_HANDOFF.md` — 实现状态、项目结构、待确认问题
- `AGENTS.md` — 当前阶段、行为规则
- `PROJECT_BRIEF.md` — 项目背景和目标
- `REPORTS.md` — 报告格式
- `MEMORY_AND_REFLECTION.md` — 记忆和反思规则
- `DATA_SOURCES.md` — 数据源状态

### 遗留项目相关规则

- **读取旧项目时必须只读扫描，不得修改旧项目文件**
- 旧项目数据可以审计和迁移
- 旧项目代码只能参考，不能未经确认直接复制
- 旧项目规则不能默认继承，必须与 PROJECT_HANDOFF.md 当前原则对齐
- **legacy_import 是历史迁移区，不等于正式每日录入区**
- **使用 legacy 数据时必须标记 source_project**
- **旧数据不能覆盖新数据**
- **stock-pool 暂时仅作为参考资源，不得擅自把旧代码复制进当前项目**

### 外部数据源相关规则

- **可以参考 a-stock-data（https://github.com/simonlin1212/a-stock-data）**
- **不得未经确认直接复制大段代码**
- **复用代码必须保留来源和许可证说明（Apache-2.0）**
- **不得让 Agent 直接依赖 SKILL.md 作为运行时数据源**
- **必须通过本项目 provider adapter 和统一 schema 接入**

---

**文档结束。**

> 本文档由 opencode 于 2026-05-31 创建。
> 下次更新时机：Phase 2 开始时，或项目状态发生重大变化时。
