# 发展潜力评分模型

语言：[English](scoring_model.md) · [Русский](scoring_model.ru.md) · **简体中文**

> 本文件由 `python tools/gen_scoring_doc.py` 根据 `config/scoring_model.json` 生成。请修改 JSON 后重新生成。

## 用途与使用方法

模型把对产品的定性判断转化为**可比较的0–100分**，并给出不确定区间和红旗清单。它是一种纪律而非“真理”：
每个分数都要有锚点（该维度“3分”具体指什么）和证据等级（A/B/C）。

1. 根据事实确定**阶段**（`idea` / `prototype` / `pilot` / `growth`）：想法——没有可运行的成果；原型——TRL 4–6，
   无付费用户；试点——至少一个外部试点、首笔收入或意向书；增长——可复制的销售，按月衡量ARR和留存。
2. 确定**受众**（`investor` / `government` / `corporate` / `academic`）：受众改变权重（第7节）和演示结构（第9节）。
3. 确定**市场画像**（`ru`、`en`、`zh`、`vn`、`id`、`my`，默认随语言区域）：调整部分权重，重新定义“合规与自主可控”
   维度，并启用市场特定的红旗规则（第10节，`markets/*.md`）。
4. 填写 `scoring_input.json`（`templates/zh/` 或 `python tools/scoring.py template`）：每个维度0–5分（可用半分）、
   证据等级、附事实和链接的一句话依据。
5. 运行 `python tools/scoring.py --input scoring_input.json --locale zh [--market zh]`。`run_pipeline.py` 还会计算全部四种受众画像。

公式：`总分 = Σ(权重_i × 得分_i / 5)`，权重 = 阶段画像 × 受众系数 × 市场系数，归一化为100。区间：
`Σ 权重_i × (得分_i ± 区间_i) / 5`，A = 0，B = 0.5，C = 1.0。

## 1. 基础权重（合计100）及依据

| # | id | 维度 | 权重 | 依据（英文） |
|---|---|---|---:|---|
| 1 | `market` | 市场规模与增长 | **14** | Caps the upside; every audience asks 'how big can this get'. Highest single weight because every other criterion is multiplied by the size of the prize. Absolute SAM thresholds are set per market profile (currency-specific). |
| 2 | `problem` | 问题严重性与付费意愿 | **12** | Painful, budgeted problems shorten sales cycles; 'nice-to-have' kills B2B and B2G products regardless of tech quality. |
| 3 | `trl` | 产品与技术成熟度（TRL） | **10** | Separates research from product. Mapped to the TRL scale (and national equivalents, e.g. ГОСТ Р 58048-2017 in Russia) so that grant committees and corporates read it the same way. |
| 4 | `moat` | 差异化、壁垒与知识产权 | **10** | Determines whether margins survive competition from big platforms and open-source models. |
| 5 | `team` | 团队与执行能力 | **10** | Early-stage outcomes track team quality; government and academic audiences also weigh institutional backing. |
| 6 | `traction` | 市场验证与证据 | **10** | Converts claims into evidence: users, revenue, pilots, LOIs, retention. |
| 7 | `unit_economics` | 商业模式与单位经济 | **9** | Shows growth will create rather than burn value: gross margin, LTV/CAC, payback. |
| 8 | `gtm` | 市场进入与渠道 | **7** | B2B/B2G sales cycles are long; a named channel (integrator, marketplace, procurement route) matters more than ads. |
| 9 | `regulatory` | 合规与技术自主 | **7** | Data-protection, security certification and supply-chain sovereignty requirements are entry tickets for public-sector, regulated and critical-infrastructure buyers. The concrete regimes differ by market and are defined in market_profiles. |
| 10 | `scalability` | 可扩展性与出海潜力 | **5** | Measures the option value beyond the first market: replicability across sectors and accessible export markets (defined per market profile). |
| 11 | `risk` | 风险状况（5 = 低风险） | **6** | Inverse criterion: concentration, dependency, technology, financing and regulatory risk after mitigants. |
| | | **合计** | **100** | |

## 2. 0–5分锚定量表

量表: 0 = 无证据/不存在；5 = 同类最佳且有可核实证据。允许半分。

### 市场规模与增长 (`market`, 权重 14)

