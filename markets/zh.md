# Market guide: Mainland China (`zh`)

Default locale `zh` (Simplified Chinese) · currency CNY (元/万元/亿元) · citations GB/T 7714-2015
numeric · verified 2026-10-20.

## 1. Statistics and data sources / 数据来源

| Need | Source | Link |
|---|---|---|
| 官方统计（GDP、CPI、企业数量） | 国家统计局 National Bureau of Statistics | https://www.stats.gov.cn/ |
| 货币政策、LPR、利率 | 中国人民银行 People's Bank of China | http://www.pbc.gov.cn/ |
| 国债收益率曲线 | 中国债券信息网 (ChinaBond) | https://www.chinabond.com.cn/ |
| 软件和信息技术服务业统计 | 工业和信息化部 MIIT | https://www.miit.gov.cn/ |
| 网络与数据监管、生成式AI备案 | 国家互联网信息办公室 CAC | https://www.cac.gov.cn/ |
| 政府采购 | 中国政府采购网 | https://www.ccgp.gov.cn/ |
| 国家标准全文 | 国家标准全文公开系统 | https://openstd.samr.gov.cn/ |

## 2. Regulation and sovereignty / 合规与自主可控

The criterion for this profile measures readiness for government and key-industry buyers:

* **《个人信息保护法》 PIPL** — adopted 2021-08-20, in force 2021-11-01
  (http://www.npc.gov.cn/npc/c2/c30834/202108/t20210820_313088.html).
* **《数据安全法》 Data Security Law** — adopted 2021-06-10, in force 2021-09-01
  (http://www.npc.gov.cn/npc/c2/c30834/202106/t20210610_311888.html).
* **《网络安全法》 Cybersecurity Law** — amended by the NPCSC decision of 2025-10-28, amendments
  in force 2026-01-01 (http://www.npc.gov.cn/npc/c2/c30834/202510/t20251028_449048.html).
* **《生成式人工智能服务管理暂行办法》** — interim measures for generative AI services offered to
  the public, including filing (https://www.cac.gov.cn/2023-07/13/c_1690898327029107.htm).
* **等级保护 MLPS 2.0** — GB/T 22239-2019 baseline requirements
  (https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=BAFB47E8874764186BDB7865E8344DAF).
* **信创 (IT application innovation)** — compatibility with domestic CPUs, operating systems and
  databases is usually requested by government and SOE buyers; ask the customer for the
  applicable catalogue or certification.
* Cross-border transfer of personal information requires one of the mechanisms provided by PIPL;
  check current CAC rules before promising any transfer.

Scoring facts: `xinchuang_adapted`, `mlps_certified`, `genai_filing_missing`,
`cross_border_data_unassessed`, `critical_foreign_dependency`.

## 3. Discount rate, inflation, valuation / 折现率与估值

* Risk-free rate: government bond yield of matching maturity (ChinaBond curve), dated and linked.
* Policy reference: LPR published by the PBoC; do not hard-code values.
* CPI from the NBS; state 名义 / 实际 explicitly.
* Domestic investors and state-backed funds often look at revenue scale, customer quality
  (government / SOE references), qualifications and the path to profitability; venture IRR targets
  must be stated as assumptions. The example uses 18%.
* Units: 万元 and 亿元, never "million" translated literally; `fmt_utils.py` handles this.

## 4. Audience and presentation culture / 受众

* **政府与国企 (government and SOEs).** Formal titles, policy alignment (refer to official
  documents by full name and number), qualifications (等保, 信创, 软件著作权), local service
  capacity, case studies with named reference customers only if permitted.
* **投资人 (investors).** Market space, team, technology barriers, commercialisation milestones,
  financing ask; 15–20 pages common for BP (商业计划书).
* Body text uses 2-character first-line indent in reports; table captions above, centred
  ("表1  …"); the tools apply these by locale.
* Fonts: Microsoft YaHei / Noto Sans CJK SC for slides, SimSun (宋体) body and SimHei (黑体)
  headings for reports.

## 5. Banned and hype phrases / 禁用词

`config/banned_phrases.json` → `zh`: 独一无二、颠覆性、革命性、史无前例、世界第一、100%准确、零风险、
稳赚、保本、风口 and others. 国际领先、国内领先、首个、首家 only with a cited source (an appraisal
report or authoritative evaluation). Note that absolute claims in advertising are restricted by the
Advertising Law; in investor material they damage credibility.
