# PROJECT_HANDOFF.md — 项目交接文档

> **本文档是项目唯一权威交接文件。**
> ChatGPT、opencode 以及任何后续 AI 助手在接手本项目时，**必须首先完整阅读本文档**，然后才能开始任何操作。
> 本文档由 opencode 负责维护，每次重大变更后必须同步更新。

---

## 一、项目定位与目标

### 1.1 项目名称

TradingAgents-AStock（基于 TradingAgents v0.2.5 魔改）

### 1.2 项目正在做什么

本项目是对开源项目 [TradingAgents](https://github.com/TauricResearch/TradingAgents)（一个多 Agent LLM 金融交易框架）的深度改造。

**原项目定位：** 多 Agent 协作的自动交易框架，面向美股，最终输出买入/卖出/持有的交易决策，连接模拟交易所执行下单。

**本项目定位：** 以 A 股为主，兼容美股和加密货币的**多市场 Agent 辅助决策系统**。

**核心区别：本项目不自动交易，不连接券商，不执行下单，不预测明天涨跌。**

### 1.3 为什么要魔改 TradingAgents

用户需要的不是"替我交易"的机器人，而是一个能帮助他：
- 识别当前市场环境
- 识别当前强主线
- 找到每条主线的核心标的
- 判断趋势结构位置
- 给出止损位和止盈/减仓位
- 判断是否适合开仓、加仓、减仓、观察或空仓
- 通过反思系统长期修正经验

的**辅助决策工具**。

原项目无法满足这些需求，因为：
1. 原项目面向美股，没有 A 股的涨跌停、T+1、连板、炸板率等规则
2. 原项目是自动交易系统，输出"买入/卖出"指令，而非"观察/等待/回避"等辅助建议
3. 原项目没有热榜、主线、龙头、平替标的等 A 股特有的选股逻辑
4. 原项目没有反思记忆分层系统（观察→假设→验证规则→失效经验）
5. 原项目的数据源（yfinance、Alpha Vantage）对 A 股支持不完善

### 1.4 用户的目标

用户的核心目标是建立一个**长期可进化的 A 股辅助决策系统**，能够：
1. 每天盘后自动处理热榜数据，形成 Attention Pool
2. 生成尾盘辅助决策报告、盘后复盘报告、次日观察计划
3. 通过反思系统不断修正判断规则
4. 最终形成一套适合用户个人风格的、有证据支撑的决策辅助体系

---

## 二、三方角色分工

### 2.1 核心关系

> **用户在 ChatGPT 和 opencode 之间扮演中间传话人。ChatGPT 是项目架构师和任务指挥者，opencode 是代码执行者和项目维护者。**

### 2.2 角色详细说明

| 角色 | 身份 | 职责 |
|------|------|------|
| **用户** | 中间传话人、主要功能决策者 | 1. 把 ChatGPT 的指令转发给 opencode<br>2. 把 opencode 的回复、报错和疑问发回给 ChatGPT<br>3. 对功能方向做最终决策<br>4. 提供手工数据（如热榜文字） |
| **ChatGPT** | 项目架构师、任务指挥者 | 1. 做项目架构设计<br>2. 需求整合和任务拆解<br>3. 编写详细指令给 opencode<br>4. 审查 opencode 的执行结果<br>5. 规划下一步行动 |
| **opencode** | 代码执行者、项目维护者 | 1. 读取 ChatGPT 通过用户转发的指令<br>2. 修改代码、创建文件、更新文档<br>3. 汇报执行结果、遇到的问题和不确定项<br>4. 维护 PROJECT_HANDOFF.md 的实时性 |

### 2.3 工作流程

```
ChatGPT → [指令] → 用户 → [转发] → opencode → [执行] → 结果 → 用户 → [转发] → ChatGPT → [审查+下一步指令]
```

### 2.4 重要约定

- opencode **不得自行决定**产品方向或架构变更，必须通过用户向 ChatGPT 确认
- opencode **必须主动汇报**执行中遇到的所有不确定项
- opencode **必须在每次执行后**检查 PROJECT_HANDOFF.md 是否需要更新
- ChatGPT 的指令如果和 PROJECT_HANDOFF.md 中的原则冲突，opencode 应提出疑问

---

## 三、当前项目结构初步观察

以下为 opencode 扫描到的当前项目目录结构（截至 2026-05-31）：

```
C:\github\TradingAgents\
├─ .dockerignore
├─ .env.enterprise.example
├─ .env.example
├─ .git/
├─ .gitignore
├─ assets/                          # 原项目图片资源
├─ CHANGELOG.md                     # 原项目变更日志
├─ cli/                             # CLI 交互界面
│  ├─ __init__.py
│  ├─ announcements.py
│  ├─ config.py
│  ├─ main.py                       # CLI 入口
│  ├─ models.py
│  ├─ stats_handler.py
│  └─ utils.py
├─ docker-compose.yml
├─ Dockerfile
├─ LICENSE
├─ main.py                          # Python API 入口示例
├─ pyproject.toml                   # 项目构建配置（v0.2.5）
├─ README.md                        # 原项目 README
├─ requirements.txt
├─ scripts/
│  └─ smoke_structured_output.py
├─ test.py
├─ tests/                           # 测试文件
│  ├─ conftest.py
│  ├─ test_*.py                     # 多个测试文件
│  └─ __init__.py
├─ tradingagents/                   # 核心代码
│  ├─ __init__.py
│  ├─ agents/                       # Agent 定义
│  │  ├─ __init__.py
│  │  ├─ analysts/                  # 分析师 Agent
│  │  │  ├─ fundamentals_analyst.py
│  │  │  ├─ market_analyst.py
│  │  │  ├─ news_analyst.py
│  │  │  ├─ sentiment_analyst.py
│  │  │  └─ social_media_analyst.py
│  │  ├─ managers/                  # 管理者 Agent
│  │  │  ├─ portfolio_manager.py
│  │  │  └─ research_manager.py
│  │  ├─ researchers/               # 研究员 Agent
│  │  │  ├─ bear_researcher.py
│  │  │  └─ bull_researcher.py
│  │  ├─ risk_mgmt/                 # 风险管理 Agent
│  │  │  ├─ aggressive_debator.py
│  │  │  ├─ conservative_debator.py
│  │  │  └─ neutral_debator.py
│  │  ├─ schemas.py                 # Pydantic 结构化输出 Schema
│  │  ├─ trader/                    # 交易员 Agent
│  │  │  └─ trader.py
│  │  └─ utils/                     # Agent 工具和工具函数
│  │     ├─ agent_states.py         # Agent 状态定义
│  │     ├─ agent_utils.py          # Agent 工具函数
│  │     ├─ core_stock_tools.py     # 核心股票数据工具
│  │     ├─ fundamental_data_tools.py
│  │     ├─ market_data_validation_tools.py
│  │     ├─ memory.py               # 决策日志记忆系统
│  │     ├─ news_data_tools.py
│  │     ├─ rating.py               # 评级解析
│  │     ├─ structured.py
│  │     └─ technical_indicators_tools.py
│  ├─ dataflows/                    # 数据流
│  │  ├─ __init__.py
│  │  ├─ alpha_vantage*.py          # Alpha Vantage 数据源
│  │  ├─ config.py
│  │  ├─ interface.py               # 数据路由接口
│  │  ├─ market_data_validator.py
│  │  ├─ reddit.py
│  │  ├─ stockstats_utils.py
│  │  ├─ stocktwits.py
│  │  ├─ utils.py
│  │  ├─ y_finance.py               # Yahoo Finance 数据源
│  │  └─ yfinance_news.py
│  ├─ default_config.py             # 默认配置
│  └─ graph/                        # LangGraph 编排
│     ├─ __init__.py
│     ├─ analyst_execution.py
│     ├─ checkpointer.py
│     ├─ conditional_logic.py
│     ├─ propagation.py
│     ├─ reflection.py              # 反思系统（基础版）
│     ├─ setup.py
│     ├─ signal_processing.py
│     └─ trading_graph.py           # 主入口类 TradingAgentsGraph
└─ uv.lock
```

### 3.1 关键发现

1. **原项目是完整的多 Agent 框架**，基于 LangGraph 编排，包含分析师→研究员→交易员→风险管理→投资组合经理的完整流程
2. **数据源以美股为主**：yfinance、Alpha Vantage、StockTwits、Reddit
3. **已有基础反思系统**：`memory.py` 实现了决策日志，`reflection.py` 实现了基础反思
4. **已有结构化输出**：`schemas.py` 定义了 PortfolioRating（5级）、TraderAction（3级）、SentimentBand（6级）等
5. **没有 A 股专属模块**：没有任何 `cn_stock`、`markets/` 目录
6. **没有热榜系统**：没有 `manual_hotlists`、`Attention Pool` 相关代码
7. **没有主线/龙头识别**：没有 `Theme Agent`、`Leader Agent` 等
8. **没有市场环境分类**：没有 A 股特有的市场环境状态机
9. **持仓/资金模块未实现**：没有 `portfolio/` 目录和持仓录入功能

---

## 四、产品方向（已确定）

### 4.1 最终定位

以 A 股为主，兼容美股和加密货币的多市场 Agent 辅助决策系统。

### 4.2 核心功能

1. **热榜解析与 Attention Pool 生成**：从同花顺、东方财富、雪球、通达信四个平台的热榜文字中解析出结构化数据，形成 20 交易日滚动热度的候选池
2. **市场环境识别**：判断当前是强势增量、结构性活跃、存量轮动、缩量弱势、退潮杀跌还是冰点修复
3. **主线识别与分级**：识别 S/A/B/C 级主线，判断持续性和退潮风险
4. **龙头与核心股识别**：每条主线的第一核心、龙头、趋势中军、弹性标的、平替标的
5. **趋势结构分析**：平台整理、放量突破、突破后回踩、趋势主升、第一次分歧、高位加速、结构破坏
6. **负面事件排雷**：确定性利空、公告风险、监管风险、减持、解禁、退市风险的一票否决
7. **基本面底线排雷**：不做深度估值，只做底线排雷
8. **决策报告生成**：尾盘辅助决策报告、盘后复盘报告、次日观察计划
9. **反思与进化**：次日/周/月/季/年反思，四层记忆分层

### 4.3 不做的事

- ❌ 不自动交易
- ❌ 不连接券商接口
- ❌ 不执行自动下单
- ❌ 不输出无条件买入/卖出指令
- ❌ 不预测明天涨跌
- ❌ 不做深度估值
- ❌ 不做指标金叉死叉交易

### 4.4 输出原则

输出应以"观察、等待、回避、风险升高、结构确认、持仓处理建议"为主。

---

## 五、A 股核心交易思想

### 5.1 系统不是什么

- ❌ 预测市场
- ❌ 抄底摸顶
- ❌ 指标金叉死叉交易
- ❌ 自动荐股下单系统

### 5.2 系统是什么

- ✅ 跟随市场主线
- ✅ 找核心股票
- ✅ 等趋势启动或第一次分歧
- ✅ 做主升波段
- ✅ 用反思系统不断修正经验

### 5.3 核心原则

1. 只做主线
2. 只做核心
3. 只做趋势
4. 不预测，只跟随
5. 成交量和资金行为优先于传统指标

### 5.4 系统核心公式

```
资金和趋势决定是否进入候选；
主线和龙头决定优先级；
结构决定参与位置；
利空和基本面风险决定是否否决；
持仓和市场环境决定仓位；
反思系统决定长期进化。
```

---

## 六、A 股系统分析流程

### 6.0 正式分析流程

```
Market-Wide Scan → Theme Detection → Attention Pool Matching → Candidate Selection → Out-of-Pool High Conviction Alert → Report
```

中文解释：

```
全市场扫描 → 主线识别 → Attention Pool 匹配 → 候选标的选择 → 池外高置信度提示 → 报告输出
```

### 6.0.1 全市场扫描层（Market-Wide Scan）

全市场扫描是整个分析流程的前置步骤，用于判断：

- 市场环境
- 风格状态
- 强主线
- 新主线
- 板块扩散
- 资金流向
- 情绪周期
- 涨停和亏钱效应

未来应扫描的数据包括：

- 指数
- 全市场涨跌家数
- 两市成交额
- 涨停池
- 跌停池
- 炸板率
- 连板高度
- 板块涨幅
- 板块成交额
- 板块涨停数量
- 个股成交额排名
- 个股涨幅排名
- 换手率
- 强势股表现

### 6.0.2 Attention Pool 定位

- **Attention Pool 是市场注意力池，不是唯一选股范围**
- 后续分析"优先"从 Attention Pool 中找标的，但不是"只能"从 Attention Pool 中找
- 票池用于提高稳定性、可追踪性和反思质量
- 但不能因为票池中没有，就忽略新主线启动

### 6.0.3 池外高置信度提示（Out-of-Pool High Conviction Alert）

**定义：**

当新主线刚启动或市场风格快速切换时，如果 Attention Pool 中没有合适标的，但全市场中出现非常强且证据充分的标的，系统可以单独提示用户。

**但必须强调：**

- 这是例外机制，不是常规推荐
- 不能把普通异动股随便放进来
- 必须明确标记"未进入 Attention Pool，需后续验证持续性"
- 不能因为池外票很强就绕过数据新鲜度、风险排雷和可参与性检查

**池外标的触发条件（初版规则）：**

池外标的至少需要具备多项证据，例如：

- 所属主题/板块当日明显强于市场
- 板块内出现多个涨停或多只大涨股票
- 个股成交额显著放大
- 个股是该新主线中最早启动或最有辨识度的标的之一
- 个股强于板块，也强于指数
- 个股处在有效结构位置，而不是纯高位追涨
- 有明确资金进场迹象
- 没有重大利空、ST、退市、停牌等硬风险
- 如果非主板、涨停或股价 > 120 元，需要给出主板非涨停平替

**简要原则：**

池外标的必须同时有：主线证据 + 个股强度 + 资金证据 + 结构证据 + 风险不过线

### 6.0.4 报告输出分层

尾盘和盘后报告中的标的输出应分为：

- **A. Attention Pool 内优先标的**
- **B. 同主线可参与平替**
- **C. 池外高置信度新机会**

池外高置信度新机会必须单独列示，不能和 Attention Pool 内标的混在一起。

### 6.0.5 当前实现状态

- 该规则目前只是文档规划
- 尚未实现 Market-Wide Scan
- 尚未实现 Out-of-Pool High Conviction Alert
- 尚未实现全市场扫描数据接入

---

## 六A、A 股核心模块规划

### 6A.1 Attention Pool Agent

- 解析热榜文字
- 保存原始热榜
- 结构化热榜
- **记录所有热榜股票，不因板块类型剔除**
- 为每只股票标注：`board_type`、`tradability_flags`、`price_level`、`limit_status` 等字段
- 计算 20 交易日滚动热度
- 识别多平台共振
- 生成 candidate_pool（全市场注意力池）
- **Attention Pool 是优先范围，不是封闭范围**

### 6A.2 Market Regime Agent

- 判断市场环境（强势增量、结构性活跃、存量轮动、缩量弱势、退潮杀跌、冰点修复）
- 决定整体风险预算和策略适用性

### 6A.3 Theme Agent

- 识别市场主线
- 给主线分级：S 级、A 级、B 级、C 级
- 判断主线持续性、扩散程度和退潮风险

### 6A.4 Leader Agent

- 识别每条主线的第一核心、龙头、趋势中军、弹性标的、平替标的、掉队标的
- 区分"主线最强标的"和"可参与平替标的"
- **最强标的满足以下任一条件时必须给平替：**
  - 非主板
  - 涨停
  - 股价 > 120 元（高价阈值）
  - ST / *ST
  - 退市风险
  - 停牌
  - 流动性不足
  - 关键数据缺失
- **平替优先选择：** 同主线、主板、非涨停、股价 ≤ 120 元、成交额充足、趋势结构未破坏
- 如果找不到合格平替，必须明确写"暂无合格平替"，不能硬凑

### 6A.5 Structure Agent

- 判断平台整理、放量突破、突破后回踩、趋势主升、第一次分歧、高位加速、结构破坏
- 给出参与条件、失效条件、止损位、止盈/减仓位

### 6A.6 Negative Event Guard

- 识别确定性利空
- 识别公告风险、监管风险、减持、解禁、退市风险、ST 风险等
- **接入公告层（Disclosure Layer）作为核心输入**
- 对高风险标的执行强降权或一票否决

### 6A.6.1 公告层（Disclosure Layer）

**公告层定位：**

公告层不是普通新闻层。公告层的核心作用是：
1. 识别确定性利空
2. 识别重大公告催化
3. 识别监管、退市、ST、减持、解禁、业绩暴雷等硬风险
4. 在尾盘、盘后、次日计划、持仓建议前做风险排查
5. 对高风险标的执行强降权或一票否决

**公告层应接入或服务于：**
- Negative Event Guard
- Fundamental Risk Guard
- Decision Summary Agent
- 未来 Portfolio Agent

**公告风险分层：**

| Level | 名称 | 说明 | 处理方式 |
|-------|------|------|----------|
| Level 0 | 普通公告 | 董事会、监事会、普通经营公告、普通股东大会 | 正常处理 |
| Level 1 | 需要提示 | 权益分派、股权激励、定增、可转债、重大合同、业绩预告 | 提示关注 |
| Level 2 | 强风险提示 | 大额减持、解禁、业绩大幅下滑、诉讼仲裁、补充更正、澄清致歉、风险提示 | 强风险提示 |
| Level 3 | 强降权或一票否决 | 立案调查、监管处罚、财务造假、ST/*ST、特别处理和退市、退市整理期、债务违约、实控人或高管重大风险 | 强降权或一票否决 |

**当前实现状态：**
- 公告层已规划
- 尚未实现公告数据接入
- 尚未实现 Disclosure Guard

### 6A.7 Fundamental Risk Guard

- 不做深度估值
- 只做基本面底线排雷
- 识别业绩暴雷、财务异常、退市风险等

### 6A.8 Decision Summary Agent

- 生成尾盘报告、盘后报告、次日观察计划和风险提示
- **报告输出必须分层：** Attention Pool 内标的、可参与平替、池外高置信度新机会

### 6A.9 Reflection Agent

- 生成次日反思、周反思、月反思、季度反思、年度反思
- 将经验分为观察、假设、已验证规则、失效经验

---

## 七、报告体系规划

### 7.1 尾盘辅助决策报告

**目标：** 尾盘抓取最新数据，判断今天是否有适合参与的机会。

**内容必须包括：**
- 数据新鲜度检查
- 市场环境
- 风险等级
- 是否适合开新仓
- 建议总仓位区间
- 强主线排序
- **公告层风险检查：**
  - 对最佳标的、平替标的、池外高置信度标的都要检查公告风险
  - 如果公告层数据失败，不能声称"无重大利空"
  - 如果发现重大公告风险，必须降权或剔除
- **每条强主线必须输出：**
  - **A. Attention Pool 内优先标的**
  - **B. 同主线可参与平替**（如果最强标的不适合用户参与）
  - **C. 池外高置信度新机会**（单独列示，不能与常规候选混在一起）
- **当最强标的满足以下任一条件时必须给平替：**
  - 非主板
  - 涨停
  - 股价 > 120 元
  - ST / *ST
  - 退市风险
  - 停牌
  - 流动性不足
  - 关键数据缺失
- **平替优先选择：** 同主线、主板、非涨停、股价 ≤ 120 元、成交额充足、趋势结构未破坏
- **如果找不到合格平替，必须明确说明原因，不得硬凑**
- 每个标的的入选理由、结构位置、参与条件、止损位、止盈/减仓位、风险点
- 最终建议：可参与、只观察、不开仓、等待分歧、等待回踩等

**池外高置信度新机会必须包含：**
- 股票
- 所属主线
- 为什么没有在 Attention Pool 中
- 为什么仍然值得提示
- 证据列表
- 是否可参与
- 是否需要平替
- 后续观察条件
- 风险点

### 7.2 盘后复盘报告

**目标：** 收盘后抓取当日全量数据，总结市场并给出次日观察计划。

**内容必须包括：**
- 数据新鲜度检查
- 指数表现
- 两市成交额
- 上涨/下跌家数
- 涨停/跌停数量
- 炸板率
- 连板高度
- 情绪阶段
- 今日主线复盘
- 今日核心股复盘
- Attention Pool 更新
- **今日重大公告汇总**
- **重点候选股公告风险**
- **晚间公告二次检查建议**
- **新启动主线观察**
- **池外高置信度标的回顾**
- **是否应加入后续观察**
- **是否需要等待进入 Attention Pool 后再提高权重**
- 次日观察计划
- 仓位建议
- 风险预案

### 7.3 次日反思报告

**目标：** 验证前一个交易日盘后报告是否正确。

**内容必须包括：**
- 昨日主线判断是否正确
- 昨日核心股判断是否正确
- 昨日平替标的是否有效
- 昨日风险提示是否发生
- **昨日是否漏掉公告风险**
- **公告风险是否影响主线或核心股判断**
- **是否需要调整 Negative Event Guard 规则**
- 观察条件是否触发
- 错误归因
- 经验沉淀
- 是否更新策略库

### 7.4 周/月/季/年反思报告

**目标：** 让系统长期进化，避免短期过拟合。

**内容必须包括：**
- 哪些规则有效
- 哪些规则失效
- 哪些主线识别正确
- 哪些龙头识别错误
- 哪些市场环境下策略有效
- 是否存在短期偶然现象
- 是否需要将某些假设升级为规则
- 是否需要将某些规则降权或标记失效

---

## 八、反思记忆系统

### 8.1 四层记忆架构

| 层级 | 名称 | 说明 |
|------|------|------|
| L1 | Observation Memory（观察记忆） | 只记录现象，不直接形成规则 |
| L2 | Hypothesis Memory（假设记忆） | 短期似乎有效，但需要验证 |
| L3 | Validated Rule Memory（已验证规则） | 经过多次、跨环境验证后才能进入 |
| L4 | Deprecated Memory（失效经验） | 曾经有效但最近大量反例，需要标记过期，不能直接删除 |

### 8.2 核心原则

- 反思经验不能因为一两次成功就直接变成永久规则
- 必须经过多次、跨市场环境的验证才能升级为规则
- 失效经验不能删除，必须标记过期，供后续参考

---

## 九、市场环境与策略库

### 9.1 市场环境分类

| 环境 | 说明 |
|------|------|
| 强势增量市场 | 成交额放大，多数股票上涨，主线明确 |
| 结构性活跃市场 | 部分板块活跃，部分板块弱势，需要精选 |
| 存量轮动市场 | 成交额不变，板块快速轮动，追高容易亏损 |
| 缩量弱势市场 | 成交额缩小，多数股票下跌，需要防守 |
| 退潮杀跌市场 | 主线退潮，强势股补跌，需要空仓 |
| 冰点修复市场 | 极度弱势后的修复，需要谨慎观察 |

### 9.2 策略库

| 策略 | 适用环境 | 说明 |
|------|----------|------|
| 主线核心平台突破 | 强势增量、结构性活跃 | 等平台突破确认后参与 |
| 第一次分歧低吸 | 强势增量、结构性活跃 | 主线核心股第一次分歧时低吸 |
| 趋势中军回踩 | 强势增量、结构性活跃 | 趋势中军回踩支撑位时参与 |
| 冰点修复观察 | 冰点修复 | 观察修复力度，不急于参与 |
| 防守空仓 | 缩量弱势、退潮杀跌 | 空仓等待 |

### 9.3 核心原则

- 系统必须先判断市场环境，再选择策略
- 不要在所有市场环境中使用同一套策略

---

## 十、持仓资金模块规划

### 10.1 第一阶段（暂不实现，预留接口）

后续用户会手动录入：
- 总资产
- 现金
- 持仓股票
- 持仓成本
- 持仓数量
- 当前盈亏
- 当前仓位
- 计划最大仓位
- 单票最大仓位
- 最大可接受回撤

### 10.2 系统未来输出

- 继续持有
- 减仓
- 止盈
- 止损
- 不加仓
- 等回踩加仓
- 结构破坏退出
- 主题暴露过高，不建议加同方向
- 账户回撤中，降低试错仓位

### 10.3 重要原则

- 好股票不等于适合现在买
- 好主线不等于适合继续加仓
- 已有持仓建议必须和新标的观察建议分开

---

## 十一、多市场规划

### 11.1 市场划分

| 市场标识 | 说明 |
|----------|------|
| `cn_stock` | A 股（第一优先级） |
| `us_stock` | 美股 |
| `crypto` | 加密货币 |

### 11.2 目录规划

```
tradingagents/
├─ markets/
│  ├─ common/           # 通用能力
│  ├─ cn_stock/         # A 股专属能力
│  ├─ us_stock/         # 美股专属能力
│  └─ crypto/           # 加密货币专属能力
├─ dataflows/
├─ agents/
└─ graph/
```

### 11.3 核心原则

- **禁止**把 A 股涨跌停、T+1、连板、炸板率、主板过滤等逻辑写入全局模块
- A 股规则必须放在 `markets/cn_stock/` 中
- 美股和加密货币能力保留原项目能力，轻量扩展

---

## 十二、用户 A 股选股思路

### 12.1 热榜数据来源

用户每天盘后手动抄取四个平台热门股排名前 20：
- 同花顺
- 东方财富
- 雪球
- 通达信

### 12.2 数据处理要求

1. 每个平台前 20 必须完整保存
2. 用户只负责把文字发给 Agent
3. 系统负责保存原始文字并解析成结构化数据
4. **所有热榜股票全部保留，不因板块类型提前剔除**
5. 创业板、科创板、北交所、主板股票均进入原始热榜和 Attention Pool
6. Attention Pool 是"市场注意力池"，不等于"用户可买池"
7. 只保留近 20 个交易日，滚动更新
8. 后续优先在 Attention Pool 中筛选标的，但不是唯一范围

### 12.3 推荐数据保存结构

```
data/
├─ manual_hotlists/
│  ├─ raw_text/
│  │  └─ YYYY-MM-DD.md          # 原始热榜文字
│  ├─ structured/
│  │  └─ YYYY-MM-DD.yaml        # 结构化热榜数据
│  └─ events/
│     └─ hotlist_events.jsonl    # 热榜事件日志
```

---

## 十三、推荐长期目录结构

```
TradingAgents-AStock/
├─ PROJECT_HANDOFF.md              # 本文档
├─ AGENTS.md                       # Agent 技能和行为指南
├─ PROJECT_BRIEF.md                # 项目简要说明
├─ MARKETS.md                      # 多市场配置说明
├─ DATA_SOURCES.md                 # 数据源清单和配置
├─ MEMORY_AND_REFLECTION.md        # 反思记忆系统说明
├─ REPORTS.md                      # 报告体系说明
├─ docs/
│  ├─ CN_STOCK_SYSTEM.md           # A 股系统详细设计
│  ├─ US_STOCK_SYSTEM.md           # 美股系统详细设计
│  ├─ CRYPTO_SYSTEM.md             # 加密货币系统详细设计
│  ├─ A_STOCK_RULES.md             # A 股交易规则
│  ├─ REPORT_TEMPLATES.md          # 报告模板
│  ├─ REFLECTION_SYSTEM.md         # 反思系统设计
│  └─ DEVELOPMENT_PLAN.md          # 开发计划
├─ data/
│  ├─ manual_hotlists/
│  │  ├─ raw_text/
│  │  ├─ structured/
│  │  └─ events/
│  ├─ market_data/
│  ├─ news/
│  ├─ reports/
│  └─ portfolio/
├─ .tradingagents/
│  ├─ cache/
│  ├─ memory/
│  ├─ logs/
│  ├─ reports/
│  └─ raw/
└─ tradingagents/
   ├─ markets/
   │  ├─ common/
   │  ├─ cn_stock/
   │  ├─ us_stock/
   │  └─ crypto/
   ├─ dataflows/
   ├─ agents/
   └─ graph/
```

---

## 十四、阶段规划与实现状态

> **重要提醒：截至 2026-05-31，本项目仅完成了交接文档第一版的创建。除 PROJECT_HANDOFF.md 外，绝大部分规划中的功能均未实现。原项目已有能力虽然存在，但尚未针对本项目的目标进行适配和测试。**

### Phase 0：交接文档和项目原则

| 任务 | 状态 |
|------|------|
| 创建 PROJECT_HANDOFF.md | ✅ 已实现 |
| 明确项目目标、角色、功能、边界、后续计划 | ✅ 已实现 |
| 明确每次重大变更必须更新文档 | ✅ 已实现 |

### Phase 1：项目本地化和基础文档

| 任务 | 状态 |
|------|------|
| 建立 AGENTS.md | ✅ 已实现 |
| 建立 PROJECT_BRIEF.md | ✅ 已实现 |
| 建立 REPORTS.md | ✅ 已实现 |
| 建立 MEMORY_AND_REFLECTION.md | ✅ 已实现 |
| 建立 DATA_SOURCES.md | ✅ 已实现 |
| 创建本地目录结构（.tradingagents/、data/、docs/） | ✅ 已实现 |
| 确认 memory/cache/logs/reports/raw 全部项目本地化 | ✅ 已实现（Phase 1.5 完成） |

### Phase 1.5：项目本地化路径改造

| 任务 | 状态 |
|------|------|
| 修改 default_config.py 使用项目本地路径 | ✅ 已实现 |
| 支持 TRADINGAGENTS_PROJECT_ROOT 环境变量 | ✅ 已实现 |
| 创建 .tradingagents/cache/checkpoints/ 目录 | ✅ 已实现 |
| 修复 .gitignore 允许 .gitkeep 跟踪 | ✅ 已实现 |
| 更新 .env.example 包含路径配置 | ✅ 已实现 |
| 验证环境变量覆盖能力 | ✅ 已实现 |

### Phase 1.8：遗留项目资产审计

| 任务 | 状态 |
|------|------|
| 扫描 tradingagents-old 目录 | ✅ 已完成 |
| 扫描 stock-pool 目录 | ✅ 已完成 |
| 创建 docs/legacy_audit/LEGACY_ASSET_INVENTORY.md | ✅ 已完成 |
| 创建 docs/legacy_audit/LEGACY_MIGRATION_PLAN.md | ✅ 已完成 |
| 创建 legacy_import 相关目录 | ✅ 已完成 |
| 正式迁移历史热榜数据 | ✅ 已完成（Phase 1.9） |

**遗留项目路径：**
- `C:\github\tradingagents-old` — 用户之前魔改的 tradingagents 项目
- `C:\github\stock-pool` — 独立的股票池管理系统

**可迁移数据：**
- 热榜 JSONL 数据：19 个交易日（2025-05-27 到 2026-05-28）
- 票池 active.json：100+ 只股票的滚动聚合数据
- 股票名称映射：3315 个股票名称
- 报告样例：8 个盘后观察报告
- 规则文档：A 股交易规则等

**重要说明：**
- 旧项目热榜数据可以复用
- 旧项目代码只能参考
- 旧项目规则必须重新审查
- 不能直接把旧项目混乱逻辑带入新项目

### Phase 1.9：历史热榜数据迁移

| 任务 | 状态 |
|------|------|
| 迁移 tradingagents-old 热榜 JSONL 数据 | ✅ 已完成 |
| 创建迁移脚本 | ✅ 已完成 |
| 生成审计报告 | ✅ 已完成 |
| stock-pool 暂不迁移，仅作为参考资源 | ✅ 已确认 |

**迁移结果：**
- 迁移文件数量：19 个 JSONL 文件
- 覆盖日期范围：2026-04-22 到 2026-05-28
- 覆盖交易日数量：16 天（另有 3 天数据因 name 字段缺失进入无效记录）
- 总记录数：693
- 有效记录数：449
- 无效记录数：244（主要是 name 字段为空）
- 四平台覆盖：同花顺、东方财富、雪球、通达信
- 非主板股票保留：23 条

**迁移输出路径：**
- `data/manual_hotlists/legacy_import/raw/tradingagents-old/` — 原始文件副本
- `data/manual_hotlists/legacy_import/structured/tradingagents-old/` — 标准化 JSONL
- `data/manual_hotlists/legacy_import/audit/` — 审计报告和无效记录

### Phase 1.11：a-stock-data 外部数据工具包审计

| 任务 | 状态 |
|------|------|
| 审计 a-stock-data 仓库 | ✅ 已完成 |
| 创建 docs/external_sources/A_STOCK_DATA_AUDIT.md | ✅ 已完成 |
| 评估是否作为本项目 A 股数据层参考实现 | ✅ 已完成 |

**审计仓库：** https://github.com/simonlin1212/a-stock-data

**审计结论：**
- **许可证：** Apache-2.0，可以自由使用，需要保留 attribution
- **项目形态：** Skill.md + 内嵌 Python 代码（非传统 Python 包），不能直接 import
- **数据覆盖：** 7 层架构、27 端点、13 数据源
- **推荐方式：** 抽取稳定函数为 provider adapter，不直接整包硬拷
- **数据源优先级：** mootdx/腾讯优先（不封 IP），东财仅用于独有数据
- **东财限流：** 有统一 em_get() 限流机制，可以参考
- **已移除 akshare：** V3.0 彻底移除 akshare 依赖，改为直连 HTTP API
- **财联社快讯已下线：** 使用东财全球资讯替代

**MVP 第一批推荐接入端点：**
- mootdx 行情（K 线、五档盘口、实时价格）
- 腾讯财经（PE/PB/市值/换手率/涨跌停价）
- 巨潮 cninfo（公告数据）
- mootdx F10（基本面数据、最新提示）

**详细审计报告：** `docs/external_sources/A_STOCK_DATA_AUDIT.md`

### Phase 2：手动热榜和 Attention Pool

| 任务 | 状态 |
|------|------|
| 支持用户输入热榜文字 | ✅ 已实现 |
| 保存原始文本 | ✅ 已实现 |
| 解析为结构化数据 | ✅ 已实现 |
| 生成 20 交易日滚动 Attention Pool | ✅ 已实现 |
| 全量热榜股票录入，不因板块剔除 | ✅ 已实现 |
| 为每只股票标注 board_type 等字段 | ✅ 已实现 |
| 接入 legacy_import 历史数据 | ✅ 已实现 |
| 接入实时行情 | ❌ 未实现（不在本轮范围） |
| 判断涨停、高价、止损、止盈 | ❌ 未实现（不在本轮范围） |
| 主线识别 | ❌ 未实现（不在本轮范围） |
| 可参与性过滤 | ❌ 未实现（不在本轮范围） |

**Phase 2 新增模块：**
- `tradingagents/markets/cn_stock/hotlist/schema.py` — 数据结构定义
- `tradingagents/markets/cn_stock/hotlist/parser.py` — 热榜文本解析器
- `tradingagents/markets/cn_stock/hotlist/normalizer.py` — 记录标准化
- `tradingagents/markets/cn_stock/hotlist/attention_pool.py` — Attention Pool 构建
- `tradingagents/markets/cn_stock/hotlist/io.py` — 数据读写
- `scripts/import_manual_hotlist.py` — 手动热榜导入脚本
- `scripts/build_attention_pool.py` — Attention Pool 构建脚本
- `tests/test_cn_hotlist.py` — 测试文件（19 个测试）

**Attention Score v0.1 公式：**
```
rank_score = max(1, 21 - rank)  # rank 有效时
recency_weight = 0.5 ** (age_index / 10)  # 时间衰减
record_score = rank_score * recency_weight
daily_resonance_bonus = max(0, daily_source_count - 1) * 5 * recency_weight
consecutive_bonus = min(consecutive_days, 5) * 3
attention_score_20d = sum(record_score) + sum(daily_resonance_bonus) + consecutive_bonus
```

**当前限制：**
- 不接实时行情
- 不判断涨停
- 不判断高价
- 不输出选股建议
- 不做主线识别
- 不做可参与性过滤

**后续待办：**
- 与市场数据源结合
- 可参与性标签
- 平替规则

### Phase 2.5：热榜数据质量增强

| 任务 | 状态 |
|------|------|
| 读取 stock-pool 名称映射 | ✅ 已完成 |
| 修复 legacy invalid records | ✅ 已完成（203 条修复成功，41 条无法修复） |
| 更新 Attention Pool builder 支持 repaired legacy | ✅ 已完成 |
| 新增 board_type 离线推断 | ✅ 已完成 |
| 增强 Attention Score 可解释性（score_breakdown + evidence） | ✅ 已完成 |
| 生成 CSV 输出 | ✅ 已完成 |
| 生成 Top 50 explain | ✅ 已完成 |
| 更新测试（30 个测试全部通过） | ✅ 已完成 |

**Phase 2.5 新增文件：**
- `scripts/import_stock_name_map.py` — stock-pool 名称映射导入脚本
- `scripts/repair_legacy_records.py` — legacy invalid records 修复脚本
- `data/reference/stock_name_map.json` — 股票名称映射（3053 条）
- `data/reference/stock_name_map.jsonl` — 股票名称映射（含元数据）
- `data/manual_hotlists/legacy_import/structured/tradingagents-old/hotlist_legacy_repaired.jsonl` — 修复后的记录

**board_type v0.1 离线推断规则：**
- 600/601/603/605 → main_board_sh（上海主板）
- 000/001/002/003 → main_board_sz（深圳主板）
- 300/301 → chinext（创业板）
- 688/689 → star_market（科创板）
- 8/4 开头的北交所代码 → beijing_stock_exchange（北交所）
- 其他 → unknown

**当前限制：**
- board_type 只是离线粗略推断，不能替代实时交易资格判断
- 不判断涨停
- 不判断高价
- 不输出选股建议

### Phase 2.6：Attention Pool 合并逻辑复核与修正

| 任务 | 状态 |
|------|------|
| 复核 Phase 2.5 股票数下降原因 | ✅ 已完成 |
| 修复合并逻辑 bug | ✅ 已完成 |
| 生成 compare_original_vs_repaired 报告 | ✅ 已完成 |
| 更新测试（32 个测试全部通过） | ✅ 已完成 |

**问题原因：**
Phase 2.5 中 `--use-repaired-legacy` 分支只读取了修复文件（203 条），没有同时读取原始有效文件（449 条），导致 Attention Pool 从 129 只下降到 55 只。

**修复方案：**
`--use-repaired-legacy` 现在同时读取：
1. 原始有效 legacy 数据（449 条）
2. 修复成功 legacy 数据（203 条）
3. 合并后去重构建 Attention Pool

**修复后结果：**
- 不使用 repaired：489 条记录 → 129 只股票
- 使用 repaired：692 条记录 → 142 只股票
- 新增 13 只股票，删除 0 只股票

**关键发现：**
- 修复数据是增量，不会替代原有效数据
- 同一天同一股票在不同平台的记录保留用于共振计算
- 去重 key 为 `(trade_date, source, ticker)`，不会删除多平台记录

**新增文件：**
- `scripts/compare_attention_pool.py` — 对比报告生成脚本
- `data/manual_hotlists/attention_pool/audit/attention_pool_compare_original_vs_repaired.md` — 对比报告

### Phase 3A：Data Freshness Guard 骨架

| 任务 | 状态 |
|------|------|
| 创建 config/data_freshness.yaml | ✅ 已完成 |
| 实现 DataStatus / ReportFreshnessResult 模型 | ✅ 已完成 |
| 实现 DataFreshnessGuard 类 | ✅ 已完成 |
| 实现报告阻断/降级逻辑 | ✅ 已完成 |
| 实现 status summary 生成 | ✅ 已完成 |
| 预留 auto_update 接口 | ✅ 已完成 |
| 生成 Attention Pool freshness metadata | ✅ 已完成 |
| 测试（16 个测试全部通过） | ✅ 已完成 |

**新增文件：**
- `tradingagents/markets/common/__init__.py`
- `tradingagents/markets/common/data_status.py` — DataStatus / ReportFreshnessResult 模型
- `tradingagents/markets/common/data_freshness.py` — DataFreshnessGuard 类
- `config/data_freshness.yaml` — 新鲜度阈值配置
- `tests/test_data_freshness.py` — 16 个测试

**支持的 report_type：**
- `pre_close_report` — 尾盘辅助决策报告
- `post_close_report` — 盘后复盘报告
- `next_day_plan` — 次日观察计划
- `attention_pool` — Attention Pool 构建

**核心原则：**
- 数据过期不能强结论
- 抓取失败不能编造
- 公告失败不能说无重大利空
- 关键行情数据失败不能生成尾盘参与建议

**未实现：**
- 真实数据源更新
- 自动抓取
- 交易日历精确判断
- provider adapter 接入

### Phase 3A.5：a-stock-data 上游更新检查机制

| 任务 | 状态 |
|------|------|
| 创建 a_stock_data_baseline.json 基线文件 | ✅ 已完成 |
| 创建 check_a_stock_data_updates.py 检查脚本 | ✅ 已完成 |
| 创建测试（13 个测试全部通过） | ✅ 已完成 |
| 创建 GitHub Actions workflow | ❌ 未创建（建议后续添加） |

**新增文件：**
- `docs/external_sources/a_stock_data_baseline.json` — 审计基线
- `scripts/check_a_stock_data_updates.py` — 上游更新检查脚本
- `tests/test_external_source_update_check.py` — 13 个测试

**核心原则：**
- ✅ 可以自动检查更新
- ❌ 不允许自动合并上游代码
- ❌ 不允许自动修改 provider
- ❌ 不允许自动修改业务逻辑
- ⚠️ 上游更新后只能生成审计报告和人工确认事项
- ⚠️ 是否采用上游更新必须由用户 / ChatGPT / opencode 审查后决定

**风险分级：**
- Low：README 文档说明变化、示例变化
- Medium：CHANGELOG 提到接口修复、新增数据源、修改限流建议
- High：SKILL.md 中函数实现变化、关键接口变化、LICENSE 变化

**输出：**
- `docs/external_sources/a_stock_data_update_check_latest.md` — 最新检查报告
- `docs/external_sources/a_stock_data_update_checks/YYYY-MM-DD.md` — 有变化时的日期报告

### Phase 3B：Market-Wide Scan 数据结构骨架

| 任务 | 状态 |
|------|------|
| 创建 market_scan 目录和模块 | ✅ 已完成 |
| 实现 Market-Wide Scan schema（10 个数据结构） | ✅ 已完成 |
| 更新 data_freshness.yaml 增加 market_scan 配置 | ✅ 已完成 |
| 创建离线 sample input | ✅ 已完成 |
| 实现 build_market_wide_scan_result 骨架 | ✅ 已完成 |
| 创建测试（22 个测试全部通过） | ✅ 已完成 |
| 接入真实数据源 | ❌ 未实现 |
| 实现主线识别 | ❌ 未实现 |
| 实现尾盘报告 | ❌ 未实现 |

**新增文件：**
- `tradingagents/markets/cn_stock/market_scan/__init__.py`
- `tradingagents/markets/cn_stock/market_scan/schema.py` — 数据结构定义
- `tradingagents/markets/cn_stock/market_scan/scan_result.py` — 骨架函数
- `tradingagents/markets/cn_stock/market_scan/freshness.py` — Freshness 对接
- `tradingagents/markets/cn_stock/market_scan/io.py` — I/O 工具
- `tests/fixtures/cn_market_scan/sample_market_scan_input.json` — 离线样例
- `tests/test_cn_market_scan_schema.py` — 22 个测试

**实现的 schema：**
- `IndexSnapshot` — 指数快照
- `MarketBreadthSnapshot` — 涨跌家数
- `TurnoverSnapshot` — 成交额
- `SectorSnapshot` — 板块快照
- `StrongStockSnapshot` — 强势股快照
- `LimitUpPoolSnapshot` — 涨停池
- `ThemeCandidateSignal` — 主题候选信号
- `OutOfPoolCandidateSignal` — 池外候选信号
- `MarketWideScanInput` — 扫描输入
- `MarketWideScanResult` — 扫描结果

**Market-Wide Scan 定位：**
- 先看全市场
- 再匹配 Attention Pool
- 池外高置信度只是例外机制

**当前实现状态：**
- ✅ 数据结构
- ✅ 离线样例
- ✅ freshness 对接骨架
- ❌ 真实数据源
- ❌ 主线识别
- ❌ 尾盘报告

**待处理事项：**
- a-stock-data baseline commit 待补充（GitHub API 限流）

### Phase 3C：Theme Detection / 主线识别 schema 骨架

| 任务 | 状态 |
|------|------|
| 创建 theme_detection 目录和模块 | ✅ 已完成 |
| 实现 Theme Detection schema（ThemeEvidence/ThemeCandidate/ThemeDetectionInput/ThemeDetectionResult） | ✅ 已完成 |
| 实现 ThemeLevel / ThemeStatus 枚举 | ✅ 已完成 |
| 实现评分 v0.1 骨架 | ✅ 已完成 |
| 实现 build_theme_detection_result 骨架 | ✅ 已完成 |
| 创建离线样例 | ✅ 已完成 |
| 创建测试（25 个测试全部通过） | ✅ 已完成 |
| 接入真实数据 | ❌ 未实现 |
| 实现最终主线识别算法 | ❌ 未实现 |
| 实现尾盘报告 | ❌ 未实现 |

**新增文件：**
- `tradingagents/markets/cn_stock/theme_detection/__init__.py`
- `tradingagents/markets/cn_stock/theme_detection/schema.py` — 数据结构定义
- `tradingagents/markets/cn_stock/theme_detection/scoring.py` — 评分 v0.1 骨架
- `tradingagents/markets/cn_stock/theme_detection/detector.py` — 骨架函数
- `tradingagents/markets/cn_stock/theme_detection/io.py` — I/O 工具
- `tests/fixtures/cn_theme_detection/sample_theme_detection_input.json` — 离线样例
- `tests/fixtures/cn_theme_detection/sample_theme_detection_result.json` — 离线样例
- `tests/test_cn_theme_detection_schema.py` — 25 个测试

**实现的 schema：**
- `ThemeEvidence` — 主题证据（9 种证据类型）
- `ThemeCandidate` — 主题候选
- `ThemeLevel` — 主题级别枚举（S/A/B/C/unknown）
- `ThemeStatus` — 主题状态枚举（9 种状态）
- `ThemeDetectionInput` — 主题检测输入
- `ThemeDetectionResult` — 主题检测结果

**Theme Detection 定位：**
- 连接 Market-Wide Scan 和 Attention Pool
- 生成主线候选
- 不直接输出买卖建议

**当前实现状态：**
- ✅ 数据结构
- ✅ 评分骨架
- ✅ 离线样例
- ❌ 真实数据
- ❌ 最终主线识别算法
- ❌ 尾盘报告

**风险提示：**
- 主题评分 v0.1 只是骨架
- 不能作为交易依据
- 后续需要真实数据和反思系统验证

### Phase 3D：Candidate Selection / 标的选择 schema 骨架

| 任务 | 状态 |
|------|------|
| 创建 candidate_selection 目录和模块 | ✅ 已完成 |
| 实现 Candidate Selection schema（StockCandidate/ReplacementCandidate/CandidateSelectionResult） | ✅ 已完成 |
| 实现 CandidateTradabilityFlag/CandidateRiskLevel/CandidateActionLabel 枚举 | ✅ 已完成 |
| 实现平替规则 v0.1 骨架 | ✅ 已完成 |
| 实现候选评分 v0.1 骨架 | ✅ 已完成 |
| 实现 build_candidate_selection_result 骨架 | ✅ 已完成 |
| 创建离线样例 | ✅ 已完成 |
| 创建测试（28 个测试全部通过） | ✅ 已完成 |
| 接入真实行情、公告、结构数据 | ❌ 未实现 |
| 实现正式选股算法 | ❌ 未实现 |
| 实现尾盘报告 | ❌ 未实现 |

**新增文件：**
- `tradingagents/markets/cn_stock/candidate_selection/__init__.py`
- `tradingagents/markets/cn_stock/candidate_selection/schema.py` — 数据结构定义
- `tradingagents/markets/cn_stock/candidate_selection/replacement.py` — 平替规则骨架
- `tradingagents/markets/cn_stock/candidate_selection/scoring.py` — 候选评分骨架
- `tradingagents/markets/cn_stock/candidate_selection/selector.py` — 骨架函数
- `tradingagents/markets/cn_stock/candidate_selection/io.py` — I/O 工具
- `tests/fixtures/cn_candidate_selection/sample_candidate_selection_input.json` — 离线样例
- `tests/test_cn_candidate_selection_schema.py` — 28 个测试

**实现的 schema：**
- `StockCandidate` — 股票候选
- `ReplacementCandidate` — 平替候选
- `OutOfPoolHighConvictionCandidate` — 池外高置信度候选
- `CandidateSelectionInput` — 标的选择输入
- `CandidateSelectionResult` — 标的选择结果
- `CandidateTradabilityFlag` — 可交易性标志枚举
- `CandidateRiskLevel` — 风险等级枚举
- `CandidateActionLabel` — 操作标签枚举（不含 buy/sell）

**Candidate Selection 定位：**
- 连接 Theme Detection 和 Report
- 区分池内标的、平替标的、池外高置信度标的、blocked 标的
- 不直接输出买卖建议

**当前实现状态：**
- ✅ 数据结构
- ✅ 平替规则骨架
- ✅ 候选评分骨架
- ✅ 离线样例
- ❌ 真实行情、公告、结构数据
- ❌ 正式选股算法
- ❌ 尾盘报告

**风险提示：**
- candidate_score v0.1 只是骨架
- 没有实时数据时不能判断涨停、高价、止损、止盈
- 平替不能硬凑

### Phase 3：A 股报告 MVP

| 任务 | 状态 |
|------|------|
| 尾盘辅助决策报告 | ❌ 未实现 |
| 盘后复盘报告 | ❌ 未实现 |
| 次日观察计划 | ❌ 未实现 |
| 基础市场环境识别 | ❌ 未实现 |
| 基础主线识别 | ❌ 未实现 |
| 基础核心股识别 | ❌ 未实现 |
| 基础趋势结构分析 | ❌ 未实现 |

### Phase 4：数据源接入

#### Phase 4A：Provider 基础设施（已完成）

| 任务 | 状态 |
|------|------|
| ProviderResult 统一返回类型 | ✅ 已完成 |
| BaseCnStockProvider 抽象基类 | ✅ 已完成 |
| RawPayloadStore 原始载荷存储 | ✅ 已完成 |
| RateLimiter 统一限速器 | ✅ 已完成 |
| ProviderRegistry 供应器注册中心 | ✅ 已完成 |
| LocalHotlistProvider（本地热榜） | ✅ 已完成 |
| ProviderResult → DataStatus 转换 | ✅ 已完成 |
| cn_stock_providers.yaml 配置文件 | ✅ 已完成 |
| THIRD_PARTY_NOTICES.md | ✅ 已完成 |
| 测试（30 个） | ✅ 全部通过 |

**注意：**
- 当前未实现外部 provider（mootdx/腾讯/akshare/东财/同花顺）
- 未调用真实 API
- 下一步建议 Phase 4B：mootdx 行情 provider（实时行情、K线、盘口、F10）

#### Phase 4B：mootdx 行情 Provider v0.1（已完成）

| 任务 | 状态 |
|------|------|
| MootdxProvider 实现 | ✅ 已完成 |
| daily_kline | ✅ 已实现 |
| minute_kline | ✅ 已实现 |
| index_kline | ✅ 已实现 |
| realtime_quote | ✅ 已实现 |
| order_book | ✅ 已实现（partial，取决于 mootdx 返回字段） |
| lazy import mootdx | ✅ 已实现 |
| mootdx 未安装时优雅失败 | ✅ 已实现 |
| Raw payload 保存 | ✅ 已实现 |
| ProviderResult → DataStatus | ✅ 已实现 |
| RateLimiter 接入 | ✅ 已实现 |
| cn_stock_providers.yaml 更新 | ✅ 已完成 |
| smoke_test_mootdx_provider.py | ✅ 已创建（需手动 --allow-network） |
| mock 单元测试（34 个） | ✅ 全部通过 |
| mootdx 依赖声明 | ✅ 已加入 pyproject.toml |

**未实现（后续阶段）：**
- mootdx finance
- mootdx F10
- 逐笔成交
- 资金流
- 自动更新调度
- 报告生成集成

**限制：**
- mootdx 依赖通达信服务器可用性
- 数据时间 as_of_time 可能需要后续进一步校验
- order_book 字段以实际 mootdx 返回为准
- 北交所支持情况需要后续确认
- smoke test 需要国内 IP 和手动 --allow-network

#### Phase 4C：Tencent Provider 骨架（已完成）

| 任务 | 状态 |
|------|------|
| TencentProvider 实现 | ✅ 已完成 |
| valuation | ✅ 骨架（返回 not_implemented） |
| market_cap | ✅ 骨架（返回 not_implemented） |
| turnover_rate | ✅ 骨架（返回 not_implemented） |
| limit_price | ✅ 骨架（返回 not_implemented） |
| ProviderResult → DataStatus | ✅ 已实现 |
| RateLimiter 接入 | ✅ 已实现 |
| mock 单元测试（15 个） | ✅ 全部通过 |

**注意：**
- 腾讯 API 端点需要验证
- 当前返回 not_implemented
- 不默认联网

#### Phase 4D：Cninfo 巨潮公告 Provider 骨架（已完成）

| 任务 | 状态 |
|------|------|
| CninfoProvider 实现 | ✅ 已完成 |
| announcement | ✅ 骨架（返回 not_implemented） |
| ProviderResult → DataStatus | ✅ 已实现 |
| RateLimiter 接入 | ✅ 已实现 |
| mock 单元测试（16 个） | ✅ 全部通过 |

**注意：**
- 巨潮 API 端点需要验证
- 当前返回 not_implemented
- 不默认联网
- 公告失败时不能写"无重大利空"
- 不实现 Disclosure Guard
- 不实现 Negative Event Guard

#### Phase 4D.2：Provider 并发抓取策略（已完成）

| 任务 | 状态 |
|------|------|
| ProviderConcurrencyConfig schema | ✅ 已完成 |
| cn_stock_providers.yaml 增加 concurrency 配置 | ✅ 已完成 |
| 默认外部 provider max_concurrency=1 | ✅ 已完成 |
| 本地 provider max_concurrency=null | ✅ 已完成 |
| batch_preferred 策略 | ✅ 已完成 |
| 并发策略文档 | ✅ 已完成 |
| 并发配置测试（13 个） | ✅ 全部通过 |

**核心原则：**
- 数据抓取允许有限并行，但禁止无控制并行
- 所有 provider 必须遵守 RateLimiter
- 所有 provider 必须支持 max_concurrency 配置
- 默认所有外部 provider 的 max_concurrency=1
- 批量接口优先于多线程逐个请求
- 同一 provider 内不允许绕过 rate limiter 并发乱打
- 并发失败不能静默成功

**注意：**
- 本阶段未实现真实并发 orchestrator
- 未来 provider orchestration 必须遵守并发策略

#### Phase 4E：akshare/东财数据源接入（未实现）

| 任务 | 状态 |
|------|------|
| akshare 板块/新闻/涨停/财联社 | ❌ 未实现 |
| 东财/同花顺研报和一致预期 | ❌ 未实现（低优先级） |

### Phase 5：反思系统

| 任务 | 状态 |
|------|------|
| 次日反思 | ❌ 未实现 |
| 周反思 | ❌ 未实现 |
| 月反思 | ❌ 未实现 |
| 季度反思 | ❌ 未实现 |
| 年度反思 | ❌ 未实现 |
| 观察→假设→验证规则→失效经验 的记忆分层 | ❌ 未实现 |

### Phase 6：持仓资金模块

| 任务 | 状态 |
|------|------|
| 手动录入真实持仓 | ❌ 未实现 |
| 记录资金状态 | ❌ 未实现 |
| 结合持仓给出操作建议 | ❌ 未实现 |
| 识别主题暴露集中风险 | ❌ 未实现 |

### Phase 7：美股和加密货币轻量扩展

| 任务 | 状态 |
|------|------|
| 保留原项目美股能力 | ⚠️ 待确认（原项目已有，但未测试是否兼容魔改后的架构） |
| 新增 market profile | ❌ 未实现 |
| 美股做观察报告 | ❌ 未实现 |
| 加密货币做 BTC/ETH/主流币趋势与风险报告 | ❌ 未实现 |

### 原项目已有能力状态（需注意：这些是原项目能力，非本项目实现）

### 当前路径配置（Phase 1.5 更新后）

| 配置项 | 默认路径 | 环境变量覆盖 |
|--------|----------|-------------|
| `project_dir` | `<PROJECT_ROOT>` | — |
| `results_dir` | `<PROJECT_ROOT>/.tradingagents/logs` | `TRADINGAGENTS_RESULTS_DIR` |
| `data_cache_dir` | `<PROJECT_ROOT>/.tradingagents/cache` | `TRADINGAGENTS_CACHE_DIR` |
| `memory_log_path` | `<PROJECT_ROOT>/.tradingagents/memory/trading_memory.md` | `TRADINGAGENTS_MEMORY_LOG_PATH` |
| checkpoint 数据库 | `<PROJECT_ROOT>/.tradingagents/cache/checkpoints/<TICKER>.db` | 跟随 `data_cache_dir` |
| 项目根目录 | 自动推断（基于 `default_config.py` 位置） | `TRADINGAGENTS_PROJECT_ROOT` |

**已实现的改造：**
- `default_config.py` 已修改为使用项目本地路径
- 支持 `TRADINGAGENTS_PROJECT_ROOT` 环境变量显式指定项目根目录
- 环境变量覆盖能力完整保留
- `.gitignore` 已修复，允许目录结构和 `.gitkeep` 文件被跟踪
- `.env.example` 已更新，包含路径配置示例

### 原项目已有能力状态（需注意：这些是原项目能力，非本项目实现）

| 能力 | 状态 | 说明 |
|------|------|------|
| 多 Agent 协作框架 | ⚠️ 部分实现 | 原项目已有 LangGraph 编排，但未针对 A 股适配 |
| 多 LLM 提供商支持 | ⚠️ 部分实现 | 原项目已有，但未测试是否兼容魔改后的架构 |
| 结构化输出 | ⚠️ 部分实现 | 原项目已有 Pydantic Schema，但未针对 A 股报告适配 |
| 决策日志记忆 | ⚠️ 部分实现 | 原项目已有 `TradingMemoryLog`，但未针对四层记忆分层改造 |
| 基础反思系统 | ⚠️ 部分实现 | 原项目已有 `Reflector`，但只有 2-4 句基础反思，未实现分层反思 |
| 检查点恢复 | ⚠️ 部分实现 | 原项目已有，但未测试是否兼容魔改后的架构 |
| CLI 交互界面 | ⚠️ 部分实现 | 原项目已有，但未针对 A 股报告改造 |
| Yahoo Finance 数据 | ⚠️ 部分实现 | 原项目已有，但对 A 股支持不完善 |
| Alpha Vantage 数据 | ⚠️ 部分实现 | 原项目已有，但对 A 股支持不完善 |
| A 股专属模块 | ❌ 未实现 | 无任何 cn_stock 相关代码 |
| 热榜系统 | ❌ 未实现 | 无 Attention Pool |
| 主线/龙头识别 | ❌ 未实现 | 无 Theme/Leader Agent |
| 市场环境分类 | ❌ 未实现 | 无 A 股市场环境状态机 |
| 持仓/资金模块 | ❌ 未实现 | 无 portfolio 目录 |
| Data Freshness Guard | ❌ 未实现 | 无数据新鲜度检查 |
| A 股数据源接入 | ❌ 未实现 | 无 mootdx/akshare/腾讯财经等 |

### 当前实现状态总结

**已实现：**
- PROJECT_HANDOFF.md 第一版已创建并更新
- 项目目标和阶段规划已初步沉淀到文档
- AGENTS.md 已创建
- PROJECT_BRIEF.md 已创建
- REPORTS.md 已创建
- MEMORY_AND_REFLECTION.md 已创建
- DATA_SOURCES.md 已创建
- 本地目录结构已创建（.tradingagents/、data/、docs/）

**部分实现（原项目已有，但未针对本项目适配）：**
- 原 TradingAgents 已有 LangGraph 多 Agent 框架
- 原项目已有基础 memory/reflection 能力
- 原项目已有美股相关数据流和分析框架
- 原项目已有结构化输出基础

**未实现：**
- A 股市场专属模块
- 手动热榜解析
- Attention Pool
- Market Regime Agent
- Theme Agent
- Leader Agent
- Structure Agent
- Negative Event Guard
- Fundamental Risk Guard
- Data Freshness Guard
- **公告层（Disclosure Layer）**
- **Disclosure Guard**
- A 股尾盘报告
- A 股盘后报告
- 次日反思报告
- 周/月/季/年反思
- 持仓资金模块
- 多市场 market profile 架构
- A 股数据源接入
- 项目本地化 memory/cache/logs/reports/raw 目录重构

**待确认：**
- 所有"待确认问题"章节（第十八章）中的内容

---

## 十五、数据新鲜度与禁止编造数据原则

### 15.1 核心原则

> **系统绝对不能编造行情、成交额、涨跌幅、涨停状态、主线强度、止损止盈位。**

### 15.2 数据新鲜度检查

1. 系统在生成任何正式报告前，**必须先执行数据新鲜度检查**。
2. 尾盘选股报告尤其依赖实时数据，K 线数据必须更新到距离当前时间 10 分钟以内。
3. 如果 K 线、实时价格、涨停状态、板块数据等关键数据过期，系统应**先自动更新**，不要先询问用户。
4. 如果自动更新失败，必须如实说明失败原因、失败数据源、是否有备用源。
5. 数据不完整时只能降级分析，不能输出强结论。
6. 系统绝对不能编造行情、成交额、涨跌幅、涨停状态、主线强度、止损止盈位。
7. 如果关键数据缺失，**必须拒绝生成尾盘参与建议**，只能输出数据缺失说明或历史复盘。
8. 非交易时间用户与 Agent 沟通时，也要根据任务类型检查数据新鲜度。如果超过阈值，应提醒用户并主动更新。
9. 手动热榜无法自动更新，如果缺失，只能提示用户缺失，不能编造热榜。
10. 每份正式报告开头都应包含"数据新鲜度检查"摘要。

### 15.3 建议阈值

#### 尾盘辅助决策报告

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
| 手动热榜 | 使用最近一次，但必须标注日期；缺失则提醒用户 |

#### 盘后复盘报告

| 数据类型 | 新鲜度阈值 |
|----------|-----------|
| 日 K | 必须更新到最近交易日 |
| 分钟 K | 必须覆盖当日完整交易时段 |
| 成交额/换手率 | 必须更新到收盘 |
| 涨停/跌停/炸板/连板数据 | 收盘后 30 分钟内更新 |
| 板块涨幅/成交额 | 收盘后 30 分钟内更新 |
| 新闻快讯 | 30 分钟内更新 |
| 公告/重大利空 | 2 小时内更新，建议晚间二次刷新 |

#### 次日计划/非交易时间分析

| 数据类型 | 新鲜度阈值 |
|----------|-----------|
| 日 K、板块、涨停、情绪数据 | 必须更新到最近一个交易日 |
| 新闻 | 12 小时以内 |
| 公告/利空 | 12 小时以内 |
| 研报 | 7 天以内 |
| 基本面快照 | 30 天以内或最近财报期 |
| 持仓数据 | 超过 1 个交易日应提醒用户更新 |

#### 公告层数据新鲜度

| 场景 | 新鲜度要求 |
|------|-----------|
| 尾盘报告 | 检查最近 1-3 个交易日公告；重大风险公告尽量 30-60 分钟内更新；如果更新失败，报告必须说明 |
| 盘后报告 | 检查当日公告；允许盘后 1-2 小时内形成初版；建议晚间二次刷新公告 |
| 次日计划 | 必须检查昨晚至今早公告；如果公告数据不可用，不能输出"无重大利空" |
| 持仓建议 | 必须检查持仓股公告风险 |
| 池外高置信度标的 | 必须临时检查公告风险；不能绕过公告层 |

### 15.4 数据失败降级规则

| 失败数据源 | 降级策略 |
|-----------|----------|
| 新闻失败 | 可以继续做资金和结构分析，但不能做完整利空排雷 |
| 研报失败 | 可以继续短线分析 |
| 基本面过期 | 可以继续主线观察，但要提示排雷不完整 |
| 手动热榜缺失 | 可以使用已有 Attention Pool 和行情，但必须提示热榜不完整 |
| **公告数据失败** | **不能声称"无重大利空"；必须说明公告层数据不可用；不能输出强结论** |
| 实时价格、分钟 K、日 K、板块数据、涨停状态等关键数据失败 | **不能生成尾盘参与建议和强结论** |

### 15.5 未来建议实现

- 新增 `Data Freshness Guard` Agent
- 新增 `data_freshness.yaml` 配置文件
- 每个数据源返回 `fetched_at`、`as_of_time`、`source`、`status`、`error_message`
- 每份报告必须包含数据状态摘要

---

## 十六、核心原则（不可破坏）

以下原则是项目的根基，任何改动都不能违反：

1. **本项目不是自动交易系统。** 不连接券商，不执行自动下单。
2. **不接券商接口。** 任何券商 API 都不接入。
3. **不执行自动下单。** 所有交易决策由用户手动执行。
4. **不输出无条件买入/卖出指令。** 输出应以"观察、等待、回避、风险升高、结构确认、持仓处理建议"为主。
5. **A 股是第一优先级，但不能破坏美股和加密货币能力。**
6. **A 股规则必须放在 A 股市场专属模块中，不能硬编码进全局逻辑。**
7. **系统应采用"规则引擎 + LLM"的模式，不能纯靠 LLM 主观判断。**
8. **每个结论都要有证据。**
9. **反思经验不能因为一两次成功就直接变成永久规则。**
10. **新闻和基本面不是 A 股短线主驱动，只做辅助验证和风险排雷。**
11. **确定性利空、公告风险、监管风险、退市风险应强降权或一票否决。**
12. **交接文档 PROJECT_HANDOFF.md 必须长期维护，每次重大改动都要更新。**
13. **系统绝对不能编造数据。** 数据缺失时必须如实说明，不能编造。

---

## 十七、后续每次更新要求

### 17.1 必须更新 PROJECT_HANDOFF.md 的场景

| 场景 | 说明 |
|------|------|
| 每次新增功能后 | 更新"实现状态"章节，标记新功能状态 |
| 每次修改架构后 | 更新"当前项目结构"章节，反映新的目录结构 |
| 每次新增数据源后 | 更新数据源相关章节 |
| 每次新增 Agent 后 | 更新"核心模块规划"章节，标记新 Agent 状态 |
| 每次改变项目原则后 | 更新"核心原则"章节 |
| 每次改变报告格式后 | 更新"报告体系"章节 |
| 每次改变反思系统后 | 更新"反思记忆系统"章节 |

### 17.2 opencode 的主动责任

- 每次执行任务后，如果发现实际代码结构和文档不一致，**必须提醒用户**，并建议同步更新文档
- 如果发现新的未记录的实现状态变化，**必须主动更新** PROJECT_HANDOFF.md
- 如果遇到不确定的问题，**必须记录在文档末尾的"待确认问题"章节**

### 17.3 更新格式

每次更新 PROJECT_HANDOFF.md 时，必须在文档末尾的"变更日志"章节记录：
- 更新日期
- 更新内容摘要
- 更新原因

---

## 十八、待确认问题

> 以下问题需要用户或 ChatGPT 确认后，opencode 才能继续执行。
> 这些问题的答案将直接影响后续开发方向和具体实现，opencode 不得自行假设答案并实现。

### 18.1 Attention Score 具体评分公式待确认

- 排名分如何计算（第 1 名 vs 第 20 名的分值差异）
- 多平台共振如何加权（同时出现在 3 个平台 vs 只出现在 1 个平台）
- 连续上榜如何加权（连续 5 天上榜 vs 首次上榜）
- 时间衰减如何计算（昨天上榜 vs 10 天前上榜的权重差异）
- 是否需要区分同花顺/东方财富/雪球/通达信的平台权重

### 18.2 手动热榜文本解析规则待确认

- 用户只会提供自然语言或复制文本
- Agent 如何识别股票名称、代码、排名和平台来源
- 遇到重名股票、缺少代码、格式混乱时如何处理
- 是否允许低置信度解析结果进入待确认区

### 18.3 主板过滤规则

- **热榜和 Attention Pool 不做主板过滤**，所有热榜股票全部保留
- **尾盘可参与平替优先主板**，但非主板股票仍作为主线强度证据
- 需要明确如何识别主板股票（代码前缀规则：60 开头沪市主板、00 开头深市主板）
- ST、*ST、退市风险股在尾盘可参与平替中默认剔除

### 18.4 主线识别评分规则待确认

- 板块涨幅、成交额、涨停数、持续天数、热榜共振分别如何加权
- 如何区分强主线、弱主线、一日游、伪主线
- 一个股票属于多个主题时如何处理

### 18.5 龙头/核心股识别规则待确认

- 第一核心、龙头、趋势中军、弹性标的、平替标的的定义需要进一步细化
- 最佳标的不适合参与时，平替标的如何选择
- 平替标的是同主线内次强，还是结构更适合参与的标的

### 18.6 尾盘报告强结论阻断条件待确认

- 哪些数据缺失时绝对不能输出尾盘参与建议
- 哪些数据缺失时可以降级为观察报告
- 如何在报告中展示数据缺失对结论的影响

### 18.7 数据源更新策略待确认

- mootdx、腾讯财经、akshare、东财、同花顺等数据源的优先级需要进一步细化
- 备用源如何切换
- 多个数据源冲突时如何处理
- 是否保留 raw payload 以便追溯

### 18.8 交易日历和数据时间判断待确认

- 如何识别最近一个 A 股交易日
- 节假日、周末、临时休市如何处理
- 非交易时间如何判断数据是否过期
- 尾盘、盘后、次日计划分别对应什么数据要求

### 18.9 止损位和止盈/减仓位计算规则待确认

- 止损位应优先使用平台下沿、MA10、前低、趋势结构失效点
- 止盈/减仓位应结合压力位、上涨幅度、放量滞涨、板块退潮
- 不能随意编造价位
- 如果 K 线数据不完整，不允许给出具体价位

### 18.10 反思系统升级规则待确认

- 什么情况下 Observation 可以升级为 Hypothesis
- 什么情况下 Hypothesis 可以升级为 Validated Rule
- 出现多少反例后规则需要降权
- Deprecated Memory 是否需要定期复查

### 18.11 持仓资金模块待确认

- 用户未来会手动输入真实持仓和资金
- 需要确认保存格式（YAML/JSON/其他）
- 需要确认是否需要脱敏
- 需要确认如何处理主题暴露集中风险
- 当前阶段只预留，不实现

### 18.12 美股和加密货币功能边界待确认

- A 股优先
- 美股和加密货币只做轻量辅助决策
- 需要确认哪些原项目功能必须保留
- 不能让 A 股规则污染 us_stock 和 crypto

### 18.13 报告模板细节待确认

- 尾盘报告、盘后报告、次日反思、周/月/季/年反思的最终字段仍需细化
- 每份报告都必须包含数据新鲜度摘要
- 每个结论都应有证据字段

### 18.15 高价阈值和平替规则待确认

- 高价阈值 120 元是否长期固定，还是后续按账户规模/波动率动态调整
- 平替标的排序公式待确认（同主线、主板、非涨停、价格 ≤ 120、成交额充足、结构未破坏，如何加权）
- 非主板最强标的是否只作为主线强度证据，还是未来在用户权限变化后可参与
- 涨停票平替规则是否要求同主线，是否允许相邻主线

### 18.16 池外高置信度提示规则待确认

- 池外高置信度提示的硬阈值如何设置
- 池外标的是否允许进入次日观察计划
- 池外标的需要连续观察几天才能进入 Attention Pool 或常规候选池
- 新主线启动时，如何区分真主线和一日游
- 全市场扫描的性能和数据源优先级如何设计

### 18.17 遗留项目数据迁移待确认

- ✅ **已在 Phase 1.9 解决**：tradingagents-old 热榜数据已正式迁移
- stock-pool 暂不迁移为热榜，仅作为后续参考资源
- 旧数据与新数据日期重复时：新数据优先，旧数据保留在 legacy_import
- 缺少 name 字段的记录已进入 invalid_records
- 迁移后已保留原始文件路径信息（original_path 字段）

### 18.18 公告层规则待确认

- 公告风险关键词和分类规则如何细化
- Level 3 一票否决是否所有场景都适用
- 是否需要晚间公告二次报告
- mootdx F10 最新提示是否仅作为摘要补充
- 巨潮 cninfo / akshare 接口的具体使用方式和频率限制
- 公告数据缓存策略和更新频率

### 18.19 a-stock-data 接入待确认

- 是否将 a-stock-data vendored 到 third_party
- 是否建立 THIRD_PARTY_NOTICES.md
- 哪些端点作为 MVP 第一批接入
- 是否保留 akshare 作为 fallback
- 是否采用 a-stock-data 的直连 HTTP 方案作为主路径
- 东财限流器是否直接参考 em_get() 实现

### 18.14 待处理事项（代码路径本地化）

以下问题在 Phase 1 代码扫描中发现，需要在后续阶段处理：

1. **原项目 memory/cache/logs 默认使用用户 home 目录**（`~/.tradingagents/`），不是项目本地目录
   - ✅ **已在 Phase 1.5 解决**：默认路径已改为项目本地 `.tradingagents/`
2. **核心配置文件**：`tradingagents/default_config.py`
   - ✅ **已在 Phase 1.5 修改**：使用 `pathlib` 计算项目根目录
3. **使用这些路径的文件**：
   - `tradingagents/graph/checkpointer.py` — 使用 `data_cache_dir`，无需修改
   - `tradingagents/agents/utils/memory.py` — 使用 `memory_log_path`，无需修改
   - `tradingagents/graph/trading_graph.py` — 使用 `results_dir` 和 `data_cache_dir`，无需修改
4. **.gitignore 问题**：
   - ✅ **已在 Phase 1.5 解决**：添加了 negation 规则允许 `.gitkeep` 跟踪

---

## 十九、变更日志

| 日期 | 更新内容 | 更新原因 |
|------|----------|----------|
| 2026-05-31 | 创建 PROJECT_HANDOFF.md | 项目交接文档初始化，整合所有已知信息 |
| 2026-05-31 | 补充 13 项待确认问题；修正实现状态为保守表述；原项目能力标记为"部分实现"；增加"PROJECT_HANDOFF.md 不是需求冻结文档"提醒 | 初版文档过于乐观，容易误导后续开发；大量细节问题尚未确认 |
| 2026-05-31 | Phase 1 文档创建：AGENTS.md、PROJECT_BRIEF.md、REPORTS.md、MEMORY_AND_REFLECTION.md、DATA_SOURCES.md；创建本地目录结构；扫描当前路径配置并记录 | Phase 1 基础文档和项目工作规范建立 |
| 2026-05-31 | Phase 1.5 路径本地化：default_config.py 改为项目本地路径；支持 TRADINGAGENTS_PROJECT_ROOT；修复 .gitignore；更新 .env.example | 项目本地化路径改造完成 |
| 2026-05-31 | Phase 1.6 规则更新：热榜全量录入不剔除；Attention Pool 定义为全市场注意力池；尾盘区分最强标的和平替标的；高价阈值 120 元；新增待确认问题 | 用户更新热榜和尾盘选股规则 |
| 2026-05-31 | Phase 1.7 补充全市场扫描优先原则；明确 Attention Pool 不是唯一选股范围；新增池外高置信度提示机制（Out-of-Pool High Conviction Alert）；新增报告输出分层（池内标的、平替标的、池外高置信度标的）；新增待确认问题 | 用户确认系统不应只在 Attention Pool 中选股 |
| 2026-05-31 | Phase 1.8 遗留项目资产审计：扫描 tradingagents-old 和 stock-pool；创建 LEGACY_ASSET_INVENTORY.md 和 LEGACY_MIGRATION_PLAN.md；创建 legacy_import 目录；发现 19 天热榜数据和完整票池系统 | 审计旧项目资产，准备历史数据迁移 |
| 2026-05-31 | Phase 1.9 历史热榜数据迁移：正式迁移 tradingagents-old 热榜 JSONL 数据；创建迁移脚本；生成审计报告；有效记录 449 条，无效记录 244 条（name 字段缺失）；stock-pool 暂不迁移 | 历史热榜数据迁移完成，可用于 Attention Pool 初始化 |
| 2026-05-31 | Phase 1.10 公告层规划：新增公告层（Disclosure Layer）定位和风险分类（Level 0-3）；更新报告模板增加公告风险检查；更新数据新鲜度规则增加公告层阈值；新增待确认问题 | 用户确认需要增加公告层作为风险控制核心输入 |
| 2026-05-31 | Phase 1.11 a-stock-data 外部数据工具包审计：审计 GitHub 仓库 simonlin1212/a-stock-data；许可证 Apache-2.0；7 层架构 27 端点 13 数据源；推荐抽取为 provider adapter；创建审计报告；新增待确认问题 | 评估外部数据工具包作为 A 股数据层参考实现 |
| 2026-05-31 | Phase 2 手动热榜与 Attention Pool 初版实现：实现 parser/normalizer/attention_pool/io 模块；实现 import_manual_hotlist.py 和 build_attention_pool.py 脚本；19 个测试全部通过；成功读取 legacy_import 数据；Attention Pool 生成 129 只股票 | 初版热榜录入和 Attention Pool 系统可用 |
| 2026-05-31 | Phase 2.5 热榜数据质量增强：导入 stock-pool 名称映射（3053 条）；修复 legacy invalid records（203 条修复成功）；新增 board_type 离线推断；增强 Attention Score 可解释性（score_breakdown + evidence）；生成 CSV 和 Top50 explain；30 个测试全部通过 | 数据质量增强，Attention Pool 更可信 |
| 2026-05-31 | Phase 2.6 合并逻辑复核与修正：修复 --use-repaired-legacy 只读取修复文件未读取原始有效文件的 bug；修复后 Attention Pool 从 55 只恢复到 142 只；新增 compare_original_vs_repaired 对比报告；32 个测试全部通过 | 修复 Phase 2.5 股票数下降异常 |
| 2026-05-31 | Phase 3A Data Freshness Guard 骨架实现：创建 data_freshness.yaml 配置；实现 DataStatus/ReportFreshnessResult 模型；实现 DataFreshnessGuard 类；支持 pre_close_report/post_close_report/next_day_plan/attention_pool；实现报告阻断/降级逻辑；预留 auto_update 接口；16 个测试全部通过 | 系统级数据新鲜度基础设施 |
| 2026-05-31 | Phase 3A.5 a-stock-data 上游更新检查机制：创建 a_stock_data_baseline.json 基线文件；创建 check_a_stock_data_updates.py 检查脚本；实现风险分级（Low/Medium/High）；13 个测试全部通过 | 外部参考源更新检查机制 |
| 2026-05-31 | Phase 3B Market-Wide Scan 数据结构骨架：实现 10 个 schema（IndexSnapshot/MarketBreadthSnapshot/TurnoverSnapshot/SectorSnapshot/StrongStockSnapshot/LimitUpPoolSnapshot/ThemeCandidateSignal/OutOfPoolCandidateSignal/MarketWideScanInput/MarketWideScanResult）；新增 market_scan freshness 配置；创建离线样例；实现骨架函数；22 个测试全部通过 | 全市场扫描层数据结构就绪 |
| 2026-05-31 | Phase 3C Theme Detection 主线识别 schema 骨架：实现 ThemeEvidence/ThemeCandidate/ThemeDetectionInput/ThemeDetectionResult；实现 ThemeLevel/ThemeStatus 枚举；实现评分 v0.1 骨架；实现 build_theme_detection_result 骨架；创建离线样例；25 个测试全部通过 | 主线识别层数据结构就绪 |
| 2026-05-31 | Phase 3D Candidate Selection 标的选择 schema 骨架：实现 StockCandidate/ReplacementCandidate/OutOfPoolHighConvictionCandidate/CandidateSelectionInput/CandidateSelectionResult；实现 CandidateTradabilityFlag/CandidateRiskLevel/CandidateActionLabel 枚举；实现平替规则 v0.1 骨架；实现候选评分 v0.1 骨架；创建离线样例；28 个测试全部通过 | 标的选择层数据结构就绪 |
| 2026-05-31 | Phase 4A Provider 基础设施：实现 ProviderResult/ProviderStatus/ProviderConfig schema；实现 BaseCnStockProvider 抽象基类；实现 RawPayloadStore 原始载荷存储；实现 RateLimiter 统一限速器；实现 ProviderRegistry 供应器注册中心；实现 LocalHotlistProvider 本地热榜供应器；实现 ProviderResult→DataStatus 转换；创建 cn_stock_providers.yaml 配置；创建 THIRD_PARTY_NOTICES.md；30 个测试全部通过 | 数据供应器基础设施就绪 |
| 2026-05-31 | Phase 4A.1 Provider 文档同步：DATA_SOURCES.md 新增"十九、Provider Adapter 基础设施"章节（总原则/标准字段/Raw Payload 规则/DataStatus 转换/RateLimiter/Registry/Planned Providers）；REPORTS.md 新增"七、Provider 数据使用规则"章节（数据链路要求/Provider Failed 规则/Attention Pool 限制/报告降级规则）；PROJECT_HANDOFF.md Phase 4A 补充未调用真实 API 说明和下一步建议；457 个测试全部通过 | Phase 4A 文档同步完成 |
| 2026-05-31 | Phase 4B mootdx 行情 Provider v0.1：实现 MootdxProvider（继承 BaseCnStockProvider）；支持 daily_kline/minute_kline/index_kline/realtime_quote/order_book 5 个 dataset；实现 lazy import mootdx；mootdx 未安装时优雅返回 failed；实现 symbol 规范化和市场推断；接入 RateLimiter；RawPayloadStore 保存原始载荷；ProviderResult→DataStatus 转换；创建 smoke_test_mootdx_provider.py（需手动 --allow-network）；34 个 mock 单元测试全部通过；mootdx 加入 pyproject.toml 依赖；cn_stock_providers.yaml 更新为 partial_implemented | 第一个真实外部数据源接入 |
| 2026-05-31 | Phase 4C Tencent Provider 骨架：实现 TencentProvider（继承 BaseCnStockProvider）；支持 valuation/market_cap/turnover_rate/limit_price 4 个 dataset；当前返回 not_implemented；接入 RateLimiter；RawPayloadStore 集成；cn_stock_providers.yaml 更新为 skeleton；15 个 mock 测试全部通过 | 腾讯估值数据骨架就绪 |
| 2026-05-31 | Phase 4D Cninfo 巨潮公告 Provider 骨架：实现 CninfoProvider（继承 BaseCnStockProvider）；支持 announcement dataset；当前返回 not_implemented；接入 RateLimiter；RawPayloadStore 集成；cn_stock_providers.yaml 更新为 skeleton；16 个 mock 测试全部通过；公告失败时 error_message 提及"无重大利空"影响 | 公告数据骨架就绪 |
| 2026-05-31 | Phase 4B.1 mootdx 字段校验基础设施：创建 FIELD_CHECKLIST.md；创建 docs/data_samples/mootdx/README.md；smoke test 默认不联网；未运行真实联网 smoke test | 字段校验基础设施就绪 |

---

## 二十、给 opencode 的特别说明

### 20.0 重要前提

> **PROJECT_HANDOFF.md 是项目事实源，但不是最终需求冻结文档。** 后续 ChatGPT 会继续根据用户反馈修正文档和开发计划。opencode 不应因为文档中出现某个规划，就主动实现未被明确下达的功能。

### 20.1 读取本文档后的行动指南

1. **首先**：完整阅读本文档，理解项目定位、角色分工、核心原则
2. **然后**：扫描项目目录结构，确认本文档中的"当前项目结构"是否准确
3. **接着**：等待用户转发 ChatGPT 的指令
4. **执行时**：严格遵守"核心原则"章节的所有约束
5. **执行后**：检查 PROJECT_HANDOFF.md 是否需要更新

### 20.2 禁止事项

- ❌ 不得自行决定产品方向或架构变更
- ❌ 不得删除 PROJECT_HANDOFF.md 中的任何已有内容（除非用户或 ChatGPT 明确要求）
- ❌ 不得编造数据或实现状态
- ❌ 不得在没有明确指令的情况下创建新的业务逻辑文件
- ❌ 不得修改核心原则

### 20.3 必须事项

- ✅ 每次执行后必须汇报结果
- ✅ 每次执行后必须检查文档是否需要更新
- ✅ 遇到不确定的问题必须主动提出
- ✅ 发现代码和文档不一致必须提醒用户
- ✅ 保持 PROJECT_HANDOFF.md 的实时性

---

**文档结束。**

> 本文档由 opencode 于 2026-05-31 创建，2026-05-31 首次更新（Phase 1 文档创建）。
> 下次更新时机：Phase 2 开始时，或 ChatGPT 下达新指令时。
