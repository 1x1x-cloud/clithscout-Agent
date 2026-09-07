# 差评到找货对照报告 Implementation Plan

**Goal:** 把用户已同意的最小流程实现为本机可运行的 Python 命令，并用现有 Apify 运行与一次 1688 查询验证。

**Architecture:** 已有运行 API / 本地 JSON → 证据规范化和有限规则提取 → 需求卡 → 有上限的 1688 CLI 查询 → 三态核对与人工复核报告。每次运行保存独立快照，失败保留已完成阶段。

**Tech Stack:** Python 标准库、既有虚拟环境 keyring、既有 1688 CLI；不新增模型服务或持续收费采集。

业务定义引用 [V1 方案](../../business_rules/docs/2026-09-06-clothing-demand-agent-v1-design.md)；窗口、市场和授权状态引用 [TASK_STATE.md](../../project_state/docs/TASK_STATE.md)。本计划是本次 S1 实现切片，不替代三种方法的完整设计。

## 已确认设计及实现取舍

用户在助手提出“差评 → 自动需求卡 → 1688 找货 → 满足/冲突/未知报告”后回复“开始下一步”，沿用该批准执行，不重新索要流程许可。

先交付命令行和 Markdown/JSON 报告。与立即引入付费模型或完整网页相比，有限规则引擎可以用现有数据独立验收；代价是仅识别明确的常见表述。所有规则未覆盖、否定范围不明或矛盾表达保留原文、转人工复核，不冒充通用语言模型。规则不能从“太大”推导 S 码、修身版或成衣尺寸。

同品类查询作为探索，不能当作需求已符合。明确保留商品标题与具体 SKU 的关系；库存、物流、材质未核实不能升级。报告区分程序完成与现货候选合格。

## 文件和步骤

- [x] 1. `clothing_agent/tests/test_pipeline.py`：先写并运行失败的验收测试。覆盖新 ID、裤长痛点、赞美/否定、物流、重复 ID、窗口端点/缺时间/市场、注入文本、SKU 冲突、未知材质/库存、失败不当无货、分页与限制。
- [x] 2. `clothing_agent/analysis.py`：保留每条来源、去重分组、窗口检查、多标签规则及证据引用；仅同商品同问题聚合，不把不同商品评论合成独立用户。
- [x] 3. `clothing_agent/providers.py`：限定 Apify GET 主机/路径、禁止跳转、分页行数上限、凭据只在内存；调用已核对的 1688 CLI 参数，shell=False，有超时，失败不自动替代渠道。
- [x] 4. `clothing_agent/matching.py`：自动生成有品类依据的查询，执行次数受配置限制；按返回的 SKU/标题核对，供货缺项保持未知，支持快照回放。
- [x] 5. `clothing_agent/pipeline.py`、`__main__.py`：串联阶段、独立目录、检查点与失败记录；输出完整供应商表、需求卡、逐项核对、复核清单、运行清单和校验结果。
- [x] 6. `clothing_agent/config/current_round.json`、`run.ps1`、`README.md`：固化本轮已确认配置快照，提供离线运行、真实读取和查询、快照回放命令。配置的查询/下载上限是技术限制，不是样本量合格标准。
- [x] 7. 运行 `python -B -m unittest discover -s clothing_agent/tests -v`；离线样本验证；用户身份下真实 API 读取 + 一次最多 3 款的 1688 查询；完整快照回放。核验行数、原文、引用、无虚假现货候选。
- [x] 8. 更新唯一状态文件，记录本次实际实现范围、证据及未完成能力；不改旧原始数据，不触碰网站等子项目。

验收以测试输出及真实运行快照为证据。A01–A03、A08–A10、A12–A14 是本切片直接适用情境；S2/S3 与可采购状态的正向核验留在后续阶段，不声称全 V1 完成。无新 Actor POST、下单、供应商消息或定时任务。

API 文档核验日期 2026-09-06：[Get run](https://docs.apify.com/api/v2/actor-run-get)、[Get dataset items](https://docs.apify.com/api/v2/dataset-items-get)。采购参数引用本机 `1688-product-find/references/capabilities/text_search.md` 与实际 cmd.py。已有主技能与 reference 的 configure 前置矛盾沿用状态文件记录的解决方式：直接搜索，让命令执行 AK 前置检查，不读取或显示 AK。

