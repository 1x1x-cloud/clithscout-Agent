# 评价覆盖与去重依据输入

业务门槛唯一维护于 [V1 方案 S1](2026-09-06-clothing-demand-agent-v1-design.md)。本文定义程序接口和验证边界，不另设阈值。

## 输入和运行

原始评价 JSON 保持原格式。新增 `--review-evidence`（PowerShell 为 `-ReviewEvidence`）传入独立 JSON 资料；不修改原始评价，不从昵称、正文或 `authorVerified` 自动生成买家身份。省略该资料时仍归档线索，但不能确认全星级覆盖或独立买家人数。

以下仅展示字段结构，身份及来源均为占位示例，不能作为真实证据；`review_ids` 应填写该商品在当轮范围中完整导入的原始评价 ID，包括后续被排除的记录。

```json
{
  "schema_version": 1,
  "samples": [{
    "product_id": "example-product",
    "market": "US",
    "window": {"start": "2026-08-30T09:05:42Z", "end": "2026-09-06T09:05:42Z"},
    "rating_scope": "all",
    "complete": false,
    "review_ids": ["example-review"],
    "source_ref": "真实采集范围、全分页完成及星级筛选核验记录的位置",
    "checked_at": "2026-09-07T00:00:00Z"
  }],
  "reviews": [{
    "product_id": "example-product",
    "review_id": "example-review",
    "substantive": true,
    "buyer_id": null,
    "buyer_identity_verified": false,
    "thread_id": null,
    "suspected_reused_account": false,
    "is_repost": false,
    "source_ref": "正文有效性、身份或线程核验记录的位置",
    "checked_at": "2026-09-07T00:00:00Z"
  }]
}
```

每项资料必须有来源和含时区的核对时间。每商品最多一个 sample，每商品/评价最多一个 annotation，引用评价必须存在于输入。`complete` 只有取得当轮同市场、全 SKU、全星级完整评价覆盖证据后才能写 true；有一条好评或 Actor 成功结束不等于完整覆盖。配置窗口采用左闭右开；资料窗口须与配置原值一致，完整 ID 集须与导入范围一致。

`buyer_id` 使用来源内稳定、可核实的买家标识并带来源命名空间；匿名/遮蔽名称不作身份。`buyer_identity_verified` 是已核验声明，不是程序验证结果。同一买家多正文仍只计一个买家；只要有效支持中有身份未确认记录，独立买家总人数保留未知。疑似复用账号标记沿相同 buyer_id 传播，排除相关评价。

`thread_id` 采用稳定的来源线程标识；同商品同线程只保留一份有效评价参与计数。`is_repost=true` 排除已核验转载正文。程序自动处理相同评价 ID、大小写/空白规范化后相同正文，以及常见完整短句赞美；复制改写或未知复用关系需要有来源的人工标注。正文或线程去重按输入顺序保留首条有效记录，全部原始记录和被排除的 SKU 关联仍保留在 evidence.json。

`substantive=false` 排除人工核验无实质内容的正文；true 可补充规则未覆盖表达的有效性依据，不能覆盖已识别纯赞美或结构错误。当前有限规则对否定、问询、转折等仍保守挂起，暂不支持通过该布尔值直接确认它们的问题分类；有未解释记录时，占比保持未知。`substantive` 不用于伪造问题提取。

## 输出和边界

- `review_evidence.json`：输入覆盖及去重资料归档。
- `problem_signals.json`：全部问题线索、原文引用及资格判定，包括历史或其他市场线索。
- `demand_cards.json`：仅保存本次通过门槛的需求卡；有效支持引用剔除去重和排除项。
- 每条 `prevalence`：支持记录数、有效支持数、不同正文数、独立买家数、有效分母、占比、三项门槛、覆盖状态、建议样本量提示、排除/未确认记录和来源。计数中的 support_record_count 是问题提取后的支持记录数；原始采集行数另见 summary。
- `search_plan.json` 只规划通过门槛的需求；未达标不会下载主图、调用找货或进入测品。报告与人工队列显示待补证据。

程序验证结构、引用和规则计算，不独立证明导入的覆盖/身份声明真实。低星采样即使条数很多也不得将 rating_scope 写成 all。必须先取得真实覆盖证据；全星级不要求样本必然包含每一种星级，要求采集未因星级而筛选。

`--replay-run`、`--recheck-run` 使用保存的分析与查询计划，仅回放旧结果或核对新 SKU 资料，不重新计算普遍性，也不能覆盖 review-evidence。旧规则需求卡有历史提示，不能据此新找货。若补齐评价资料，应使用 `--reviews` 与 `--review-evidence` 启动新分析；新快照不会改写旧快照。