| 分数 | 锚点 | Anchor (EN) |
|---:|---|---|
| 0 | 无可识别的付费市场 | no identifiable paying market |
| 1 | SAM很小或市场萎缩 | very small SAM or shrinking market |
| 2 | SAM较小，年增长 < 5% | small SAM, growth < 5%/yr |
| 3 | SAM中等，年增长 5–15% | mid-size SAM, growth 5–15% |
| 4 | SAM较大或年增长 15–30%，自下而上已验证 | large SAM or growth 15–30%, bottom-up confirmed |
| 5 | SAM很大且年增长 > 20%，自上而下与自下而上交叉验证 | very large SAM and growth > 20%, triangulated top-down + bottom-up |

**红旗:** TAM quoted from a generic 'global AI market' figure; no bottom-up check; CAGR from a single press release

### 问题严重性与付费意愿 (`problem`, 权重 12)

| 分数 | 锚点 | Anchor (EN) |
|---:|---|---|
| 0 | 问题未经验证 | problem not validated |
| 1 | 零星反馈，无预算负责人 | anecdotal pain, no budget owner |
| 2 | < 10 次访谈确认痛点，预算不明 | pain confirmed in < 10 interviews, unclear budget |
| 3 | ≥ 20 次访谈，明确预算负责人，替代方案成本已量化 | ≥ 20 interviews, named budget owner, workaround cost quantified |
| 4 | 客户目前已为替代方案付费；量化损失 > 价格的10倍 | customers pay for workarounds today; quantified loss > 10x price |
| 5 | 关键业务 / 监管强制要求；客户预付或共同出资 | mission-critical / regulatory mandate; customers pre-pay or co-fund |

**红旗:** problem described only in the team's words; buyer ≠ user and buyer not interviewed

### 产品与技术成熟度（TRL） (`trl`, 权重 10)

| 分数 | 锚点 | Anchor (EN) |
|---:|---|---|
| 0 | TRL 1–2：仅有概念 | TRL 1–2: concept only |
| 1 | TRL 3：原理验证（PoC） | TRL 3: proof of concept |
| 2 | TRL 4–5：在相关环境中验证 | TRL 4–5: validation in a relevant environment |
| 3 | TRL 6：基于真实数据的原型演示 | TRL 6: prototype demonstrated with real data |
| 4 | TRL 7–8：系统在客户环境运行并通过鉴定 | TRL 7–8: system in customer operation, qualified |
| 5 | TRL 9：在多个客户处常态化运行 | TRL 9: proven in routine operation at several customers |

**红旗:** demo is scripted / not on customer data; claimed TRL above evidence

### 差异化、壁垒与知识产权 (`moat`, 权重 10)

| 分数 | 锚点 | Anchor (EN) |
|---:|---|---|
| 0 | 同质化产品，易被复制 | commodity; easily replicated |
| 1 | 仅功能层面差异 | feature-level difference only |
| 2 | 在1–2个可测量维度上优于替代方案 | better on 1–2 measured dimensions vs. alternatives |
| 3 | 可测量的优势 + 专有数据或流程嵌入 | measured advantage + proprietary data or workflow lock-in |
| 4 | 多重相互强化的壁垒（数据、集成、资质认证、已登记知识产权） | several reinforcing moats (data, integrations, certifications, registered IP) |
| 5 | 结构性壁垒：网络效应 / 独家数据 / 受监管保护的地位 | structural moat: network effects / exclusive data / regulation-backed position |

**红旗:** thin wrapper over a third-party model without a proprietary data advantage; 'no competitors' claim

### 团队与执行能力 (`team`, 权重 10)

| 分数 | 锚点 | Anchor (EN) |
|---:|---|---|
| 0 | 无专职团队 | no dedicated team |
| 1 | 兼职团队，缺少关键能力 | part-time team, key skills missing |
| 2 | 有技术核心，无商业负责人 | core technical team, no commercial lead |
| 3 | 核心团队完整，具备行业经验 | complete core team, relevant domain track record |
| 4 | 团队曾交付并销售过类似产品；顾问可提供渠道 | team has shipped & sold similar products; advisors with access |
| 5 | 连续创业者 / 领先研究团队 + 经过验证的商业管理者 | repeat founders / leading research group + proven commercial executives |

**红旗:** single point of failure (one developer); no one owns sales

### 市场验证与证据 (`traction`, 权重 10)

