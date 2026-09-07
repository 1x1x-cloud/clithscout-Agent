# 已展开女装类目页采集记录

核验日期：2026-09-06（Asia/Shanghai）。[用户提供的页面](https://shop.tiktok.com/us/c/womenswear-underwear/601152?source=ecommerce_mall&enter_method=categories&first_entrance=others_homepage&first_entrance_position=navigation_bar&first_entrance_tt_scene=seo&btm_pre=a18064.b46636.c37357.d69217_i1&btm_pre_show_id=027cf9a6-432b-4062-bf0a-fc8201c1caca&btm_transfer_id=acdeda42-69f8-4677-b72f-60345f78a3a1)。

已读取页面底部的 `No more products`，商品链接 100 个，商品 ID 去重后 100 个。该结论仅覆盖初次读取时已经展开的这次列表；不能据此推断全站、全类目库存量或所有会话的页面上限。

## 文件

- `products.csv`：100 条整理后的商品展示数据，UTF-8 BOM。商品 ID 为 19 位文本；在 Excel 中导入时将 product_id 列设置为文本，以免精度丢失。JSON 中 ID 保持字符串。
- `products.json`：来源、范围、字段覆盖及每件商品原始卡片信息区文本。
- `raw_batch_01.json` 与 `raw_batch_02.json`：浏览器读取的原始 [商品链接, 信息区文本]，各 50 条。
- `validation.json`：整批完整性及字段覆盖记录。

## 实际字段覆盖

| 字段 | 有值条数 |
| --- | ---: |
| 商品 ID、链接、展示标题、标价、已售展示值 | 各 100 |
| 评分 | 98 |
| 店铺或品牌展示名称 | 25 |
| 划线价 | 40 |
| 折扣标记 | 40 |

评分缺失为第 14、78 件，保留空值。店铺/品牌名称只取页面明确显示的独立名称，不从商品标题推断。页面顺序仅用于对账，不代表销量榜名次。商品 ID 从实际商品 URL 尾部读取。

## 核验与边界

最小验收：100 条记录与 100 个去重 ID 对应；标题、链接、标价、已售展示值无缺失；评分缺失不补零；输出保留原始数据；文件可重新解析。浏览器缓存数据序列与写入前原始记录的 FNV-1a UTF-16 校验值均为 `e56f6ab0`（仅用于检查转录一致性，不证明源数据真实销量）。字段解析时处理了标题中的重复空格。

已售数量原样保留 K 等缩写，统计周期未知，不当成近 3/7 天销量；价格为页面美元符号展示值，适用 SKU、折后结算价、税费口径尚未验证。第 8 件连帽衫显示 $3,000.00，已保留并标记待核实；未自动更正。

本次未批量取得图片链接、包邮标记、商品详情及视频数据。后续读取时同一标签页已切换到商品详情，故导出使用此前已缓存的完整类目列表；详情页的一次错位读取没有混入本文件。没有刷新或重新展开用户页面。浏览器通用内容导出不受支持；本结果由可读取 DOM 信息区数据整理保存。

本次验证了用户先展开列表后的单次采集，没有验证自动分页、无人值守稳定性或长期覆盖率。父类目页也出现男装及中性服装标题，页面类目不能直接充当每件商品的末级类目。

业务采集范围唯一来源：[../TASK_STATE.md](../../../project_governance/project_state/docs/TASK_STATE.md)。业务漏斗字段与验收定义唯一来源：[../field_dictionary.csv](../../../project_governance/business_rules/schemas/field_dictionary.csv)。本批数据是候选商品资料，不满足已约定的完整漏斗样本要求。

