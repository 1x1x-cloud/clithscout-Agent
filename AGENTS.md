# ClothScout 项目协作入口

适用于本目录及其子目录。本文维护 Agent 的阅读顺序和任务导航；全局工作规则沿用 [全局 AGENTS.md](C:/Users/86130/.codex/AGENTS.md)，业务定义和执行状态由下方文件分别维护。

## 开始任务

1. 确认当前工作目录和用户本次请求涉及的模块。开始新任务时，完整读取 [TASK_STATE.md](project_governance/project_state/docs/TASK_STATE.md)，据此识别已确认事项、已完成工作、待办与执行边界。
2. 读取 [START_HERE.md](project_governance/user_guide/docs/START_HERE.md) 获取当前运行入口、环境和目录约定；通过 [MODULE_INDEX.md](project_governance/workspace_registry/docs/MODULE_INDEX.md) 定位目标模块。
3. 按下表读取本次工作所需的唯一真源。沿用已有确认和有效证据，仅对影响当前任务的缺失信息提出问题。

## 按任务读取

| 任务 | 必须读取的来源 |
|---|---|
| 调整需求发现、证据结构、商品匹配、供货判断或业务验收 | [V1 方案与验收情境](project_governance/business_rules/docs/2026-09-06-clothing-demand-agent-v1-design.md) |
| 使用或修改商品字段、CTR、点击下单率及数据口径 | [字段字典](project_governance/business_rules/schemas/field_dictionary.csv) |
| 修改评论痛点识别 | V1 方案，以及 [现行规则代码](demand_discovery/pain_classification/src/rules.py) 和对应分类实现 |
| 执行或调整一轮分析 | TASK_STATE.md 中的轮次确认，以及 [运行配置](workflow_execution/run_configuration/config/current_round.json)；窗口和调用范围按该轮次核对 |
| 读取 Apify 既有运行、排查认证或规划新采集 | [Apify 接入记录](data_acquisition/apify_reviews/records/README.md)，以及 TASK_STATE.md 中的接入状态与授权范围 |
| 使用 1688 找货或修改适配器 | [项目内 1688 Skill](product_sourcing/1688_skill/vendor/1688-product-find/SKILL.md)，以及 TASK_STATE.md 中的 1688 数据口径与凭据注意事项 |
| 调整模块布局、索引或查阅历史证据 | MODULE_INDEX.md、[模块登记](project_governance/workspace_registry/config/modules.json) 和 [索引策略](project_governance/workspace_registry/config/index_policy.json)；原始证据按运行清单或引用读取 |

## 执行与文件维护

- 实际执行以 START_HERE.md 和当前启动脚本为准。使用项目独立 Python 环境；先区分离线分析、历史回放和联网模式，再执行符合本次授权的命令。
- 延续现有模块职责和路径解析方式。历史实现计划、迁移脚本及恢复包用于追溯，不作为重建项目或重跑迁移的默认入口。
- 业务规则只在对应唯一真源修改，引用方保持路径指针。修改配置或代码时，核对其是否符合已确认业务规则；必要条件缺失时记录待确认项。
- 证据、运行结果和核验记录保存到相应模块的独立快照，并保留来源、时间和引用关系。历史记录的适用范围按其采集时点解释。
- 完成长任务的重要阶段后，更新现有 TASK_STATE.md 的目标、关键决策、进度、待办和证据路径；本文件保持导航职责。

## 交付前验收

- 文档变更：检查新增或修改的引用均可访问，且与唯一真源一致。
- 代码变更：按 START_HERE.md 的回归入口执行相关检查；涉及数据流时，补充对应离线分析或真实快照回放，并核对输出记录。
- 目录、启动环境或迁移兼容性变更：执行 START_HERE.md 的迁移验收入口，检查当前入口链接、原始文件保全及快照一致性。
- 业务判断变更：对照 V1 方案中适用的验收情境和实际证据核验；报告分别说明程序检查、业务证据和真实测品结果的验证范围。
- 交付说明列出实际改动、已执行的验证及未验证事项；历史通过记录只作为历史证据引用。