| 分数 | 锚点 | Anchor (EN) |
|---:|---|---|
| 0 | 无 | none |
| 1 | 仅有等候名单 / 意向 | waitlist / interest only |
| 2 | 1–2个免费试点或意向书 | 1–2 unpaid pilots or LOIs |
| 3 | 付费试点或 ≥ 3份意向书；有使用数据 | paid pilots or ≥ 3 LOIs; usage data |
| 4 | 经常性收入，≥ 5家付费客户，有留存数据 | recurring revenue, ≥ 5 paying customers, retention data |
| 5 | 经常性收入快速增长（同比 > 2倍），NRR ≥ 110% | fast-growing recurring revenue (> 2x YoY) with NRR ≥ 110% |

**红旗:** pilots that never convert; vanity metrics (registrations, downloads) without usage

### 商业模式与单位经济 (`unit_economics`, 权重 9)

| 分数 | 锚点 | Anchor (EN) |
|---:|---|---|
| 0 | 无商业模式 | no model |
| 1 | 定价未确定 | pricing undefined |
| 2 | 已定价，毛利未知 | pricing defined, margins unknown |
| 3 | 毛利率 ≥ 50%，估算 LTV/CAC ≥ 2 | GM ≥ 50%, LTV/CAC estimated ≥ 2 |
| 4 | 毛利率 ≥ 70%，LTV/CAC ≥ 3，回收期 ≤ 18个月（实测） | GM ≥ 70%, LTV/CAC ≥ 3, payback ≤ 18 mo (measured) |
| 5 | 毛利率 ≥ 80%，LTV/CAC ≥ 5，回收期 ≤ 12个月，烧钱倍数 < 1.5 | GM ≥ 80%, LTV/CAC ≥ 5, payback ≤ 12 mo, burn multiple < 1.5 |

**红旗:** LTV computed with < 2% monthly churn assumption without data; inference/compute costs ignored in COGS

### 市场进入与渠道 (`gtm`, 权重 7)

| 分数 | 锚点 | Anchor (EN) |
|---:|---|---|
| 0 | 无计划 | no plan |
| 1 | 笼统计划（“营销、合作伙伴”） | generic plan ('marketing, partners') |
| 2 | 已明确目标细分市场和理想客户画像 | target segment and ICP defined |
| 3 | 找到首个可复制渠道，已测量销售周期 | repeatable first channel identified, sales cycle measured |
| 4 | 2个以上有效渠道，与集成商签约，采购路径清晰 | 2+ working channels, partner/integrator agreements, procurement route clear |
| 5 | 高效可扩展的销售体系（magic number > 0.75），已验证“先落地后扩展” | efficient scalable engine (magic number > 0.75), land-and-expand proven |

**红旗:** relying on a single anchor customer; no understanding of public/enterprise procurement rules

### 合规与技术自主 (`regulatory`, 权重 7)

| 分数 | 锚点 | Anchor (EN) |
|---:|---|---|
| 0 | 受阻：关键组件依赖外部且无替代 | blocked: critical dependency on a component that cannot be used in the target market, no substitute |
| 1 | 存在重大合规缺口 | major compliance gaps |
| 2 | 合规路径已知，尚未启动 | compliance path known, not started |
| 3 | 合规进行中，技术栈可控 | compliance in progress, controllable stack |
| 4 | 满足目标客户的数据与安全要求 | meets data & security requirements of target buyers |
| 5 | 合规完备 + 资质认证 + 纳入行业或政策项目 | full compliance + certifications + listed in sector / policy programmes |

**红旗:** third-party cloud/LLM API in the critical path where buyers require local processing; personal data processed outside the permitted jurisdiction

### 可扩展性与出海潜力 (`scalability`, 权重 5)

| 分数 | 锚点 | Anchor (EN) |
|---:|---|---|
| 0 | 每次都是定制项目 | custom project each time |
| 1 | 每个客户需大量定制 | heavy customization per client |
| 2 | 可配置产品，单一行业 | configurable product, single sector |
| 3 | 多行业产品，单客户边际成本低 | multi-sector product, marginal cost per client low |
| 4 | 已针对 ≥ 1个海外市场本地化，并有合作伙伴 | localized for ≥ 1 export market, partner identified |
| 5 | 已有海外收入或平台型经济 | proven export revenue or platform/marketplace economics |

**红旗:** export plan to markets where local compliance blocks distribution

### 风险状况（5 = 低风险） (`risk`, 权重 6)

