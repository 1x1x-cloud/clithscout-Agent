# 当前商品评价 Actor 合约核验

核验日期：2026-09-07（Asia/Shanghai）。本文件仅记录目标 Actor 的公开文档和已保存 API 元数据；本子任务未读取凭据、未操作浏览器、未启动 Actor。实际采集与输出验收由同目录的执行记录另行维护。

## 已确认身份与版本

目标 `zk1NwTZ5eTPYhRcvF` 为 **`lurkapi/tiktok-shop-reviews-scraper`**（TikTok Shop Reviews Scraper），社区开发者 LurkAPI 维护，公开且未弃用。认证 GET 的当前结果已由主任务保存为 [actor_metadata.json](actor_metadata.json)：读取时间 `2026-09-07T05:07:36.408084+00:00`、HTTP 200，`stable` 和 `latest` 同指向 `0.0.8` / `WYpz9tfujbBp1yK0S`。名称与 [Actor 产品页](https://apify.com/lurkapi/tiktok-shop-reviews-scraper)一致。公开网页可能经过缓存；运行时应保留实际 build 和价格快照。

## 输入与采集边界

下表依据 [Actor Input](https://apify.com/lurkapi/tiktok-shop-reviews-scraper/input-schema)，核验时工具标记网页抓取于5天前；以本次构建实际 input schema 再核对字段为准。

| 字段 | 类型 / 默认 | 本次用途或边界 |
|---|---|---|
| `productIds` | `string[]` | 支持批量商品 ID，18–19 位，以字符串传递 |
| `urls` | `string[]` | 支持商品或数字店铺 URL；本轮使用商品 ID 即可 |
| `maxReviewsPerTarget` | integer / 50，最小1，无声明最大值 | 每商品返回条数上限；拟300不是完整性保证 |
| `maxProductsPerShop` | integer / 5，范围1–50 | 只限制店铺输入；商品输入不受此值限制 |
| `sortBy` | `newest` / `recommended`，默认 `newest` | 本次显式使用 `newest` |
| `starRating` | integer / 0，范围0–5 | **0表示全部星级**，不只采差评 |
| `withPhotosOnly` | boolean / false | false，避免图片筛选造成样本偏差 |
| `country` | string / `US` | 当前唯一可选店铺地区为US |

公开 Input 未列开始/结束日期参数。日期应保留原始 ISO 时间并在本地按既有轮次筛选；不能发明 `startDate` 等字段或把运行时间当评价时间。[Input](https://apify.com/lurkapi/tiktok-shop-reviews-scraper/input-schema)

开发者说明混合 URL/ID 目标自动去重，匿名读取 TikTok 公开评价流，无需 TikTok 登录；`newest` 为时间排序。开发者同时提示公开流常在约2,000–2,400条处限制翻页，少于页面总数仍可能是平台可达深度限制。选0星级、300上限以及 SUCCEEDED 状态，均不能单独证明全体评价已完整取得。[Actor README](https://apify.com/lurkapi/tiktok-shop-reviews-scraper)

## 买家与 SKU 字段

Input 的输出开关默认均为 true，覆盖评分、正文、ISO时间、作者 handle/显示名/头像/购买验证/国家、评价图片、SKU ID、商品标题/主图/URL、店铺 ID 和来源输入。`outputAuthorHandle` 特别声明多数 handle 经 TikTok 隐私掩码处理。[Input](https://apify.com/lurkapi/tiktok-shop-reviews-scraper/input-schema)

**未确认提供稳定、不掩码的买家 ID；未声明输出颜色名、尺码名或适用尺寸表。** `outputSkuId` 仅承诺 SKU ID。需检查实际结果中字段存在率和含义；掩码 handle、显示名不同或正文不同不能直接写成独立买家人数。购买验证字段也须保留原值，并检查空值/默认值，不能补成 true。

`country=US` 指店铺地区，不能由此推断每条评价的作者国家均为美国。原页全球评价数不能直接替代本项目去重后的有效评价分母。以上为字段语义对本项目的适用判断；业务门槛仍引用 [V1 方案](../../../../project_governance/business_rules/docs/2026-09-06-clothing-demand-agent-v1-design.md)，不在此复制数值规则。

## 费用上限与运行选项

[API 元数据](actor_metadata.json)当前计费模型为 `PAY_PER_EVENT`，`review-scraped` 为每条 `$0.002`，`apify-actor-start` 为每事件 `$0.00005`，默认512 MB；`minimalMaxTotalChargeUsd=null`，未声明最低限额。产品页当前展示从 `$2/1000` 评价起，与该基础单价一致。[Actor 产品页](https://apify.com/lurkapi/tiktok-shop-reviews-scraper)

按三个目标各最多300条、512 MB、一次启动推算，900条评价事件加启动事件为 **$1.80005**；这是按当前已知事件价格计算的上界估算，不是实际账单。最终须核对运行的 `pricingInfo`、`chargedEventCounts`、`usageTotalUsd` 及费用明细。

运行费用上限应放在 **Run Actor API 的 `maxTotalChargeUsd=2` 查询参数/客户端运行选项**，不放进 Actor 的业务 input。官方 REST 文档当前写适用于全部计费模型；`maxItems` 仅用于 pay-per-result 的收费条数限制，不能替代本次 PPE 费用限制。[Run Actor API](https://docs.apify.com/api/v2/actors-runs-post)

官方 JavaScript `ActorStartOptions` 仍将 `maxTotalChargeUsd` 描述为仅 PPE；两份说明范围不同，但对本次已确认 PPE Actor 均适用，不影响本次参数选择。[ActorStartOptions](https://docs.apify.com/api/client/js/reference/interface/ActorStartOptions)

PPE 官方说明：平台强制单次 run 的费用限额，触顶停止追加收费/数据写入并自动终止；不是账户或多个 run 的合计限额。启动事件在不超过1 GB时计1次，因此默认512 MB对应上述启动估算；不要自动重开第二次run补缺失数据。是否达300上限、费用上限或平台分页末尾，需在执行日志分开核验。[PPE 计费与限额](https://docs.apify.com/actors/publishing/monetize/pay-per-event)

## 本次三商品建议输入（供主任务核对后使用）

以下是已确认字段构成的具体输入，不代表本文件已执行采集。商品 ID 来源应与主任务的产品档案逐一对账；除列出项外，保留输出字段默认 true，或在实际 schema 校验后显式开启。

```json
{
  "productIds": [
    "1732357239054307594",
    "1732510609891758832",
    "1731650530027868452"
  ],
  "urls": [],
  "maxReviewsPerTarget": 300,
  "sortBy": "newest",
  "starRating": 0,
  "withPhotosOnly": false,
  "country": "US"
}
```

运行选项：`build=0.0.8`、`maxTotalChargeUsd=2`、`memory=512`、`restartOnError=false`；输入与运行选项分开保存。API接受 build tag 或 build number；每次真正执行后保存响应里的实际 build ID、run ID和dataset ID。[Run Actor API](https://docs.apify.com/api/v2/actors-runs-post)

## 未验证事项

- 本子任务没有实际启动：每款能否返回、返回条数、SKU/作者字段实值、覆盖末端、按原窗口有效样本数均待运行证据。
- 页面总数与公开流可达条数是否一致、评价国家范围、删除/不可见评价等差异未验证。
- 公开价格页单独路径和公共 OpenAPI JSON 在 web 工具本次返回 Internal Error；未重复请求，也没有用这些失败页推断 schema/价格。上文价格依据已成功读取的 API 元数据，字段依据成功读取的 Input。
- 本文件不产生需求卡或找货许可；后续业务判断必须遵循唯一真源及真实数据验证。
