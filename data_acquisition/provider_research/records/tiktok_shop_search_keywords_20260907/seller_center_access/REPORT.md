# 美国搜索洞察后台访问核验

核验：2026-09-07 11:36（Asia/Shanghai）。用户已授权“开始下一步”，本次执行真实浏览器页面访问与只读核验。

## 已确认

连接的 Chrome 可列出标签页；读取官方指南和新标签页导航曾各发生一次超时，随后截图与 DOM 正文读取成功。不能将早先超时当作此次浏览器完全不可用。

访问 [美国搜索洞察入口](https://seller-us.tiktok.com/product/search-operations?shop_region=US) 后，实际来到 `https://seller-us.tiktok.com/settle/landing/?is_new_connect=0&shop_region=US`，标题为 TikTok Shop Seller Center | United States。页面要求提供资料、等待审核、通过验证后开始销售，未显示搜索洞察导航或关键词表。

点击一次 Shop 按钮后，返回正文未显示可切换的已有店铺。未点击 Get started 或 Start selling，未注册、接受卖家协议或提交身份资料。记录是页面观测，不能断言用户没有其他已开通美国店铺。

## 当前缺项

服装类目选项、关键词原始指标/单位、趋势及比较周期、导出与 API 均尚未读取，取得关键词记录0条。尚不能判断本账号能否访问搜索洞察或可否通过 Apify 获取。

已询问用户是否有已开通的美国店铺；若有，需切换到该店铺会话后继续。核验页已标记保留以供接续。没有启动付费 Actor 或改变生产规则。

选定页面观测与操作边界见 [observation.json](observation.json)，这是工具输出的结构化摘录，不是完整原始 DOM 或接口响应。[上一阶段官方来源](../official_sources.md)只说明文档能力，不能替代本次账号实测。