| 分数 | 锚点 | Anchor (EN) |
|---:|---|---|
| 0 | 存在未缓解的生存性风险 | existential risks unmitigated |
| 1 | 多项高风险，缓解措施薄弱 | several high risks, weak mitigants |
| 2 | 高风险但有可行的缓解措施 | high risks with plausible mitigants |
| 3 | 中等剩余风险，缓解措施已有资金保障 | medium residual risk, mitigants funded |
| 4 | 剩余风险低，客户和供应商分散 | low residual risk, diversified customers & suppliers |
| 5 | 剩余风险极低，有合同保护，现金可支撑 > 24个月 | minimal residual risk, contractual protections, cash > 24 mo |

**红旗:** runway < 6 months; > 50% revenue from one customer

## 3. 证据等级

| 等级 | 含义 | 可信度 | 分数区间 |
|---|---|---:|---|
| A | 已核实（审计数据、已签合同、日志、同行评审） | 1.00 | ±0 |
| B | 可信估计（试点数据、意向书、可靠第三方来源） | 0.75 | ±0.5 |
| C | 假设 / 团队自述 | 0.40 | ±1.0 |

总体可信度为按权重加权的平均值。总分区间由各维度区间计算——请与分数一同展示（如“64分，区间55–73”）。

## 4. 评级区间

| 评级 | 门槛 | 含义 |
|---|---:|---|
| A | ≥ 80 | 强 — 优先 / 投资 |
| B | ≥ 65 | 有潜力 — 有条件支持 |
| C | ≥ 50 | 有条件 — 先补齐具体短板 |
| D | ≥ 35 | 弱 — 重新梳理思路 |
| E | ≥ 0 | 目前不可行 |

## 5. 自动红旗规则

| id | 类型 | 严重程度 | 市场 | 提示 |
|---|---|---|---|---|
| `critical_gap` | score_below_with_weight | high | 全部 | 关键短板：高权重维度得分 ≤ 1 |
| `trl_stage_mismatch` | stage_trl | high | 全部 | 所述阶段（试点/增长）与较低的技术成熟度不符 |
| `ltv_cac` | fact_below | high | 全部 | LTV/CAC < 1：增长在毁灭价值 |
| `ltv_cac_soft` | fact_below | medium | 全部 | LTV/CAC 低于 3 |
| `runway` | fact_below | high | 全部 | 现金跑道 < 6个月 |
| `concentration` | fact_above | medium | 全部 | 单一客户贡献 > 50% 收入 |
| `registry_gov` | fact_false_for_audience | high | ru | 面向俄罗斯政府/关键信息基础设施客户，但无法列入俄罗斯软件登记册 |
| `low_confidence` | confidence_below | medium | 全部 | 证据可信度 < 60%：多数评分基于假设 |
| `foreign_dependency` | fact_true | high | 全部 | 核心路径存在对外部或可能受限组件的关键依赖 |
| `xinchuang_gov` | fact_false_for_audience | high | zh | 面向政府/国企客户，但未完成信创适配 |
| `mlps_gov` | fact_false_for_audience | medium | zh | 面向政府/关键行业客户的系统尚未完成等保2.0测评 |
| `genai_filing` | fact_true | high | zh | 面向公众的生成式人工智能服务尚未完成算法备案/服务备案 |
| `cross_border_data` | fact_true | high | zh, ru, en, vn, id, my | 个人信息出境未完成规定的评估或未具备合法依据 |
| `enterprise_security` | fact_false_for_audience | medium | en | 面向企业客户销售，但无 SOC 2 / ISO 27001 认证（或可信计划） |
| `fedramp_gov` | fact_false_for_audience | medium | en | 面向美国联邦客户，但云服务无 FedRAMP 授权路径 |
| `ai_risk` | fact_true | medium | en | 向美国企业或联邦客户销售AI功能，但未形成书面的AI风险评估（如 NIST AI RMF） |
| `vn_pdp_dossier` | fact_false_for_audience | medium | vn | 未编制个人数据处理影响评估档案（越南第91/2025/QH15号法律） |
| `id_pse` | fact_false_for_audience | high | id | 在印度尼西亚提供服务但未完成电子系统运营者（PSE）登记 |
| `id_tkdn` | fact_false_for_audience | high | id | 面向政府/国企采购但无 TKDN（本地成分）证书 |
| `my_pdpa` | fact_false_for_audience | medium | my | 未证明符合《2010年个人数据保护法》（2024年修订）（如数据保护官、泄露通知、处理者义务） |

高严重度红旗不会将分数清零，但必须写入风险页和报告“风险”章节并给出应对措施。两个及以上高严重度红旗 → 无论分数多少，建议最高为“有条件（C）”。

## 6. 阶段画像（合计100）

