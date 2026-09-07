# 核心模块索引

| 二级核心目录 | 职责 | 三级独立模块 |
|---|---|---|
| project_governance | 项目治理：唯一状态、业务标准、目录登记、迁移恢复 | business_rules、implementation_history、migration、project_state、user_guide、workspace_registry |
| data_acquisition | 数据获取：Apify、TikTok商品、FastMoss、Pinterest及趋势资料 | apify_reviews、fastmoss_catalog、pinterest_keywords、pinterest_saves、provider_research、shop_reviews、social_trends、tiktok_catalog |
| evidence_processing | 证据处理：身份去重、记录规范化、服装上下文 | garment_context、review_deduplication、review_normalization |
| demand_discovery | 需求发现：痛点规则、分类、需求卡及分析流程 | analysis_workflow、demand_cards、historical_examples、pain_classification |
| product_sourcing | 采购找货：查询规划、1688适配、结果解析、Skill副本 | 1688_skill、manual_pilot、query_planning、result_parsing、skill_adapter |
| product_matching | 商品匹配：具体SKU、满足/冲突/未知、供货门槛 | sku_comparison |
| human_review | 人工复核：证据、需求与商品待办队列 | review_queue |
| report_delivery | 报告交付：原文引用、完整工具表与对照解释 | markdown_report |
| workflow_execution | 工作流执行：配置、CLI、启动、流水线及运行快照 | cli、launcher、pipeline、run_configuration、run_history |
| quality_assurance | 质量验证：原回归测试、记录核验、迁移验收 | delivery_checks、migration_validation、record_validation、regression、source_acceptance |
| runtime_support | 运行支持：项目路径、时间、标识、JSON、异常与独立环境 | json_storage、project_paths、provider_errors、python_environment、text_identity、time_windows |

层级约定：项目根 → 核心工作模块 → 单一职责子模块 → src/config/docs/records/tests/scripts/vendor → 文件。

拆分按职责和依赖边界进行；不为了增加目录数量把每行函数单独成模块。

迁移原代码对应：analysis.py → 规范化/去重/痛点规则/分类/需求卡；providers.py → Apify/1688/结果解析/异常；matching.py → 查询规划/SKU核对；pipeline.py → 执行/报告/复核/记录核验/存储。

[活动项目状态](../../project_state/docs/TASK_STATE.md) · [索引范围](../config/index_policy.json)
