# 遗留项目数据迁移方案

> 本文档设计旧项目数据迁移到新项目的方案。
> 迁移时间：待确认
> 迁移状态：方案设计完成，待用户确认后执行

---

## 一、迁移范围

### 1.1 建议迁移的数据

| 数据 | 来源 | 目标路径 | 优先级 |
|------|------|----------|--------|
| 热榜 JSONL（19天） | tradingagents-old/data/hotlists/ | data/manual_hotlists/legacy_import/raw/ | 高 |
| 票池 active.json | tradingagents-old/data/hot_pool/ | data/manual_hotlists/legacy_import/structured/ | 高 |
| 股票名称映射 | stock-pool/stock_names.json | data/manual_hotlists/legacy_import/audit/ | 高 |
| 报告样例 | tradingagents-old/reports/ | docs/legacy_audit/reports/ | 中 |
| 规则文档 | tradingagents-old/MEMORY/ | docs/legacy_audit/rules/ | 中 |

### 1.2 不建议迁移的数据

| 数据 | 原因 |
|------|------|
| 旧项目代码 | 逻辑混乱，只能参考，不能直接复制 |
| 旧项目配置 | 与新项目配置体系不兼容 |
| 市场情绪数据 | 格式和用途需要进一步确认 |
| 观察列表 | 格式和用途需要进一步确认 |
| 行情数据 | 需要确认数据完整性 |

---

## 二、迁移目标目录

```
data/manual_hotlists/legacy_import/
├─ raw/                    # 原始热榜 JSONL 文件
│  ├─ 2025-05-27.jsonl
│  ├─ 2026-04-22.jsonl
│  └─ ...
├─ structured/             # 结构化票池数据
│  └─ active.json
└─ audit/                  # 审计和辅助数据
   └─ stock_names.json
```

---

## 三、迁移步骤

### 3.1 步骤 1：复制热榜 JSONL 文件

**操作：**
```bash
# 复制所有 JSONL 文件到 legacy_import/raw/
cp C:\github\tradingagents-old\data\hotlists\*.jsonl C:\github\TradingAgents\data\manual_hotlists\legacy_import\raw\
```

**注意事项：**
- 保留原始文件名（YYYY-MM-DD.jsonl）
- 不修改文件内容
- 记录复制时间

### 3.2 步骤 2：复制票池 active.json

**操作：**
```bash
# 复制 active.json 到 legacy_import/structured/
cp C:\github\tradingagents-old\data\hot_pool\active.json C:\github\TradingAgents\data\manual_hotlists\legacy_import\structured\
```

**注意事项：**
- 保留原始文件名
- 不修改文件内容

### 3.3 步骤 3：复制股票名称映射

**操作：**
```bash
# 复制 stock_names.json 到 legacy_import/audit/
cp C:\github\stock-pool\stock_names.json C:\github\TradingAgents\data\manual_hotlists\legacy_import\audit\
```

**注意事项：**
- 保留原始文件名
- 不修改文件内容

### 3.4 步骤 4：创建迁移审计日志

**操作：**
创建 `data/manual_hotlists/legacy_import/migration_log.md`，记录：
- 迁移时间
- 迁移文件列表
- 数据来源
- 数据质量检查结果
- 已知问题

---

## 四、数据处理规则

### 4.1 日期重复处理

**场景：** 用户后续又录入了与旧数据相同日期的热榜

**处理规则：**
1. 旧数据保留在 `legacy_import/raw/` 目录
2. 新数据保存在 `data/manual_hotlists/raw_text/` 目录
3. 系统优先使用新数据
4. 如果需要合并，需要人工确认

### 4.2 缺少股票代码的记录

**场景：** 少数记录的 name 字段为空

**处理规则：**
1. 保留原始记录
2. 在 `audit/` 目录创建缺失列表
3. 后续可以通过 stock_names.json 补全

### 4.3 平台名称不统一

**场景：** 旧数据使用中文平台名称（同花顺/东方财富/雪球/通达信）

**处理规则：**
1. 保留原始中文名称
2. 在系统中建立中文→英文映射：
   - 同花顺 → tonghuashun
   - 东方财富 → eastmoney
   - 雪球 → xueqiu
   - 通达信 → tongdaxin

### 4.4 跨平台重复股票

**场景：** 同一股票出现在多个平台