| 维度 | idea | prototype | pilot | growth |
|---|---:|---:|---:|---:|
| 市场规模与增长 | 16 | 14 | 13 | 12 |
| 问题严重性与付费意愿 | 16 | 13 | 11 | 8 |
| 产品与技术成熟度（TRL） | 6 | 12 | 11 | 6 |
| 差异化、壁垒与知识产权 | 10 | 11 | 10 | 10 |
| 团队与执行能力 | 16 | 13 | 9 | 8 |
| 市场验证与证据 | 4 | 7 | 13 | 16 |
| 商业模式与单位经济 | 5 | 6 | 10 | 15 |
| 市场进入与渠道 | 7 | 7 | 8 | 10 |
| 合规与技术自主 | 7 | 7 | 7 | 6 |
| 可扩展性与出海潜力 | 6 | 5 | 4 | 6 |
| 风险状况（5 = 低风险） | 7 | 5 | 4 | 3 |
| **合计** | 100 | 100 | 100 | 100 |

权重变化逻辑：想法阶段只能评估市场、问题和团队；试点阶段权重转向证据（牵引力、单位经济）；增长阶段转向效率（单位经济、市场进入），技术风险基本消除。

## 7. 受众系数

系数乘以阶段权重，然后重新归一化为100。

| 维度 | investor | government | corporate | academic |
|---|---:|---:|---:|---:|
| 市场规模与增长 | 1.2 | 0.9 | 0.8 | 0.7 |
| 问题严重性与付费意愿 | 1 | 1 | 1.3 | 1 |
| 产品与技术成熟度（TRL） | 0.9 | 1.2 | 1.3 | 1.3 |
| 差异化、壁垒与知识产权 | 1 | 1 | 0.9 | 1.4 |
| 团队与执行能力 | 1 | 1.1 | 1 | 1.3 |
| 市场验证与证据 | 1.2 | 1 | 1 | 0.7 |
| 商业模式与单位经济 | 1.3 | 0.6 | 0.8 | 0.5 |
| 市场进入与渠道 | 1 | 1 | 1.1 | 0.6 |
| 合规与技术自主 | 0.8 | 1.6 | 1.2 | 1 |
| 可扩展性与出海潜力 | 1.2 | 1.1 | 1 | 1 |
| 风险状况（5 = 低风险） | 1 | 1.1 | 1 | 1 |

## 8. 有效权重：阶段 × 受众（默认市场）

由 `scoring.py`（`weights_for`）生成。每列合计100。

### 受众: investor

| 维度 | idea | prototype | pilot | growth |
|---|---:|---:|---:|---:|
| 市场规模与增长 | 18.3 | 16.1 | 14.6 | 13.2 |
| 问题严重性与付费意愿 | 15.3 | 12.5 | 10.3 | 7.3 |
| 产品与技术成熟度（TRL） | 5.2 | 10.3 | 9.3 | 4.9 |
| 差异化、壁垒与知识产权 | 9.6 | 10.5 | 9.4 | 9.1 |
| 团队与执行能力 | 15.3 | 12.5 | 8.5 | 7.3 |
| 市场验证与证据 | 4.6 | 8.0 | 14.6 | 17.5 |
| 商业模式与单位经济 | 6.2 | 7.5 | 12.2 | 17.8 |
| 市场进入与渠道 | 6.7 | 6.7 | 7.5 | 9.1 |
| 合规与技术自主 | 5.3 | 5.4 | 5.3 | 4.4 |
| 可扩展性与出海潜力 | 6.9 | 5.7 | 4.5 | 6.6 |
| 风险状况（5 = 低风险） | 6.7 | 4.8 | 3.8 | 2.7 |
| **合计** | 100 | 100 | 100 | 100 |

### 受众: government

| 维度 | idea | prototype | pilot | growth |
|---|---:|---:|---:|---:|
| 市场规模与增长 | 13.8 | 12.0 | 11.4 | 10.9 |
| 问题严重性与付费意愿 | 15.3 | 12.4 | 10.7 | 8.1 |
| 产品与技术成熟度（TRL） | 6.9 | 13.7 | 12.8 | 7.3 |
| 差异化、壁垒与知识产权 | 9.6 | 10.5 | 9.7 | 10.1 |
| 团队与执行能力 | 16.8 | 13.6 | 9.6 | 8.9 |
| 市场验证与证据 | 3.8 | 6.7 | 12.6 | 16.1 |
| 商业模式与单位经济 | 2.9 | 3.4 | 5.8 | 9.1 |
| 市场进入与渠道 | 6.7 | 6.7 | 7.8 | 10.1 |
| 合规与技术自主 | 10.7 | 10.7 | 10.9 | 9.7 |
| 可扩展性与出海潜力 | 6.3 | 5.2 | 4.3 | 6.6 |
| 风险状况（5 = 低风险） | 7.4 | 5.2 | 4.3 | 3.3 |
| **合计** | 100 | 100 | 100 | 100 |

