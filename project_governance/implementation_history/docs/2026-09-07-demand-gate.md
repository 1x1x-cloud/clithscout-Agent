# S1 需求卡普遍性门槛实施计划

目标：落实用户确认的三项同时成立规则，单条反馈归档为问题线索且不触发找货。业务规则唯一来源为 [V1 的 S1 章节](../../business_rules/docs/2026-09-06-clothing-demand-agent-v1-design.md)。

架构：保留现有正文规则与 SKU 关联，在需求卡生成前增加商品级样本评估。新增有来源的评价资料输入，说明全星级覆盖、完整性、有效性人工判定、买家去重与线程信息；程序不自行猜测这些事实。未满足门槛仍输出 problem_signals，只有合格信号进入 demand_cards 和查询规划。历史回放读取已归档分析并明确标为历史规则，不重新查网或改写旧记录。

技术：现有 Python 标准库、unittest、JSON 命令行输入，不新增依赖或联网采集。

- [x] 在 quality_assurance/regression/tests/test_demand_gate.py 先增加反例和边界测试：1/2条只留线索；5条样本中3人同问题通过；3/15恰好20%通过；3/16不足；3/4样本不足；疑似账号、同文和线程去重；身份和覆盖未知不通过。
- [x] 新增 demand_discovery/demand_cards/src/prevalence.py：评估分母、独立支持、来源完整性以及三项门槛；校验评价资料输入。
- [x] 接入 builder.py、analyze.py；复用现有 normalizer 和去重签名，不修改原始评价形态；保留支持原文、SKU、有效与排除原因以及每项门槛结果。
- [x] CLI/流水线增加 --review-evidence，保存输入与 problem_signals.json；报告和人工队列明确区分线索/需求卡；查询规划只接受通过门槛的需求卡。
- [x] 历史回放保留归档分析并标明规则来源；调整下游合成测试样本，覆盖新规则下真实可通过的输入，不能靠配置关闭门槛。
- [x] 更新业务规范、入口、状态；完整75项回归、真实16条离线分析、历史回放和文件保全通过；独立代码审查的1项P2修复并限定复核通过，见 [交付报告](../../../quality_assurance/delivery_checks/records/demand_gate_20260907/REPORT.md)。

验收命令：项目 venv 的 python.exe -B -m unittest quality_assurance.regression.tests.test_demand_gate -v；完整回归使用 workflow_execution/launcher/scripts/run.ps1 -Test。实测结果保存在 quality_assurance/delivery_checks/records/demand_gate_20260907，测试数据与业务真实数据分开。
