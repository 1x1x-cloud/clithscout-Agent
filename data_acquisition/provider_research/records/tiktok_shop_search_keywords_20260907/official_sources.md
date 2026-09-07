# TikTok 官方搜索需求入口核查

核验日期：2026-09-07（Asia/Shanghai）。范围：公开官方文档与入口的只读 Web 检索；未登录、调用 Actor、运行采集代码或取得实时词榜。Apify 结论见同目录 [REPORT.md](REPORT.md)。业务口径沿用 [V1 方案 S3](../../../../project_governance/business_rules/docs/2026-09-06-clothing-demand-agent-v1-design.md)。

最小验收：结论有具体来源；区分 Shop 相关搜索、广告用词和全站内容搜索；文档能力与账户实测分开；未知指标不补造。

## 结论

**最接近需求的是美国 Seller Center 的 Marketing → Search Insights → Industry Keywords → Trending keywords。** 官方文档将这一类定义为搜索兴趣快速增长的词，另有高搜索需求词与低竞争词。文档日期为 2026-07-13，属于 TikTok Shop 搜索运营说明。它可以作为优先核查入口，但本次没有证明任何 Apify Actor 能读取它，也没有取得美国服装关键词实际排名。[Search Insights 官方指南](https://seller-us.tiktok.com/university/essay?knowledge_id=4613202404771597)（核验：2026-09-07）

## 已确认来源与边界

| 官方入口 | 文档已确认内容 | 不能据此确认 | 来源与核验日期 |
|---|---|---|---|
| Seller Center → Marketing → Search Insights | Industry Keywords 分为 Hot、Trending、Low-competition；Trending 为快速增长的搜索兴趣。另有搜索机会、行业排名、看视频后的搜索；店铺表现可按时间及 Product Cards / LIVE / Videos 筛选。 | 店铺表现的时间筛选不自动等于关键词榜时间窗；未公开明确绝对搜索次数、增长率公式、榜单刷新频率、全部服装子类或数据是否仅来自 Shop Tab 搜索框。 | [Search Insights](https://seller-us.tiktok.com/university/essay?knowledge_id=4613202404771597)，2026-09-07 |
| 美国 Search Insights 实际入口 | 官方链接带 `shop_region=US`；本次公开读取跳转 Seller Center 登录页。 | 用户账户权限、登录后的字段、可导出性、可自动读取性及实际美国服装结果未验证。 | [美国 Search Insights](https://seller-us.tiktok.com/product/search-operations?shop_region=US)，2026-09-07 |
| 较早文档入口：Analytics → Shop tab → Search → Keyword Rankings | 2026-04-30 官方 SEO 课程说明可查看本商品类别中的高搜索需求词，并关注 rising / high-potential keywords。 | 未确认该导航是否仍与当前账户一致；不能据此补出涨幅数值和周期。优先使用较新的 Search Insights 说明核查。 | [SEO & Discovery](https://seller-us.tiktok.com/university/course?content_id=6613772375164686&lang=en&learning_id=6037851293763342)，2026-09-07 |
| Products → Product Opportunities → Trending keywords | 2026-08-04、明确适用美国的指南说明：提供与商品/类别相关、高搜索量且相关商品数量较少的词；详情有 Opportunity trends and performance 以观察兴趣变化。该工具还混合热门 hashtag 等机会。 | “每周了解趋势”并不是固定 7 天计数口径；高量/低供给不等于最近搜索量增长；不是所有机会都是买家搜索关键词。 | [How to Use Product Opportunities](https://seller-us.tiktok.com/university/essay?knowledge_id=4371484668528427)，2026-09-07 |
| Product Opportunity Insights（历史功能说明） | 官方月度说明称可按词查 TikTok Shop 需求与销售潜力，展示过去 30 / 60 天的订单量与搜索量。 | 页面标题是 May 2025，显示日期却为 2026-05-14，记录此差异；不把历史说明当作当前账户字段实测，也不把 30 / 60 天自动套用至新 Search Insights 的 Trending 榜。 | [May 2025 Product Innovation](https://seller-us.tiktok.com/university/essay?knowledge_id=84611377383210)，2026-09-07 |
| Creative Center → Keyword Insights | 官方定义为从 TikTok 广告中提取的常用/高表现词语，服务广告文案创作。本次旧入口跳转 TikTok One Creative Suite。 | 广告词出现频率、Popularity 或 Popularity Change 不是 Shop 买家搜索次数或搜索涨幅。 | [Creative Center 官方定义](https://ads.tiktok.com/help/article/creative-center?lang=en&quot=)、[旧入口](https://ads.tiktok.com/business/creativecenter/keyword-insights/pc/en)，2026-09-07 |
| Creator Search Insights | 官方发布说明介绍的是 TikTok 内容搜索主题，含类别、个性化主题、热度分与 content gap；内容缺口指搜索较多而相关视频较少。 | 不是已确认的 Shop 专属买家搜索数据；内容缺口不等于商品短缺。2024 发布说明提到部分地区开放，当前账户可用范围未实测。 | [TikTok 官方发布说明](https://newsroom.tiktok.com/creator-search-insights?lang=en)，2026-09-07 |

## 尚未确认与下一步验收

建议在有正常权限的美国 Seller Center 内核查 Search Insights，保留账户市场、服装分类、关键词、原始指标名称/单位、统计起止日、比较期和读取时间。先验明 Trending 表究竟展示指数、分档、涨幅还是次数，再判断能否支持“最近搜索频率上升”。这是取证建议，不代表已获数据或已完成接入。

仍未知：服装分类实际可选范围；关键词统计周期、比较基期和时区；搜索兴趣与计数的对应关系；全量/抽样/阈值屏蔽情况；是否仅 Shop Tab 搜索、是否包含其他内容搜索；导出/API/Apify 支持及账户权限。官方说明不足以填补这些字段。

## 读取与验证记录

- 已读 Search Insights、Product Opportunities、SEO 课程和相关官方定义；结论仅使用各页面实际返回的内容。
- 美国 Search Insights 入口跳转登录，未继续登录。
- Creator Search Insights 的 Help Center 直接读取无正文；另一带语言参数的读取返回不可重试错误。改用官方 Newsroom 定义，不把该读取失败解释成工具已停用。
- Creative Center 的关键词详情搜索缓存曾出现关于视频数量的 Popularity 定义；本次打开详情正文只见空的关键词栏目，故不采用该缓存说明作为当前可见字段证明。报告只引用官方广告词定义。
- 官方指南中的例词和示意截图均非本次实时美国服装词榜，本文件不输出任何实际上涨词或增长数值。
- 文档验收范围：新文件内容、来源归属、核验日期、相对项目链接和未知项表达；无代码改动，不运行业务回归或收费采集。
