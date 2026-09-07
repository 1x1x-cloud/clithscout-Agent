# 美国服装词 → 具体商品与评价入口试查

核验日期：2026-09-07（Asia/Shanghai）。接续用户“下一步”，从[100词快照](../../../social_trends/records/fastmoss_us_keywords_100_20260907/REPORT.md)的 dress、bra、jeans 各定位1款商品，核对广告关联、TikTok 原页标题/商品ID/店铺及商品图片。此次为来源和可读性试查，不是买货推荐、完整评论分析或已接入自动采集。

## 已定位的三款商品

| 调查方向/商品 | 商品ID | 页面显示全球评价总数 | 本次实际读取 | 当前原页规格选项 |
|---|---|---:|---:|---|
| 连衣裙：HoneyBadgercome V领露背款 | 1732357239054307594 | 114 | 第1页，3条 | Light wash、Black、Pink、Light blue-green；XS–XL |
| 文胸：VRCOMFY 前扣款 | 1732510609891758832 | 112 | 第1–2页，6条 | Black、Nude；XS–XL |
| 牛仔裤：Fashion forefront 刺绣款 | 1731650530027868452 | 138 | 第1页，3条 | Blue、Dark gray、Regular wash, black、Dark blue；XS–XL |

原商品链接：[连衣裙](https://shop.tiktok.com/us/pdp/mens-athletic-t-shirt-by-brand-lightweight-quick-dry-crew-neck-tops/1732357239054307594)、[文胸](https://shop.tiktok.com/us/pdp/mens-athletic-t-shirt-by-brand-lightweight-quick-dry-crew-neck-tops/1732510609891758832)、[牛仔裤](https://shop.tiktok.com/us/pdp/mens-athletic-t-shirt-by-brand-lightweight-quick-dry-crew-neck-tops/1731650530027868452)。商品ID均按字符串保存；完整来源链、店铺ID、原页类目、10个颜色图URL和选中主图见 [products.json](products.json)。图片没有下载或上传。

选择依据是关键词下出现明确服装描述并能回到原商品，不是销量、ROAS或增长排名。jeans 素材结果还含T恤、卫衣、腰带；此类单纯文案命中没有选作牛仔裤。FastMoss指标含义沿用前次来源记录，不转换成买家搜索增长。

三条落地链接都带相同的男士T恤slug，但实际TikTok原页的标题、类目、商品ID和店铺分别对应上述三款。已通过原页核对身份；slug成因未知，不能依据网址文字判定品类。网页中标注AI生成的简介/FAQ及商家标题均未作为面料、功能或尺码实证。所见颜色与尺码不证明每个组合可售，也不提供SKU ID映射。

## 评价已读到什么

读取时排序为“推荐”、筛选为“全部”；首屏三款各3条均为五星，文胸第二页为5、5、2星，共12条。文胸点击“下一步”后读到不同评价，确认本次翻页成功。页面虽分别显示38、38、46页，余下页面尚未读取，不能声明全部可读或已收齐。

文胸第二页有1条2星反馈，称舒适但承托和包容不足，购买规格显示 Nude、L，日期2026-09-01。仅保留为**待补证据线索**；该条未显示“真实购买”标记，购买验证状态未知。不能因不同昵称或不同正文硬写独立买家人数。部分好评描述贴合和舒适，后续需保留反向证据，不能只采低星。

连衣裙有1条五星评价提到裙子很短，但日期2026-08-14明确早于原窗口，只作为历史线索。牛仔裤两条历史评价希望增加颜色，而当前页已显示四色，不能将历史愿望直接写为当前供给缺口。文胸首条评价说以前的后扣使背部发痒，并认为本品前扣解决问题，不能误判为本品致痒。逐条解释见 [review_triage.json](review_triage.json)。

12条记录分属三个商品，不能合并分母；页面显示的全球评价总数也不等于美国、当期、去重后的有效样本量。当前全部样本均缺稳定买家ID、评价ID、SKU ID及精确时间/时区。正文、市场US标记、日期及所购颜色尺码展示已保留；未显示购买标记不等于已证实未购买。

## 接续动作与边界

下一步按[采集清单](review_collection_plan.json)继续补各商品全星级评价，核对覆盖完整性、评价身份、买家去重及SKU映射。原[运行窗口](../../../../workflow_execution/run_configuration/config/current_round.json)保持不变，本次页面观察未写入旧评论轮次。日期落在边界或没有精确时区时保持待确认，不为凑门槛擅自扩窗。

需求资格仍按 [V1 S1规则](../../../../project_governance/business_rules/docs/2026-09-06-clothing-demand-agent-v1-design.md)。当前有效分母、独立买家人数、问题占比全部待确认，**新需求卡0、1688查询0**。没有运行生产分析、新Apify Actor或付费采集；若采用Actor替代后续翻页，需先核验实际返回字段、覆盖能力和费用，清单不是可提交的Actor输入。

## 档案与验证

- [首屏原始转录](source_reviews.transcribed.json)：9条，由真实DOM快照解析；保留快照字符串中的原始引号表示。
- [文胸第2页转录](bra_page_02.transcribed.json)：3条；与第1页不同。
- [观察记录](observation.json)：来源范围、时间、传递指纹及历史保护文件哈希。
- [核验结果](validation.json)：检查转录指纹、商品及来源关联、星级总数、规格、未知字段和本地引用，以及5个既有文件保全。

验收范围是本次页面读取和档案一致性；未验证全量评价覆盖、独立买家、适用尺码表、实物面料、供货及真实测品效果。当前状态唯一维护于 [TASK_STATE.md](../../../../project_governance/project_state/docs/TASK_STATE.md)。
