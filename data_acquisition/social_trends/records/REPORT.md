# 四平台趋势覆盖与本次检查结果

核验日期：2026-09-06。当前窗口与执行优先级引用 [TASK_STATE.md](../../../project_governance/project_state/docs/TASK_STATE.md)。

**TikTok、Instagram、Reddit、Twitter/X 的本轮趋势统计尚未完成。** 此前 Pinterest 快照、个别平台页面访问、固定关键词检索和需求样例不构成这四个平台的趋势覆盖。本次实际完成的是四个平台公开入口的有界探测、官方指标说明核对和浏览器故障定位；合格的本轮四平台趋势数据集为 **0**。

## 实际采集状态

| 平台 | 本次实际读取结果 | 当前缺口 |
|---|---|---|
| TikTok | Web 读取到公开标签排行的 3 行 Posts/Views；工具标注缓存为 2 周前。URL 请求 US/7 天，但返回正文没有确认国家与统计起止。 | 登录浏览器正文、实际筛选状态、指标统计期、服装与可关联服装的热点、同口径比较。缓存数字不计入本轮。 |
| Instagram | Explore 页 Web 请求返回 429 Too Many Requests，没有返回正文。 | 正常登录页可读性、桌面端趋势入口、原始内容日期/市场和指标口径。没有把限流解释为没有趋势。 |
| Reddit | Web 读取到缓存为 3 周前的 Popular 页；正文有 Best/Hot/New/Top/Rising 与 Everywhere/United States 控件。只记录入口控件，未保存无关帖子。 | 新鲜且明确地域/时间的榜单或相关社区样本；Popular 排名、搜索热词、Pro 提及量须分别核验。 |
| Twitter/X | Explore 页 Web 请求返回 403 Forbidden，没有返回正文。 | 正常登录页可读性、地区选择、趋势观察时间与榜单显示数量口径。没有把工具拒绝访问解释为账号没有权限。 |

来源链接、原始显示值和访问限制见 [public_probes.json](public_probes.json)。上述网页检查发生在本轮固定窗口截止之后；缓存数据不会被写成当期统计，观察窗口没有滚动。

## 官方能力核对

已读取 11 篇官方说明与 1 个官方入口页面框架，详见[能力表](official_sources/CAPABILITIES.md)及[来源索引](official_sources/sources.json)。这是文档证据，不是当前账号功能验收。

- TikTok 官方当前帮助正文确认按行业/时间筛选标签趋势及查看趋势线、关联内容、受众与地域热度；本轮精确时间边界和 US 选项仍需现场核对。[TikTok Trends](https://ads.tiktok.com/resources/help/article/how-to-use-trends?lang=en&redirected=2)
- Instagram 官方历史公告介绍了 Reels 趋势音频/主题；当前桌面网页支持没有得到验证，个性化 Explore 内容不能直接当美国全站趋势。[Meta Reels 公告](https://about.fb.com/news/2023/04/instagram-reels-trending-audio-and-gifts-updates/)
- Reddit Pro 为部分关键词提供选定期的帖子/评论提及量和前期变化；其英文对话覆盖不能转换为美国专属统计。普通 Popular 页的地区控件与 Pro 覆盖是不同口径。[Reddit Pro Trends](https://support.reddithelp.com/hc/en-us/articles/47619216411284-Reddit-Pro-Feature-Trends)
- X 的趋势榜反映当前兴起讨论，支持位置选择；榜上近似帖数不等于固定七天总量。[X Trends FAQ](https://help.x.com/en/using-x/x-trending-faqs)

## 浏览器检查与下一步

用户已确认 Chrome 完全重启，扩展侧栏能加载，桌面设置显示 Manage。本次先取得新清单，再创建 TikTok 趋势页：创建调用超时，但后续清单已出现新页。对该已加载标签页重新绑定时，工具明确返回 **Debugger unattached**。本次重启后的正文请求失败两次，没有虚增为三次；已停止追加读取。

已知是网页调试通道未附着，尚不知道为什么未附着。今天查到的 3 个应用日志文件均为空，没有用旧日志推断本次原因。新页面能出现在清单中，也不能据此宣称正文读取已修复。详见 [browser_diagnostic.json](browser_diagnostic.json)。

官方排查说明列出通过新任务清理会话状态、重启桌面应用等步骤。保存本次状态后，建议用户先重启 Codex 桌面端，再回到此任务检查；不是再次重启 Chrome，也不保证一定修复。没有自动关闭应用、重装插件、更改权限或创建新任务。[OpenAI 浏览器连接排查](https://learn.chatgpt.com/docs/chrome-extension#troubleshooting)

恢复后优先核验四平台趋势入口和统计口径，再补需求原文与 SKU。若某入口只能展示“现在”的榜单，先如实记录观察时点；不能补写成原窗口历史榜单，也不擅自启动新窗口。

## 验收边界

最小核验：四个平台各有访问结果；缓存日期/未知字段不变成当期数值；官方文档与账号实测分开；JSON 和本地引用有效；原试跑文件不变。实际检查结果见 [validation.json](validation.json)。文件检查不代表四平台接入稳定、需求成立或选品有效。