### 受众: corporate

| 维度 | idea | prototype | pilot | growth |
|---|---:|---:|---:|---:|
| 市场规模与增长 | 12.4 | 10.7 | 10.1 | 9.6 |
| 问题严重性与付费意愿 | 20.1 | 16.2 | 13.9 | 10.4 |
| 产品与技术成熟度（TRL） | 7.5 | 14.9 | 13.9 | 7.8 |
| 差异化、壁垒与知识产权 | 8.7 | 9.5 | 8.7 | 9.0 |
| 团队与执行能力 | 15.5 | 12.4 | 8.7 | 8.0 |
| 市场验证与证据 | 3.9 | 6.7 | 12.6 | 16.0 |
| 商业模式与单位经济 | 3.9 | 4.6 | 7.8 | 12.0 |
| 市场进入与渠道 | 7.4 | 7.4 | 8.5 | 11.0 |
| 合规与技术自主 | 8.1 | 8.0 | 8.1 | 7.2 |
| 可扩展性与出海潜力 | 5.8 | 4.8 | 3.9 | 6.0 |
| 风险状况（5 = 低风险） | 6.8 | 4.8 | 3.9 | 3.0 |
| **合计** | 100 | 100 | 100 | 100 |

### 受众: academic

| 维度 | idea | prototype | pilot | growth |
|---|---:|---:|---:|---:|
| 市场规模与增长 | 11.3 | 9.8 | 9.7 | 9.5 |
| 问题严重性与付费意愿 | 16.1 | 13.0 | 11.7 | 9.1 |
| 产品与技术成熟度（TRL） | 7.9 | 15.6 | 15.2 | 8.8 |
| 差异化、壁垒与知识产权 | 14.1 | 15.4 | 14.9 | 15.9 |
| 团队与执行能力 | 20.9 | 16.9 | 12.4 | 11.8 |
| 市场验证与证据 | 2.8 | 4.9 | 9.7 | 12.7 |
| 商业模式与单位经济 | 2.5 | 3.0 | 5.3 | 8.5 |
| 市场进入与渠道 | 4.2 | 4.2 | 5.1 | 6.8 |
| 合规与技术自主 | 7.0 | 7.0 | 7.4 | 6.8 |
| 可扩展性与出海潜力 | 6.0 | 5.0 | 4.3 | 6.8 |
| 风险状况（5 = 低风险） | 7.0 | 5.0 | 4.3 | 3.4 |
| **合计** | 100 | 100 | 100 | 100 |

## 9. 各受众的演示章节权重（合计100）

`allocate_slides()` 用其分配页数和演讲时间。

| 章节 | investor | government | corporate | academic |
|---|---:|---:|---:|---:|
| 核心结论 / 论点 | 8 | 8 | 8 | 8 |
| 问题与时机 | 8 | 10 | 12 | 10 |
| 解决方案 / 产品与演示 | 8 | 7 | 12 | 8 |
| 市场规模（TAM/SAM/SOM） | 10 | 6 | 4 | 4 |
| 技术与成熟度 | 4 | 10 | 10 | 16 |
| 市场验证与证据 | 12 | 5 | 8 | 4 |
| 商业模式与单位经济 | 10 | 3 | 6 | 2 |
| 竞争与壁垒 | 7 | 5 | 5 | 8 |
| 市场进入 | 6 | 4 | 6 | 2 |
| 财务计划与回报 | 10 | 6 | 4 | 3 |
| 团队 | 7 | 8 | 5 | 10 |
| 合规与自主可控 | 2 | 12 | 7 | 4 |
| 风险与应对 | 3 | 6 | 5 | 6 |
| 路线图与里程碑 | 2 | 7 | 5 | 10 |
| 融资需求 / 决策事项 | 3 | 3 | 3 | 5 |
| **合计** | 100 | 100 | 100 | 100 |

## 10. 市场画像

