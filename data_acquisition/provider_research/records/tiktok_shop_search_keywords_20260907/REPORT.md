# Apify 能否提供美国 TikTok Shop 服装搜索上升词

核验日期：2026-09-07（Asia/Shanghai）。本次仅检索公开 Actor 说明、输入 schema 与平台文档；未启动 Actor、登录卖家后台或取得实时关键词数据。文档可被搜索引擎缓存，不能将说明或输出示例当作本日实测结果。

## 结论与验收口径

本次核查的公开 Actor 可用于关键词联想、商品检索及销量线索；**尚未确认一个现成 Actor 能同时提供 TikTok Shop 搜索场景、美国市场、服装分类和近期同口径搜索频率增长**。这是当前检查范围的结论，不是断言 Apify 全站绝无此工具。

接受为“搜索上升词”前，应验证：关键词及搜索入口、市场依据、服装分类、搜索指标定义、当前与比较时段、同口径数值或官方增长指标、来源和采集时间。排名、搜索联想、视频播放、销量和购买意图标签分别解释，不转换成搜索次数或搜索涨幅。

## 已核对的 Actor

| Actor | 文档所列能力 | 与本次目标的差距 |
|---|---|---|
| [memo23/tiktok-suggestions-scraper](https://apify.com/memo23/tiktok-suggestions-scraper) | TikTok 通用搜索自动补全；suggestion、volumeProxy、tiktokRank、hotLevel、ecomIntent、region、scrapedAt | volumeProxy 是返回该词的不同扩展查询数量，不是搜索量；没有本次所需的 Shop 搜索增长时序 |
| [easyapi/tiktok-keywords-discovery-tool](https://apify.com/easyapi/tiktok-keywords-discovery-tool) | 返回 keyword、type、item 等建议词 | 文档示例没有搜索次数、增长率、服装分类或已验证美国覆盖 |
| [memo23/tiktok-shop-sales-scraper](https://apify.com/memo23/tiktok-shop-sales-scraper) | 美国 Shop 按输入词返回商品、累计销量、日均销量、salesGrowthPercent、实际观察天数 | 输出主体是商品；增长字段针对累计销量，与关键词被搜索频率不同 |
| [doliz/tiktok-creative-center-scraper](https://apify.com/doliz/tiktok-creative-center-scraper) | 广告、标签及视频趋势等支持入口 | 当前说明明确移除了 keyword_insights 等旧 target，不能沿用旧功能介绍作为现行能力依据 |

Suggestions Actor 的 [输入 schema](https://apify.com/memo23/tiktok-suggestions-scraper/input-schema) 提供国家与语言、种子词、扩展深度和结果上限。开发者说明其地域取决于出口 IP，因此配置 US 后仍需核验实际地域。ecomIntent 表示购买意图信号，不能据此认定数据采自 Shop 买家搜索。未试跑其准确性和可用性。

另核查 [easyapi 输入 schema](https://apify.com/easyapi/tiktok-keywords-discovery-tool/input-schema)，并在 Apify 域名内检索 search volume、search frequency、search growth、search analytics、keyword ranking、Creator Search Insights 等组合；没有取得满足上述完整口径的现成返回证据。

## 项目中的使用建议

若只需要服装关键词线索，可将自动补全 Actor 作为待验证数据源，输入服装种子词后检查美国地域和相关性。比较多次同配置快照最多可标为“联想词曝光或排名变化”，不能标为实际搜索频率增长。此处是方法建议，没有创建定时任务或追加采集授权。

更直接的官方入口已确认：[美国卖家中心 Search Insights 说明](https://seller-us.tiktok.com/university/essay?knowledge_id=4613202404771597) 标注2026-07-13，路径为 Marketing → Search Insights → Industry Keywords → Trending keywords；官方将该类词定义为搜索兴趣快速增长的关键词。另有高搜索需求词和低竞争词，含义分别保留。

[实际后台入口](https://seller-us.tiktok.com/product/search-operations?shop_region=US) 本次公开读取跳转登录，未读取用户账号。服装子类选项、增长周期/公式、绝对搜索次数、导出和API可用性仍未确认。应先在账号可见范围核对这些字段，再决定是否开发或选择 Apify 接入；“官方有此功能”不等于“现成 Actor 已能获取”。平台来源另见 [官方入口核查](official_sources.md)。通用 TikTok 内容搜索与 Shop 商品搜索需分别保留来源标签。

本次不改需求卡规则和生产采集逻辑，不把搜索趋势直接当作已成立的商品普遍差评。未取得或推荐任何“本周服装上升词”名单。
