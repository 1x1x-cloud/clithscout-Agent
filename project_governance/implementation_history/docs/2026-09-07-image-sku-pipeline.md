# 图片召回与 SKU 核对实施计划

目标：实现用户指定的三步流程。业务与输入定义唯一维护在 [流程规范](../../business_rules/docs/2026-09-07-image-sku-workflow.md)。当前工作区无 Git 仓库，修改前代码保全于 quality_assurance/delivery_checks/records/image_sku_20260907/before_changes.zip。

架构：复用现有规范化、查询适配、流水线、报告与复核模块；新增 image_planner.py 负责主图计划，spec_evidence.py 负责资料校验，inspection.py 负责逐评价和 SKU 规格对照。通过显式图片模式接入，旧模式与回放配置保持兼容。实现使用项目 Python 3.10 和标准库，不修改 vendor。

- [x] 先在 quality_assurance/regression/tests/test_image_sku.py 写合成验收：主图来源与冲突、查询上限、图片 CLI 参数、不同 SKU、尺寸换算、材料资料、端到端和回放。运行测试并确认失败原因是功能缺失。
- [x] 更新 evidence_processing/review_normalization/src/normalizer.py；新增 product_sourcing/query_planning/src/image_planner.py；在 planner.py 分派图片模式；在 skill_adapter/src/client.py 接入 image_search。
- [x] 新增 product_matching/sku_comparison/src/spec_evidence.py 与 inspection.py，实现规范中的输入校验和三个维度对照。保留原 comparison.py 的文字模式行为。
- [x] 在 workflow_execution/pipeline/src/orchestrator.py 保存 SKU 资料、图片计划和核对结果；在 cli/src/main.py 与 launcher/scripts/run.ps1 增加图片模式、资料输入及回放衔接。
- [x] 更新 report_delivery/markdown_report/src/render.py 与 human_review/review_queue/src/builder.py，展示主图、原评价/SKU、候选 SKU、核对依据和待办；补充 START_HERE.md 的运行示例。
- [x] 执行 run.ps1 -Test、迁移验收与当前真实评价离线图片计划。真实图片调用在进程启动前被自动审批拒绝，已记录限制。
- [x] 独立代码审查、修复实际问题，核对修改范围与历史文件保全；将验证记录和后续缺项写入唯一 TASK_STATE.md。

- [x] 用户明确批准主图URL外传后，已执行一次最多3款的真实1688图片查询并核验离线回放；结果与后续缺项见唯一 TASK_STATE.md。
