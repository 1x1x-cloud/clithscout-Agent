# 四平台趋势：不连接本机浏览器的方案

核验日期：2026-09-06。项目范围、窗口与业务标准引用 [TASK_STATE.md](../../../project_governance/project_state/docs/TASK_STATE.md)；本报告只记录取数路径评估，不改变业务规则。**可以不依赖本机 Chrome 扩展连接，改用 API 或文件导入；当前仍未接通或实测这些服务。**

## 可选方案

| 路径 | 已核验能力 | 限制与采用条件 |
|---|---|---|
| TikTok：Apify 云端 Actor | 关键词、话题、账号、视频 URL 样本；文档示例有原帖 ID/URL、发布时间、播放及互动计数，可附加评论采集。[产品](https://apify.com/clockworks/tiktok-scraper) | 第三方服务，不是 TikTok 官方 API；不是全站热榜。US 代理出口不代表美国消费者，评论完整性和历史覆盖需验样。 |
| Instagram：Apify 云端 Actor | 话题、账号、地点、帖子/Reels 样本及部分评论，输出可追溯链接与时间。[产品](https://apify.com/apify/instagram-scraper) | 不是全站热榜，地点不等于受众地区；评论范围、缺失和计费需验样。Meta 官方 API 可补专业账号及受限话题数据，不能直接承诺广域消费趋势。 |
| X：官方 API | Trends 按地区取当前话题，美国 WOEID 为 23424977；Post Counts 提供关键词匹配帖量时间序列；Search 可取得匹配原帖。[Trends](https://docs.x.com/x-api/trends/trends-by-woeid/introduction)、[Counts](https://docs.x.com/x-api/posts/counts/introduction)、[Search](https://docs.x.com/x-api/posts/search/introduction) | 需开发者账号、应用和 Bearer token，按量收费；当前榜单不能回填历史榜单。Trends 当前文档只确认话题名，不承诺每条带帖量。关键词计数与原帖检索的过滤可能不同。 |
| Reddit：获批商用 API 或有相应许可的数据服务 | 以公开讨论、帖子及评论作为需求样本来源。Reddit 官方要求访问审批，商业用途需相应书面许可/协议。[政策](https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy)、[条款](https://redditinc.com/policies/data-api-terms) | 不能假定注册免费 OAuth 即可商用；采用供应商也要确认合同包含本项目分析用途及所需原文输出。 |
| 统一服务：Meltwater Listening API | 官方矩阵明确 TikTok、Instagram、Reddit、X 均支持提及总量、按日/小时提及量以及部分话题分析；API token 和套餐决定可用功能。[能力矩阵](https://developer.meltwater.com/api-reference/analytics-options/listening/)、[接入](https://developer.meltwater.com/guides/getting-started/overview/) | 统计供应商覆盖的搜索结果，不是全平台总量或原生热榜。TikTok 不在该矩阵的国家/地点分组支持列表中，不能承诺四平台统一美国筛选。报价、历史期、原文/评论出口和额度均待确认。 |
| 导入 CSV/JSON | Agent 可消费平台或供应商合法导出的文件，无需浏览器扩展连接。 | 这是待实现的导入方案；更新频率由文件交付决定，不能称为已建立连续自动监测。 |

Apify 的 Actors 在云端运行，可经 API 调用；不需要连接用户本机 Chrome。服务内部可能使用浏览器技术，所以此处的“无浏览器连接”不等于供应商完全不使用浏览器。[Actors 说明](https://docs.apify.com/actors)

Meltwater 自述于 2026 年成为 Reddit 官方数据合作伙伴，可作为商用许可路径的候选；这不是本项目已取得授权或已验证其原文导出权限。[供应商公告](https://www.meltwater.com/en/press-releases/reddit-partnership)

## 本项目的建议

先验证混合 API 方案：TikTok/Instagram 用 Apify 样本源，X 用官方 Trends + Counts + Search，Reddit 采用获批商用路径。这样可以分别核对可追溯原文与统计口径，且不必等 Chrome 恢复。若希望减少供应商数量，再以 Meltwater Listening 为统一方案候选，先验样和确认报价，不先购买。

这里推荐的是验证顺序，不是已选定供应商或已证明最便宜的方案。预算、账号权限和运行规模尚未确认。若优先要求一个入口覆盖四平台，Meltwater 的文档覆盖更直接；若优先原帖/评论可控和分项验收，混合方案值得先试。

趋势发现应有两部分：从覆盖范围明确的榜单、话题和监测样本发现新线索，再按新增关键词跟踪帖子与评论。不能只查询原来三个词就声称发现了平台整体新趋势。互动热度只用于选题线索，需求与测品仍按项目既有证据和指标标准验收。

## 时间、市场与费用

- X Recent Counts/Search 是调用时回溯最近 7 天；Archive 能查询更早记录。原轮次固定窗口见状态文件，当前调用的滚动 7 天已无法完整覆盖其最早部分；回补需可用档案或此前保存的数据，不能静默换窗口。档案原帖也不能重建过去的原生趋势榜。
- 旧帖的当前累计播放/点赞不等于当时七天增长。增长需相同口径的多时点快照或经核验的历史序列；未取得时保留未知。
- “美国榜单地区”“帖子标注地点”“作者地点”“美国观众/买家”是不同字段。英文内容及 US 代理出口不能直接证明美国消费需求。
- X 当前价格页：Posts Read 为 $0.005/资源，Recent Counts 为 $0.005/请求，Archive Counts 为 $0.010/请求，Trends 为 $0.010/请求。最终以调用前账号控制台现行费率为准，本次未计费调用。[价格](https://docs.x.com/x-api/getting-started/pricing)
- Apify 两个主 Actor 页显示 TikTok $1.70/1,000 results 起、Instagram $1.50/1,000 results 起，附加字段/评论等可能另计；独立 TikTok 评论 Actor 页存在价格冲突，不据此估总预算。详见 [TikTok/Instagram 核验](tiktok_instagram/REPORT.md)。
- Meltwater 需确认套餐 API 权限，未取得公开总报价或本项目报价。其导出窗口采用开始含、结束不含，采集延迟和重复输出也应验收。[FAQ](https://developer.meltwater.com/help/faqs/)

## 接入前的最小验收

以下是建议的技术验收项目，不另设商业阈值或任意成功率：

1. 实际返回可追溯的帖子 ID/URL、发布时间；评论有原文、源 ID 或可验证的父帖关联。
2. 保存查询、覆盖范围、地区语义、观察时间和限制；按固定窗口筛选，未知值不补零。
3. 分别检验发现新线索、取原文、取评论和生成可比较序列的能力，不把累计计数当历史增长。
4. 确认商用范围、实际扣费、分页/结果上限、失败处理及删除/更新要求，再安排连续运行。

本次完成文档路径评估；没有注册账号、读取凭据、联系供应商、付费、执行 Actor/API 采集或创建自动化。四平台当期合格趋势数据集、合格需求与测品候选数量均不因此增加。来源与事实边界见 [sources.json](sources.json)，TikTok/Instagram 的进一步来源见 [明细](tiktok_instagram/sources.json)。

