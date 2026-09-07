# ClothScout 项目入口

项目根目录为 **D:\clothscout**，由用户指定。根目录放核心模块文件夹及用户要求新增的 [AGENTS.md](../../../AGENTS.md) 协作入口；每个核心模块下按独立职责继续拆分，代码、配置、资料、测试进入相应 src/config/docs/records/tests/scripts 等目录。AGENTS.md 只维护 Agent 阅读顺序与任务导航。

先读 [当前唯一项目状态](../../project_state/docs/TASK_STATE.md)，再读 [模块索引](../../workspace_registry/docs/MODULE_INDEX.md)。规则唯一来源是 business_rules/ 中的 V1 设计和字段字典；历史档案及恢复包不作为现行规则重复索引。

以后在 Codex 中打开 **D:\clothscout** 作为项目目录，新任务先读取本入口或上方状态文件。当前对话的原工作目录不会因文件迁移自动改变。

## 新对话继续

在clothscout项目中新开对话，发送：

> 请完整读取 D:\clothscout\project_governance\project_state\docs\TASK_STATE.md，按顶部“新对话接续”从已完成的Apify采集继续后续流程，并把本阶段结果保存到项目。沿用已确认规则和已有数据。

当前断点、输入和下一阶段验收条件只维护于TASK_STATE.md顶部；无需复制整段旧聊天。落盘验收见[接续检查](../../project_state/records/handoff_20260907/verification.json)。

[本次迁移验收与保全说明](../../migration/docs/COMPLETION.md)记录验证范围。

## 运行

在 PowerShell 中使用完整路径，可从任意当前目录启动：

```powershell
# 离线分析原16条评价，不联网
& 'D:\clothscout\workflow_execution\launcher\scripts\run.ps1'

# 回归测试
& 'D:\clothscout\workflow_execution\launcher\scripts\run.ps1' -Test

# 迁移完整性与真实快照一致性验收（不联网）
& 'D:\clothscout\workflow_execution\launcher\scripts\run.ps1' -VerifyMigration

# 重放迁移前真实查询结果，不把历史报价视为刷新值
& 'D:\clothscout\workflow_execution\launcher\scripts\run.ps1' -ReplayRun 'D:\clothscout\workflow_execution\run_history\records\20260906T154237Z_38cd565c'

# 需要时：读取配置中的既有Apify运行并执行有上限的1688搜索
& 'D:\clothscout\workflow_execution\launcher\scripts\run.ps1' -Live
```

若本机执行策略阻止脚本，可用相同项目环境直接启动：

```powershell
& 'D:\clothscout\runtime_support\python_environment\venv\Scripts\python.exe' -B 'D:\clothscout\workflow_execution\launcher\scripts\launch.py'
```

自定义数据用 `-Reviews '完整JSON路径'`；评价覆盖与去重依据用 `-ReviewEvidence '资料JSON完整路径'`（Python 为 `--review-evidence`），格式及输出见 [评价依据输入](../../business_rules/docs/2026-09-07-review-evidence.md)。门槛见 [V1 方案 S1](../../business_rules/docs/2026-09-06-clothing-demand-agent-v1-design.md)；只有通过门槛才生成需求卡和找货计划，其他反馈保留在 problem_signals.json。原16条评价缺全星级和独立买家依据，新分析不会生成当前需求卡或触发找货。

Python CLI 还支持 `--config`、`--live-read`、`--existing-run-id`、`--live-search`。配置位于 [current_round.json](../../../workflow_execution/run_configuration/config/current_round.json)，观察窗口沿用原轮次，不会随迁移或日期变化自动滚动。

运行结果位于 workflow_execution/run_history/records/，每次独立目录；原始字段、证据、需求卡、搜索返回、SKU对照、人工复核、报告、清单及哈希均保留。

## 原商品主图找相似款与 SKU 核对

商品ID/链接确定后的评论采集路径按[TASK_STATE.md](../../project_state/docs/TASK_STATE.md)最新决定执行；已完成的[三商品Apify直接采集](../../../data_acquisition/apify_reviews/records/keyword_products_apify_20260907/REPORT.md)保存限定脚本、输入和完整结果。该次`start`已执行，禁止重复提交；`collect`只读取同一次运行。通用S1命令行目前仍只支持既有运行读取或本地评价导入，新Actor启动尚未合入该入口。

