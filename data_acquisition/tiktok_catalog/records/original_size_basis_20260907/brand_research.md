# CHICME 原商品款式线索与尺码依据

核验日期：2026-09-07（Asia/Shanghai）。商品 HTML 读取开始于 `2026-09-06T17:39:59.663977+00:00`，即北京时间 2026-09-07 01:39:59；尺码图片读取于北京时间 01:42:05。HTTP 均为 200。本记录仅负责品牌官网资料，TikTok 原商品与所购 SKU 的核验由本次主记录负责。

## 结论及适用边界

**找到该 CHICME 商品专属的尺码表。** 官网商品正文直接引用的图片底部包含 `SIZE CHART (Inch)`；同一 HTML 的尺码插件配置也通过商品 HANDLE 精确绑定 `ODS5841` 表，两者的五个尺码成衣 Bust/Length 数值一致。[官网商品页](https://www.chicme.com/products/striped-halter-sleeveless-tank-causal-golden-button-decor-breathable-knit-top)、[正文原图](https://cdn.shopify.com/s/files/1/0748/9457/3625/files/ODS5841.jpg?v=1780996154)；本地原始证据见 [HTML](brand_product_page.html)、[图片](brand_description_size_image.jpg)、[专属配置提取](brand_handle_matched_chart.json)。

**这些是 CHICME 官网款式的声明尺寸，不是 TikTok 差评 SKU 已确认尺寸。** 本任务未取得 TikTok 商品 `1732331935794958838`、所购 SKU `1732475515663127030` 与 CHICME 商品/变体之间的可靠 ID 映射；官网默认 khaki / S 不能作为该买家购买 S 的证据。相同标题或相似外观也不能独立证明相同批次、相同尺码规格。未把以下尺寸写入生产 SKU 证据或修改业务判断。

## 专属成衣尺码表

以下为官网原图的 `Product Measurement`，原始单位 Inch。源码专属配置 `contentConfigs[0].tableData` 也给出相同数值和 `defaultUnit: "Inch"`。[图片](brand_description_size_image.jpg)、[配置](brand_handle_matched_chart.json)。

| 尺码 | Bust（Inch） | Length（Inch） |
|---|---:|---:|
| S | 33.5 | 19.3 |
| M | 35.0 | 19.7 |
| L | 37.4 | 20.3 |
| XL | 39.8 | 20.9 |
| XXL | 42.1 | 21.5 |

原文明确区分 Product Measurement 与 Body Measurement；未提供完整测量步骤、容差或实物测量结果，因此不能把本表描述为本次实测。Bust 的具体测量路径、平铺/周长口径及拉伸状态仍待确认，不据此自动生成项目 `measurements.basis`。

官网同图的 `Body Measurement` 另列 Bust：S 33.9–35.8、M 36.2–37.8、L 38.2–40.6、XL 40.9–42.1、XXL 42.5–43.7（表标题 Inch）。名为 `Length` 的列分别为 `5′2″–5′4″`、`5′4″–5′6″`、`5′6″–5′7″`、`5′8″–5′9″`、`5′8″–5′9″`。后者看起来是身高范围，但原标签保留为 Length，不把它当成衣长。图中 Fit Type 指向 Slim，Stretch 指向 High；这些也是品牌宣传/选择说明，不是性能实测。[图片](brand_description_size_image.jpg)

## 地区尺码标签存在差异

正文图片地区列写的是 `UK Size`；插件配置的地区列写的是 `US Size`。两份原文均保留，不互相覆盖，不将下表解释为经过核验的英美尺码换算。[图片](brand_description_size_image.jpg)、[配置](brand_handle_matched_chart.json)。

| 字母码 | 正文图片 UK Size | 插件配置 US Size |
|---|---|---|
| S | 8–10 | 6–8 |
| M | 12 | 10 |
| L | 14 | 12–14 |
| XL | 16 | 16 |
| XXL | 18 | 18 |

插件 `appData.appStatus` 为 false，而匹配表自身 `status` 为 true。因此插件在实际浏览器中是否呈现未验证；专属尺码表的另一项直接证据是商品正文引用的可读取原图。表绑定条件为 `HANDLE EQUALS striped-halter-sleeveless-tank-causal-golden-button-decor-breathable-knit-top`，不是把全站任一通用表套用到本款。配置 id 为 `tcVgs3uRVHAT1rktUE3Z`，name 为 `ODS5841`，其 updatedAt 为 `2026-06-09T07:15:09.027Z`；该时间是配置自报更新时间，不是本次采集时间。[提取定位](brand_product_data.json)、[配置原值](brand_handle_matched_chart.json)

## 商品身份和可选变体

官网商品标题为 `Striped Halter Sleeveless Tank Causal Golden Button Decor Breathable Knit Top`，商品 ID 为 `8216081104953`，vendor 为 `Chicme`，类型为 `Knit Top`。`ODS5841` 同时出现在表名、正文图名与各变体 SKU 前缀中，是一致的品牌款式标识线索。官网标签和描述声明 `100% viscose`，不等于 TikTok 所购 SKU 已证实成分，也不等于实验室检测。[完整商品对象](brand_full_product.json)、[商品配置](brand_product_data.json)

源码提供 khaki、Black、Pink 三色及 S/M/L/XL/XXL 五种尺寸。以下为核验时点的 `available` 展示状态，不代表库存数量、下单成功或交付承诺。官网初始选中变体为 khaki / S。[完整商品对象](brand_full_product.json)、[初始选中变体](brand_page_selected_variant.json)

| 颜色 | 尺码 | 官网 variant ID | 官网 SKU（保留原大小写） | available |
|---|---|---|---|---|
| khaki | S | 45633561919545 | ODS5841-kh-S | true |
| khaki | M | 45633561952313 | ODS5841-kh-M | true |
| khaki | L | 45633561985081 | ODS5841-kh-L | true |
| khaki | XL | 45633562017849 | ODS5841-kh-XL | true |
| khaki | XXL | 45907083395129 | ODS5841-kh-XXL | true |
| Black | S | 45642446766137 | ODS5841-bK-S | true |
| Black | M | 45642446798905 | ODS5841-bK-M | true |
| Black | L | 45642446831673 | ODS5841-bK-L | true |
| Black | XL | 45642446864441 | ODS5841-bK-XL | true |
| Black | XXL | 45907083460665 | ODS5841-bk-XXL | true |
| Pink | S | 45643705417785 | ODS5841-pi-S | false |
| Pink | M | 45643705450553 | ODS5841-pi-M | false |
| Pink | L | 45643705483321 | ODS5841-pi-L | false |
| Pink | XL | 45643705516089 | ODS5841-pi-XL | false |
| Pink | XXL | 45907083493433 | ODS5841-pi-XXL | true |

## 来源、方法与验证

对给定官网链接做了一次 Web 搜索用于定位；最终结论全部基于随后一次公开 HTML GET 和一次正文所引用图片 GET。未使用浏览器、登录、购物车、采购、消息、收费采集或 1688 查询。一次本地 BeautifulSoup 导入因环境未装该包失败，随后改用 Python 标准库对已下载 HTML 解析，没有重新请求官网。

原始 HTML 保存响应体字节，见 [请求及哈希](brand_product_page_request.json)；不是浏览器屏幕截图。图片保存原字节，见 [图片请求及哈希](brand_description_size_image_request.json)，已目视核对图片底部表格。JSON 文件是从原始 HTML 解码提取的对象，均标明原文件和脚本定位，不冒充独立接口响应。完整商品对象来自 `const product =` 赋值；品牌配置对象来自 `script.mpSizeChart-script`。只解析数据，不执行网页 JavaScript。

最小验收：原始响应可复查且哈希一致；专属表精确匹配目标 HANDLE 且匹配唯一；全部 15 个变体与原始对象一致；原图五行成衣数值与绑定配置一致；报告不填补 TikTok 映射或用户目标尺寸。离线结果见 [核验记录](brand_validation.json)。实物尺寸、测量口径、TikTok SKU 对应尺码、差评者希望减少多少及具体偏大部位均未验证。
