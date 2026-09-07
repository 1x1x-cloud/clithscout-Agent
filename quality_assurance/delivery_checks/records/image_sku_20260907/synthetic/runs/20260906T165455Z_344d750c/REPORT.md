# 服装差评 → 找货对照报告

合成测试示例：评价、商品和规格为测试输入，不代表真实市场或供应商资料。

本报告由有限规则引擎自动生成；未覆盖、含糊和矛盾表达进入人工复核。

运行状态：**completed**；开始时间：2026-09-06T16:54:55.939620+00:00。
观察窗口：2026-08-30T09:05:42Z（含）至 2026-09-06T09:05:42Z（不含）；US 为来源字段所报市场。

原始评价 1 条；窗口内 1 条；窗口外 0 条；时间未知 0 条。
当前需求卡 1 张；商品对照 1 条；合格现货测品候选 0 条。
未覆盖/需人工解释的记录 0 条；重复记录 0 条；ID内容冲突记录 0 条。

上述是返回样本的记录数；没有全星级分母，不计算差评率、独立买家数或市场需求普遍程度。

## 当前需求与原文

### S1-c1fa9d160f846a83 · 评价者认为衣物过长

状态：待补证据；同商品不同正文信号 1 组（不是独立买家数）。

> The pants are too long and I had to hem them.

证据：EV-410f86324f335cee；评价 ID：synthetic-new-id；来源商品：synthetic-product；时间：2026-09-01T12:00:00Z。

待确认：目标衣长/裤内长、所购尺码及成衣实测；采购数量、目标价格、交付要求；其他独立使用者的证据。

## 原商品主图 → 图片找相似款

主图来自评价记录 productMainImage；仅保留 URL 引用，未归档图片像素。相似度为平台返回值，不证明同款、面料或尺寸。

- 原商品：synthetic-product；所购 SKU：synthetic-sku。
- 主图：https://example.invalid/product-main.jpg
- 查询计划：就绪；原因：主图可用于查询；证据：EV-410f86324f335cee。

## 1688 工具原始展示

以下表格为工具返回的原文；价格、卖点和配送标签均未独立核实。

查询用途：原商品主图召回相似款，再按差评与具体SKU核对规格。模式：synthetic_test；来源检查时间：2026-09-06T16:54:55.998626+00:00。

| Original provider table |
|---|
| candidate |

## 逐项商品核对

| 商品 ID / SKU | 满足（仅文字初筛） | 冲突 | 未知 | 结论 |
|---|---|---|---|---|
| candidate / candidate-sku | 服装品类与本次线索对应；具体原商品与候选SKU资料绑定；尺码与成衣尺寸符合已提供目标；面料成分符合已提供目标 | 无 | 评价者认为衣物过长：替代商品满足明确目标；当前可采购状态、价格数量条件、发货地和交付要求 | 待人工核验 |

## 差评、尺码、面料与具体 SKU

满足仅表示已提供资料符合明确目标；引用内容和实物未自动验证，穿着效果及供货仍待复核。

### 候选 candidate / candidate-sku

候选主图：https://example.invalid/candidate.jpg；详情：https://example.invalid/candidate。

> The pants are too long and I had to hem them.

原商品 / SKU：synthetic-product / synthetic-sku；评价：synthetic-new-id；来源：https://example.invalid/pants。

| 评价 | 核对项 | 状态 | 依据与缺项 |
|---|---|---|---|
| synthetic-new-id | 具体原商品与候选SKU资料绑定 | 满足（资料对照） | 资料已按平台、商品和具体 SKU 对齐 |
| | 原 SKU资料来源 | | https://example.invalid/specification；核对时间：2026-09-06T09:00:00Z；尺码标签：待确认 |
| | 候选 SKU资料来源 | | https://example.invalid/specification；核对时间：2026-09-06T09:00:00Z；尺码标签：待确认 |
| synthetic-new-id | 尺码与成衣尺寸符合已提供目标 | 满足（资料对照） | 仅核对明确尺寸范围，实际合身效果待实物验证 |
| | 对照数值 | | inseam（garment_length）：原 SKU 85 cm，候选 SKU 30 inch，目标 75–77 cm |
| | 目标资料来源 | | https://example.invalid/specification；核对时间：2026-09-06T09:00:00Z |
| synthetic-new-id | 面料成分符合已提供目标 | 满足（资料对照） | 仅核对成分比例，触感、透视、缩水等性能待实物验证 |
| | 对照数值 | | cotton：原 SKU 100%，候选 SKU 95%，目标最低 90% |

资料原文、来源与核对时间：product_matches.json 的 spec_checks；输入归档：sku_evidence.json。


## 下一步复核

- 补所购尺码、目标部位及成衣尺寸；不能从“太大”直接推导 S 码或修身版。
- 核对替代商品的具体 SKU、规格、实际可采购状态、价格数量条件及交付信息。
- manual_review.json 保留未覆盖正文、异常、未查询需求及逐商品待办。
- 历史或其他市场需求保留于 demand_cards.json，不混入当前查询。

程序完成不代表业务候选合格。本版未接入通用语言模型、新 Actor 采集、四平台趋势或采购审批；未验证 CTR、点击下单率及推荐效果。

原始数据见 raw_reviews.json；逐条证据见 evidence.json；全部来源返回见 searches/；执行与校验见 manifest.json、validation.json。
