# 三款服装商品：Apify 全星级评价采集

完成日期：2026-09-07（Asia/Shanghai）。按用户最新要求，确认商品ID后直接使用Apify采集评论，本次没有浏览器操作。评论来源选择与后续执行规则唯一维护于 [TASK_STATE.md](../../../../project_governance/project_state/docs/TASK_STATE.md)。

已启动并完成 **1次** `lurkapi/tiktok-shop-reviews-scraper` 运行：[NjEXpgqOIip3PeBcU](https://console.apify.com/actors/runs/NjEXpgqOIip3PeBcU)。构建0.0.8，2026-09-07 05:12:42–05:13:13 UTC；通过API下载 **366条评价**，366个不同评价ID，运行报告费用 **$0.73205**，低于本次$2上限。

## 实际取得的数据

| 商品 | 商品ID | API评价记录 | 原窗口内记录 | 窗口内非空正文 | 返回不同SKU ID |
|---|---|---:|---:|---:|---:|
| HoneyBadgercome 连衣裙 | 1732357239054307594 | 116 | 9 | 4 | 18 |
| VRCOMFY 前扣文胸 | 1732510609891758832 | 112 | 36 | 27 | 10 |
| Fashion forefront 牛仔裤 | 1731650530027868452 | 138 | 18 | 5 | 17 |
| 合计 | 三商品分别统计 | 366 | 63 | 36 | 不跨商品合并 |

“非空正文”还未排除纯赞美、复用内容及其他无效记录，不是去重后的有效评价数。三个商品各自的分母和问题占比不合并。原窗口保持 `2026-08-30T09:05:42Z ≤ timestamp < 2026-09-06T09:05:42Z`，没有因当前日期变化而滚动。

所有记录均返回商品ID、评价ID、SKU ID、原文（包括空正文）、星级、含时区的精确发表时间、商品标题/主图/URL、店铺ID和作者国家/购买标记。全部作者国家返回US，这仍是采集器报告值；独立买家ID和SKU颜色尺码字段没有返回。原始字段未据此推断或补填。

全量记录包括153条空正文，另有重复非空正文组；这些需按 [V1规则](../../../../project_governance/business_rules/docs/2026-09-06-clothing-demand-agent-v1-design.md)处理，不能直接拿366、63或页面总评价数计算痛点占比。作者handle/name经过遮蔽，昵称、头像、不同正文和已购标记均未用于确认独立买家。

## 输入、覆盖和费用核对

- [实际请求输入](actor_input.json)：仅3个商品ID，US、`starRating=0`、`withPhotosOnly=false`、`sortBy=newest`、每款最多300条，输出字段显式开启；无店铺采集。
- [运行回执](run_start.json)与[最终运行字段](run_latest.json)：固定构建0.0.8、512 MB、600秒、`maxTotalChargeUsd=2`、`restartOnError=false`。按次收费，未建立定时任务或自动重启。
- [平台保存的输入](submitted_input.json)只多出文档默认 `maxProductsPerShop=5`；所有提交字段保持一致，该默认不影响商品ID输入。最初下载校验因此暂停，核对并限定接受该默认后继续GET读取同一次结果；**没有重跑付费采集**。见 [差异核验](input_default_verification.json)。
- [运行日志（脱敏）](run_log.redacted.txt)显示3个商品分别写入116、112、138条，与本次源报告总量逐一一致，均未达到300条或费用上限。数据集读取前后的计数和修改时间保持一致，见 [下载来源](dataset_read_provenance.json)。
- 连衣裙比前次网页114条多2条，其余两款计数一致。两次采集时点和来源不同，差异原因未确认，未覆盖旧快照，也不将差值解释成增长率。

上述证据支持本次已取齐Actor公开流报告的数量，不等于证明平台全部历史、已删除或不可见评价完整。有效样本、独立买家、问题占比和适用尺码表仍待核验；本次没有生成需求卡或触发找货。

## 与已取得样本对账

前次保存的12条网页评价，全部在本次API结果中按同商品、同星级、规范化空白后的相同正文唯一匹配。原始API正文保留，网页转录中的引号/空白只在对账时规范化，没有修改两份来源。结果见 [12条对账](previous_sample_crosscheck.json)。

此前文胸“承托/包容不足”的单条反馈现取得：评价ID `7680670162944722701`、SKU ID `1732510617633002224`、时间 `2026-09-01T20:43:08.280Z`、2星、`authorVerified=false`。此前网页对应规格为 Nude、L；该关联来自两份证据唯一匹配，**不是Actor直接返回了颜色尺码**。该条仍不满足生成需求卡所需的证据条件。

## 文件与执行入口

- [完整API评价JSON](api_reviews.json)：366条，保留所有返回字段。
- [原窗口内JSON](window_reviews.json)：63条，字段原样保留，只按时间筛选。
- [采集汇总JSON](collection_summary.json) / [CSV](collection_summary.csv)：按商品列数量、星级分布、字段缺项及来源计数差异。CSV长ID须按文本导入。
- [离线下载验收](download_validation.json)：商品/店铺、字符串ID、精确时间、SKU、数据集稳定性、计费事件数量、12条旧样本及历史文件保全通过。
- [限定执行脚本](collect_once.py)：默认只离线核验；本次`start`已使用，标记文件会阻止重复启动。`collect`只读取同一次运行；新商品需另建采集输入/运行快照，不覆盖本记录。
- [参数和费用来源](actor_contract_research.md) / [账户读取的元数据](actor_metadata.json)：区分公开文档与本次实测。

当前交付是一次实际Apify采集及数据验收，并已落实后续评论走Apify的路径选择；尚未把新Actor启动合入通用S1命令行或实现无人值守采集。原始评价、旧浏览器档案和旧配置均保留；没有联系供应商、采购、1688请求或新的浏览器评论采集。