市场画像调整所列权重（并重新归一化），替换合规维度的定义和锚点，并列出红旗规则读取的合规事实。法规状态核实日期：2026-10-20；使用前请重新核实。

| id | 市场 | 币种 | 权重系数 | 合规事实 | 指南 |
|---|---|---|---|---|---|
| `ru` | 俄罗斯 | RUB | regulatory ×1.15 | `registry_eligible`, `critical_foreign_dependency`, `cross_border_data_unassessed` | [markets/ru.md](markets/ru.md) |
| `en` | 美国 | USD | regulatory ×0.85 | `security_attestation`, `fedramp_path`, `ai_risk_unassessed`, `cross_border_data_unassessed`, `critical_foreign_dependency` | [markets/en.md](markets/en.md) |
| `zh` | 中国大陆 | CNY | regulatory ×1.25, gtm ×1.1 | `xinchuang_adapted`, `mlps_certified`, `genai_filing_missing`, `cross_border_data_unassessed`, `critical_foreign_dependency` | [markets/zh.md](markets/zh.md) |
| `vn` | 越南 | VND | regulatory ×1.15, gtm ×1.05 | `pdp_impact_assessment`, `cross_border_data_unassessed`, `critical_foreign_dependency` | [markets/vn.md](markets/vn.md) |
| `id` | 印度尼西亚 | IDR | regulatory ×1.15, gtm ×1.1 | `pse_registered`, `tkdn_certified`, `cross_border_data_unassessed`, `critical_foreign_dependency` | [markets/id.md](markets/id.md) |
| `my` | 马来西亚 | MYR | regulatory ×1 | `pdpa_compliant`, `cross_border_data_unassessed`, `critical_foreign_dependency` | [markets/my.md](markets/my.md) |

### `ru` — 合规与技术主权（俄罗斯）

**“合规与自主可控”维度定义.** 俄罗斯软件统一登记册（俄联邦政府2015年第1236号决议）、第152号联邦法《个人数据法》（含本地化）、第187号联邦法（关键信息基础设施）、必要时的FSTEC/FSB认证、第44号/第223号联邦法采购规则。

| 分数 | 锚点 |
|---:|---|
| 0 | 受阻：关键依赖受制裁/外国组件且无替代 |
| 1 | 存在重大合规缺口 |
| 2 | 合规路径已知，尚未启动 |
| 3 | 进行中（申请列入登记册、152号法合规），本国技术栈 |
| 4 | 已列入俄罗斯软件登记册；满足目标客户的数据与安全要求 |
| 5 | 登记册 + 认证 + 纳入进口替代/产业规划 |

### `en` — 合规与安全（美国）

**“合规与自主可控”维度定义.** 州级隐私法（如经 CPRA 修订的加州 CCPA）、企业客户期望的 SOC 2 / ISO/IEC 27001 认证、面向美国联邦机构云服务的 FedRAMP、AI 风险管理（自愿性 NIST AI RMF）、美国出口管制（EAR）与制裁筛查、行业规则（如 HIPAA）。

| 分数 | 锚点 |
|---:|---|
| 0 | 受阻：产品无法满足目标细分市场的强制要求（如受出口管制、行业规则） |
| 1 | 重大缺口（无隐私合规体系或服务提供商条款、无安全体系） |
| 2 | 已制定合规路线图，尚未启动 |
| 3 | 已建立隐私合规体系，SOC 2 Type I / ISO 27001 进行中 |
| 4 | 已获 SOC 2 Type II 或 ISO 27001 认证；已记录 AI 风险评估 |
| 5 | 认证 + FedRAMP/行业授权；合规成为销售优势 |

### `zh` — 合规与自主可控

**“合规与自主可控”维度定义.** 《网络安全法》（2016）、《数据安全法》（2021）、《个人信息保护法》（2021，含数据出境规则）；《生成式人工智能服务管理暂行办法》（2023）及算法备案；网络安全等级保护2.0（GB/T 22239-2019）；面向党政机关和国企客户的信创适配（国产芯片/操作系统/数据库）。

| 分数 | 锚点 |
|---:|---|
| 0 | 受阻：核心依赖无法在中国大陆提供，或数据须出境且无合法路径 |
| 1 | 重大缺口（无个人信息处理合法依据、未做等保测评） |
| 2 | 合规路径已知，尚未启动 |
| 3 | 已落实个人信息保护合规；等保测评/算法备案进行中；已启动信创适配 |
| 4 | 已通过相应等保级别，备案完成，已与主流国产软硬件完成兼容认证 |
| 5 | 全面合规 + 进入政府/行业目录；与政策方向高度契合 |

