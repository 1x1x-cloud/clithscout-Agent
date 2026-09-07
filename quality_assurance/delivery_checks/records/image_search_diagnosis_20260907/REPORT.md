# 网页搜到、Skill 返回空：诊断记录

核验日期：2026-09-07（Asia/Shanghai）。本次只读取原图并检查本地请求构造，没有新增1688搜索，没有修改业务代码、筛选参数或历史快照。

## 已确认

1. 用户提供的[网页截图](C:/Users/86130/AppData/Local/Temp/codex-clipboard-c6bf7c41-9394-4a42-a220-8e493dc91557.png)显示多款外观高度相似的条纹挂脖上衣；网页入口是 `air.1688.com/kapp/1688-search/pc-image-search`，页面有主体框选，地址含 `region`、`yoloCropRegion`。截图不能用于取得完整商品身份、SKU或供货证明。
2. [上次CLI快照](../../../../workflow_execution/run_history/records/20260906T165943Z_fc9a7de8/searches/QI-eb1c8aff42a0fae9.json)的商品列表本身为空，完整工具文案为：

   > 未找到匹配商品

   这不是尺码、面料或SKU核对后被全部排除。[项目解析器](../../../../product_sourcing/result_parsing/src/parser.py)也没有把非空列表筛成空列表。[离线探针](offline_request_probe.json)验证了非空哨兵列表可以原样通过；哨兵不是商品证据。
3. [适配器](../../../../product_sourcing/skill_adapter/src/client.py)固定使用 `scoreLevel=high`、`tags=4306497`、`purchaseAmount=1`、`pageSize=3`。Skill的[参数文档](../../../../product_sourcing/1688_skill/vendor/1688-product-find/references/capabilities/image_search.md)将tags定义为品池标签。Skill通过 `skills-gateway.1688.com/api/find_product/1.0.0` 搜索，与网页入口不同；未取得证明两者检索范围一致的资料，也没有证据确定标签对应什么具体商品池。
4. 上次传入的是TikTok CDN的WebP网址。[本次读取](source_fetch.json)返回HTTP 200、`image/webp`，解码为RGB、800×800、29,344字节；已查看[原图副本](source_image.webp)，衣服外观与截图一致。本机现在能读取图片，不证明1688网关当时也能读取和解码。
5. [Skill图片预处理代码](../../../../product_sourcing/1688_skill/vendor/1688-product-find/scripts/_image.py)注明“API 仅稳定支持 JPEG”，但URL分支直接传网址，不下载、不转格式。[图片服务](../../../../product_sourcing/1688_skill/vendor/1688-product-find/scripts/capabilities/image_search/service.py)的URL请求中图片字节为空；本地WebP则会转JPEG后以Base64上传。离线拦截请求已复现这一差异，其他四个筛选参数保持相同。
6. `source_image`是Skill对输入路径的原样回填，`success=true`表示该调用路径未抛错。它们不能证明远端成功读取或识别图片。上次存档是完整CLI输出，没有保存网关原始HTTP响应或远端图片解码状态。

## 判断及待确认项

已经确定两边的输入处理和搜索条件不同；目前不能把空结果归因于某一个参数，更不能据此判断该款没有货源。优先排查网址取图/WebP处理，其次是品池与相关性限制；网页主体框选也可能影响结果。这些是排查假设，不是已验证根因。

最小下一步是一次受控诊断查询：使用本次由Skill预处理生成的同一主图[jpeg_input.jpg](jpeg_input.jpg)，保持 `high`、`4306497`、采购件数1、最多3款不变，只改变图片传入方式。图片仍为800×800，未裁剪；SHA-256见离线探针。该查询尚未执行，原先一次真实查询的授权已使用。

如果本地JPEG能返回商品，说明更换输入路径可以恢复召回，但仍不能单独区分外链抓取、WebP解码或服务时点变化；如果仍为空，也不能直接断言品池是原因。后续检验应一次只改变一个条件，并保留原始返回。

## 验收范围

- 实际原图读取、类型、尺寸、字节数及哈希已记录。
- 离线请求构造与解析共5项检查通过；新增真实网关调用次数为0。
- JPEG仅为输入格式诊断资料；没有产生新商品、SKU或供货结论。
- 本次未修改生产代码，未重跑整个业务回归套件；离线探针不能代替真实召回验证。
