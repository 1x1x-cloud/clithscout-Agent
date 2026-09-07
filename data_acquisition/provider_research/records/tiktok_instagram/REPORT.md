# TikTok / Instagram：不连接本机浏览器的数据路径

核验日期：2026-09-06；记录时间：2026-09-06 10:06:42 UTC。项目范围与固定窗口引用 [TASK_STATE.md](../../../../project_governance/project_state/docs/TASK_STATE.md)。本次只查官方资料与一个供应商 Apify 的产品文档，未注册、付费、联系供应商或执行任何采集任务。

**可以用云端采集 API 替代本机 Chrome 连接。就本项目而言，Apify 的两个维护型 Actor 是值得做小样本验收的路径；它们提供选定关键词、话题、账号和帖子样本，不能直接称为两平台全站趋势。** Apify 官方说明 Actors 是云端程序，可由 API、CLI 或定时任务运行；这种模式不依赖本机浏览器扩展。[A0](https://docs.apify.com/actors)

## 官方 API 的适用范围

| 路径 | 已核验能力与认证 | 本项目判断 |
|---|---|---|
| TikTok Research API | 官方 FAQ 明确创作者、广告主及商业用户不符合 Research Tools 资格，单有开发者账号也不够。[T1](https://developers.tiktok.com/docs/en/research-api-faq) | **不作为商业服装选品方案。** 不以研究名义申请商业用途。 |
| TikTok Display API | 需要开发者应用、Login Kit/API 产品审批、scope 与用户授权；用于获取授权用户资料和视频，示例含视频 ID、描述及分享链接。[T2](https://developers.tiktok.com/docs/en/display-api-get-started) | 可补授权合作账号，所读文档没有建立全站热点/任意关键词评论采集能力。 |
| TikTok Commercial Content API | 可按关键词或广告主检索商业内容资料，需申请通过；所读官方页仍明确当前阶段只包含 EU 数据。[T3](https://developers.tiktok.com/products/commercial-content-api?from_seo_redirect=1) | **不满足本项目美国自然讨论趋势。** “Commercial”不等于美国电商全站数据。 |
| Instagram API | Meta 官方 Postman 集合确认：Facebook Login 路径面向专业账号，需关联 Page 与 token；可找 hashtagged media、获取其他专业账号基本元数据/指标，评论管理围绕自己的内容。Instagram Login 路径也面向专业账号。[I1](https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api?entity=request-23987686-ab559ffb-8e2c-4b0a-b43a-5737b6d2f672) | 商业专业账号的**受限补充**，不能由此承诺全站热点、所有消费者账号或任意帖评论。当前 hashtag 详细额度、App Review 条件和历史窗口未核实；不套用未读到的旧数值。 |

Meta 开发者文档两次访问分别报抓取失败及 429，随后读取 [Meta 已验证的官方 Postman 团队](https://www.postman.com/meta)及其 Instagram 集合，没有反复请求失败路径。集合是官方发布资料；其示例并非本项目实测结果。

## 云端候选：Apify

下表字段来自供应商说明/示例，**实际返回率、完整性和稳定性尚未验证**。两个主 Actor 页面均显示 `Maintained by Apify`；这是维护信息，不是 TikTok/Meta 的官方授权或全量保证。

| Actor | 采集对象与可追溯字段 | 地区、历史与评论边界 |
|---|---|---|
| [clockworks/tiktok-scraper](https://apify.com/clockworks/tiktok-scraper) | 关键词、hashtag、账号、视频 URL；示例含视频 ID、原帖 URL、描述、发布时间、播放/赞/分享/评论/收藏计数。 | `proxyCountryCode=US` 是代理出口/可见性，**不是美国观众或买家过滤**。搜索提供相对时间选项；账号日期过滤有单独条件/收费。评论可通过附加采集，文档明确条数及回复完整性不保证。[输入说明](https://apify.com/clockworks/tiktok-scraper/input-schema) |
| [apify/instagram-scraper](https://apify.com/apify/instagram-scraper) | 账号、hashtag、地点、帖子/短视频 URL；示例含原帖链接、ID、caption、时间、点赞/评论数及选定评论。 | 地点检索是地点对象，不等于美国消费市场。支持 UTC 日期/ISO 下界；置顶内容可能仍出现，仍需本地核验双边时间。评论模式需对应帖子 URL；免费用量的评论条数受限，完整访问依计划。[输入说明](https://apify.com/apify/instagram-scraper/input-schema) |

TikTok 还可对选定视频使用 [Comments Scraper](https://apify.com/clockworks/tiktok-comments-scraper)，文档示例含 `cid`、评论原文、`createTimeISO` 与父视频 URL。可保留原帖和评论 ID 回溯；是否能重新定位每条评论、是否缺回复，要在验收中检查。视频的 `commentCount` 不能替代评论原文条数。

调用需要 Apify 账号及 API token；官方 API 示例是在云端运行 Actor 后读取结果 dataset。当前没有检查本项目是否已有账号、token 或可用余额。[API 说明](https://apify.com/apify/instagram-scraper/api/python)

收费方面，核验时两个主页面分别显示 TikTok **$1.70/1,000 results 起**、Instagram **$1.50/1,000 results 起**；不是含日期过滤、评论、转录等附加项的总报价。TikTok 独立评论页存在价格不一致：页头 $0.50/1,000 comments 起，正文旧 FAQ 写 $5/1,000；该项当前价格留待计费页/账号报价确认，不据此估总预算。

## 如何产生可信的趋势线

建议先选择固定的关键词/话题/账号集合，保存每次输入、Actor 版本、运行 ID、观察时间、结果上限及每条源 ID。这样得到的是**有明确覆盖范围的趋势样本**；热门列表只能提供候选，不能证明全站提及总量。

增长需要同一对象、同一口径的至少两个不同时点观测，或供应商有定义且可核验的历史序列。现在抓到旧帖及其当前累计播放量，不能反推它在过去七天增加了多少。分段计算新帖子数也须控制发现范围和漏采，不能把返回结果数直接当平台发布总量。

本轮仍为 **2026-08-30 09:05:42 UTC 至 2026-09-06 09:05:42 UTC**。可尝试找该窗口内原帖，再逐条筛时间与美国场景依据；相对 `PAST_WEEK` 会随运行时间变化，不能直接替代固定窗口。若此前没有计数快照，也没有可核验历史序列，本轮“播放增长”保持未知。

建议下一步只验收少量公开样本：原帖 URL/ID、发布时间、评论原文/ID、美国市场依据、缺失字段处理、失败返回及实际费用。达到项目既有证据标准后再决定持续运行；本次不部署、不采集、不预设商业阈值。

来源与限制见 [sources.json](sources.json)。已核验的是文档能力与候选路径，未验证任何 Actor 本次运行、美国覆盖或真实需求；不会改变既有合格计数。