### `vn` — 合规与数字主权（越南）

**“合规与自主可控”维度定义.** Law on Personal Data Protection No. 91/2025/QH15 (in force 1 Jan 2026; detailed by Decree 356/2025/ND-CP, which replaced Decree 13/2023/ND-CP) incl. impact-assessment dossiers for processing and cross-border transfer; Law on Cybersecurity No. 116/2025/QH15 (in force 1 Jul 2026, replacing the 2018 Cybersecurity Law and the 2015 Law on Cyberinformation Security) incl. information-system security levels; Law on Digital Technology Industry No. 71/2025/QH15 (incentives for digital-technology products and enterprises); Law on Artificial Intelligence No. 134/2025/QH15; public procurement under the Law on Bidding No. 22/2023/QH15.

| 分数 | 锚点 |
|---:|---|
| 0 | blocked: data or core component cannot lawfully be used/processed for the target customers |
| 1 | major gaps (no PDP impact-assessment dossier, no security-level classification) |
| 2 | compliance path known, not started |
| 3 | PDP dossiers prepared; information-system security level determined; local deployment option |
| 4 | PDP and cybersecurity obligations met for target buyers; recognised as a digital-technology product/enterprise where relevant |
| 5 | full compliance + listed in national / ministry digital-transformation programmes |

### `id` — 合规、本地成分与主权（印尼）

**“合规与自主可控”维度定义.** Personal Data Protection Law No. 27/2022 (UU PDP; two-year adjustment period ended Oct 2024); registration as an electronic system operator (PSE) under MR 5/2020 via OSS with the Ministry of Communication and Digital (Komdigi, formerly Kominfo); GR 71/2019 on electronic systems (data-placement rules for public-scope operators); local content (TKDN) certification for government and SOE procurement (Perpres 46/2025, Permenperin 35/2025).

| 分数 | 锚点 |
|---:|---|
| 0 | blocked: cannot register as PSE or meet data-placement rules for target buyers |
| 1 | major gaps (no UU PDP programme, no PSE registration) |
| 2 | compliance path known, not started |
| 3 | PSE registered; UU PDP programme in place; TKDN assessment started |
| 4 | TKDN certified at the level required by target tenders; data and security requirements met |
| 5 | full compliance + listed in e-catalogue / government programmes |

### `my` — 合规与数字信任（马来西亚）

**“合规与自主可控”维度定义.** Personal Data Protection Act 2010 (Act 709) as amended by Act A1727 (2024; phased commencement 1 Jan, 1 Apr and 1 Jun 2025): data controllers and processors, DPO appointment, breach notification, data portability, cross-border transfer; Cyber Security Act 2024 (Act 854, in force 26 Aug 2024) for national critical information infrastructure (NCII) entities, overseen by NACSA; sector rules (e.g. Bank Negara Malaysia RMiT for financial institutions); Malaysia Digital (MD, formerly MSC Malaysia) status for incentives.

| 分数 | 锚点 |
|---:|---|
| 0 | blocked: cannot meet a mandatory requirement of the target sector (e.g. NCII or RMiT obligations) |
| 1 | major gaps (no PDPA programme, no security controls) |
| 2 | compliance path known, not started |
| 3 | PDPA programme incl. DPO and breach process; security controls in progress |
| 4 | meets PDPA, sector (e.g. RMiT) and NCII-customer requirements; MD status where relevant |
| 5 | full compliance + certifications + listed in government / GLC digital programmes |

## 11. 如何解读和答辩分数

* **展示区间而不仅是一个点**：“64分（区间55–73，可信度75%）”。
* **以短板引领**：评分页以结论收尾，例如“主要短板是牵引力和单位经济，两份续约即可补齐”。
* **分数不等于决策**：评级只是建议；说明哪些事实会改变评级。
* **校准**：首次使用时，对3–5个已知项目（成功和失败的）打分，检查模型能否区分；不能则调整锚点而非权重。
* **双人评分**：某维度分差超过1分时应讨论证据。

## 12. 修改模型

* 新维度加入 `criteria` 并设定权重；随后更新所有 `stage_profiles`，确保每列合计100（测试会检查）。
* 受众系数和市场系数表示相对侧重（0.5–1.6），不要使用0。
* 修改后运行 `python -m unittest discover -s tools/tests` 和 `python tools/gen_scoring_doc.py`。