先离线分析评价并检查需求资格；只有合格需求才生成主图查询计划：

```powershell
& 'D:\clothscout\workflow_execution\launcher\scripts\run.ps1' -ImageSearch
```

真实图片搜索使用下列命令：读取本地评价并沿用本轮查询上限；默认先下载原商品主图、转JPEG，再向1688上传图片内容。运行环境需允许访问原图网站及1688。当前真实调用授权状态见 TASK_STATE.md。

```powershell
& 'D:\clothscout\runtime_support\python_environment\venv\Scripts\python.exe' -B 'D:\clothscout\workflow_execution\launcher\scripts\launch.py' --image-search --live-search
```

`-Live -ImageSearch` 则先读取配置中的既有 Apify 运行，再执行图片搜索。主图缺失、无效或冲突的商品进入人工复核。SKU资料格式见 [流程与输入规范](../../business_rules/docs/2026-09-07-image-sku-workflow.md) 和 [合成资料示例](../../../workflow_execution/run_configuration/config/sku_evidence.example.json)。示例身份和数值仅用于演示；实际核对需替换为有来源的原SKU、候选SKU及明确目标，未知项可以省略。

首次运行可加 `-SkuEvidence '资料JSON的完整路径'`；已有图片查询后，可离线导入新资料继续核对：

```powershell
& 'D:\clothscout\workflow_execution\launcher\scripts\run.ps1' -RecheckRun '已有图片运行目录的完整路径' -SkuEvidence '新资料JSON的完整路径'
```

每次复核另存报告与资料，保留原查询时间；`-ReplayRun` 按原资料回放。新图片运行在images/保存原图、上传JPEG及哈希元数据，回放直接复用；准备失败时记录错误并停止，不消耗搜索函数调用。技术限制和字段定义见[流程规范的图片输入与归档约定](../../business_rules/docs/2026-09-07-image-sku-workflow.md)。输出还包括search_plan.json的主图来源与跳过原因、sku_evidence.json的输入快照、product_matches.json的逐评价/SKU对照、manual_review.json的缺项及REPORT.md。规格资料对照通过后，实际穿着和供货仍待复核。

## 能力边界

已有功能是有限规则的 S1 最小流程。它可处理新评价ID，但不等于通用语言模型；模糊、否定、问询和未覆盖表达进入人工复核。现货供货核验、通用模型、四平台趋势采集、测品反馈尚未实现。新Actor启动已由限定脚本完成一次实测，尚未合入通用S1命令行。流水线已提供原商品主图找相似款及SKU资料核对入口；程序验证与真实接口验证的状态分别见TASK_STATE.md。

新 Python 环境位于本项目 runtime_support/python_environment/venv/，依赖锁在同模块 config/requirements.lock.txt。它使用本机已安装的 Python 3.10 基础运行时；不依赖旧工作区 venv。完整文件夹再次改位置后应重建 venv，因为虚拟环境自身并非跨路径可搬的完整Python发行版。

Apify 密钥继续由同一 Windows 用户的凭据管理器提供；1688 AK 沿用已有用户凭据配置。密钥没有复制到代码或恢复包。1688 Skill 源码已复制到 product_sourcing/1688_skill/vendor/，业务适配器使用相对根路径，未来更新由本项目自行决定。

## 恢复与文件保全

[迁移清单](../../migration/records/migration_manifest.json)记录源文件、目标路径、字节长度和SHA-256。`project_governance/migration/backup/original_project.zip` 保留迁移前全部155个Agent相关文件的原始字节，包括合并前代码；现行模块代码由原函数拆分，原始代码不丢失。

原工作区的功能代码与数据继续保留。paimon_model、开发者入驻网站、缓存和共享Git目录属于原工作区其他内容，明确保留原处，没有删除；恢复包不混入其他项目。活动状态入口迁至本项目，旧入口只保留指针。

目录独立不等于取消工具权限限制。索引策略是清晰区分当前规则、功能代码、原始证据和历史备份的配置，尚未实现向量数据库或宣称检索效果提升已验收。