**处理规则：**
1. 保留所有记录（不做跨平台去重）
2. 在 Attention Pool 中通过 appearances 字段计算多平台共振
3. 跨平台出现次数越多，权重越高

### 4.5 历史规则与当前规则冲突

**场景：** 旧项目有"每榜取10只主板"规则，新项目改为"全量录入"

**处理规则：**
1. **以新规则为准**
2. 旧数据中的非主板股票保留，不删除
3. 旧数据中的主板标记保留，但不作为筛选依据
4. 系统分析时使用新规则

---

## 五、溯源信息

### 5.1 必须保留的溯源字段

每条迁移数据必须包含以下溯源信息：

| 字段 | 说明 | 示例 |
|------|------|------|
| original_path | 原始文件路径 | C:\github\tradingagents-old\data\hotlists\2026-05-28.jsonl |
| source_project | 来源项目 | tradingagents-old |
| imported_at | 迁移时间 | 2026-05-31T19:20:00 |
| migration_version | 迁移版本 | v1 |

### 5.2 实现方式

在 `data/manual_hotlists/legacy_import/migration_log.md` 中记录：

```markdown
## 迁移记录

### 2026-05-31 v1

- 来源项目：tradingagents-old
- 迁移文件：
  - hotlists/2025-05-27.jsonl
  - hotlists/2026-04-22.jsonl
  - ...
- 迁移时间：2026-05-31T19:20:00
- 备注：原始数据保留，未修改
```

---

## 六、数据验证

### 6.1 迁移后验证清单

| 检查项 | 预期结果 | 验证方式 |
|--------|----------|----------|
| 文件数量 | 19 个 JSONL 文件 | `ls data/manual_hotlists/legacy_import/raw/` |
| 文件格式 | JSONL，每行一条 JSON | 抽样读取 |
| 字段完整性 | date/source/ticker/name/main_board | 抽样读取 |
| 日期覆盖 | 2025-05-27 到 2026-05-28 | 检查文件名 |
| 平台覆盖 | 同花顺/东方财富/雪球/通达信 | 抽样读取 |
| 票池文件 | active.json 存在 | 检查文件 |
| 股票名称映射 | stock_names.json 存在 | 检查文件 |

### 6.2 验证命令

```bash
# 检查文件数量
ls data/manual_hotlists/legacy_import/raw/*.jsonl | wc -l

# 检查最新文件
head -5 data/manual_hotlists/legacy_import/raw/2026-05-28.jsonl

# 检查票池文件
head -20 data/manual_hotlists/legacy_import/structured/active.json
```

---

## 七、后续工作

### 7.1 短期（迁移后立即执行）

1. 验证数据完整性
2. 创建迁移审计日志
3. 更新 PROJECT_HANDOFF.md 记录迁移状态

### 7.2 中期（Phase 2 实现时）

1. 开发热榜解析器，支持读取 legacy_import 数据
2. 将 legacy_import 数据导入 Attention Pool
3. 验证 Attention Pool 生成结果

### 7.3 长期（系统稳定后）

1. 考虑是否需要定期从 legacy_import 同步到新系统
2. 考虑是否需要保留 legacy_import 目录或合并到新目录

---

## 八、风险和缓解

### 8.1 数据风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 数据格式不兼容 | 无法导入 | 保留原始文件，可重新解析 |
| 日期重复 | 数据混乱 | 新数据优先，旧数据保留 |
| 字段缺失 | 功能受限 | 标注缺失，后续补全 |

### 8.2 流程风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 迁移过程中断 | 数据不完整 | 迁移前备份，支持断点续传 |
| 误修改原始数据 | 数据丢失 | 只读复制，不修改原文件 |
| 迁移后无法回滚 | 数据混乱 | 保留原始文件，可随时回滚 |

---

## 九、执行计划

### 9.1 执行前提

- [ ] 用户确认迁移范围
- [ ] 用户确认迁移日期
- [ ] 用户确认是否需要人工审核

### 9.2 执行步骤

1. 创建迁移审计日志
2. 复制热榜 JSONL 文件
3. 复制票池 active.json
4. 复制股票名称映射
5. 验证数据完整性
6. 更新 PROJECT_HANDOFF.md

### 9.3 执行时间

**建议执行时间：** 用户确认后立即执行

**预计耗时：** 5-10 分钟

---

**文档结束。**

> 本文档由 opencode 于 2026-05-31 创建。
> 待用户确认后执行迁移。
