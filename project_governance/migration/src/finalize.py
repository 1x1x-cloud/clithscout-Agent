"""Finish documentation and local migration verification tooling; no network calls."""
import json
from pathlib import Path
import os
import re

ROOT = Path('D:/clothscout')
SOURCE = Path(__file__).resolve().parents[1]
RECORD = ROOT / 'project_governance/migration/records/migration_manifest.json'


def write(path, text):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text.rstrip() + '\n', encoding='utf-8')


def main():
    record = json.loads(RECORD.read_text(encoding='utf-8'))
    mapping = record['source_to_destination']
    extras = {
        'CONTINUE_CLOTHING_AGENT.md': 'project_governance/user_guide/docs/START_HERE.md',
        'clothing_agent/README.md': 'project_governance/user_guide/docs/START_HERE.md',
        'clothing_agent/run.ps1': 'workflow_execution/launcher/scripts/run.ps1',
        'clothing_agent/config/current_round.json': 'workflow_execution/run_configuration/config/current_round.json',
        'clothing_agent/tests/test_pipeline.py': 'quality_assurance/regression/tests/test_pipeline.py',
        'clothing_agent/verify_delivery.py': 'quality_assurance/migration_validation/src/verify.py',
    }
    for source, target in extras.items():
        mapping[str((SOURCE / source).resolve())] = target
    for original, relative in list(mapping.items()):
        if not relative.endswith('.md') or relative.startswith(('workflow_execution/run_history/', 'product_sourcing/1688_skill/')) or relative.endswith('START_HERE.md'):
            continue
        old = Path(original)
        if not old.exists():
            continue
        new = ROOT / relative
        def replace(match):
            target = match.group(1)
            if target.startswith(('https:', 'http:', '#', 'app:')):
                return match.group(0)
            resolved = str((old.parent / target).resolve())
            if resolved in mapping:
                return '](' + os.path.relpath(ROOT / mapping[resolved], new.parent).replace('\\', '/') + ')'
            return match.group(0)
        content = re.sub(r'\]\(([^)]+)\)', replace, old.read_text(encoding='utf-8-sig'))
        new.write_text(content, encoding='utf-8')
    core = {
        'project_governance': '项目治理：唯一状态、业务标准、目录登记、迁移恢复',
        'data_acquisition': '数据获取：Apify、TikTok商品、FastMoss、Pinterest及趋势资料',
        'evidence_processing': '证据处理：身份去重、记录规范化、服装上下文',
        'demand_discovery': '需求发现：痛点规则、分类、需求卡及分析流程',
        'product_sourcing': '采购找货：查询规划、1688适配、结果解析、Skill副本',
        'product_matching': '商品匹配：具体SKU、满足/冲突/未知、供货门槛',
        'human_review': '人工复核：证据、需求与商品待办队列',
        'report_delivery': '报告交付：原文引用、完整工具表与对照解释',
        'workflow_execution': '工作流执行：配置、CLI、启动、流水线及运行快照',
        'quality_assurance': '质量验证：原回归测试、记录核验、迁移验收',
        'runtime_support': '运行支持：项目路径、时间、标识、JSON、异常与独立环境',
    }
    write('project_governance/user_guide/docs/START_HERE.md', '''# ClothScout 项目入口

项目根目录为 **D:\\clothscout**，由用户指定。根目录只放核心模块文件夹；每个核心模块下按独立职责继续拆分，代码、配置、资料、测试进入相应 src/config/docs/records/tests/scripts 等目录。

先读 [当前唯一项目状态](../../project_state/docs/TASK_STATE.md)，再读 [模块索引](../../workspace_registry/docs/MODULE_INDEX.md)。规则唯一来源是 business_rules/ 中的 V1 设计和字段字典；历史档案及恢复包不作为现行规则重复索引。

## 运行

在 PowerShell 中使用完整路径，可从任意当前目录启动：

```powershell
# 离线分析原16条评价，不联网
& 'D:\\clothscout\\workflow_execution\\launcher\\scripts\\run.ps1'

# 回归测试
& 'D:\\clothscout\\workflow_execution\\launcher\\scripts\\run.ps1' -Test

# 迁移完整性与真实快照一致性验收（不联网）
& 'D:\\clothscout\\workflow_execution\\launcher\\scripts\\run.ps1' -VerifyMigration

# 重放迁移前真实查询结果，不把历史报价视为刷新值
& 'D:\\clothscout\\workflow_execution\\launcher\\scripts\\run.ps1' -ReplayRun 'D:\\clothscout\\workflow_execution\\run_history\\records\\20260906T154237Z_38cd565c'

# 需要时：读取配置中的既有Apify运行并执行有上限的1688搜索
& 'D:\\clothscout\\workflow_execution\\launcher\\scripts\\run.ps1' -Live
```

若本机执行策略阻止脚本，可用相同项目环境直接启动：

```powershell
& 'D:\\clothscout\\runtime_support\\python_environment\\venv\\Scripts\\python.exe' -B 'D:\\clothscout\\workflow_execution\\launcher\\scripts\\launch.py'
```

自定义数据用 `-Reviews '完整JSON路径'`；Python CLI 还支持 `--config`、`--live-read`、`--existing-run-id`、`--live-search`。配置位于 [current_round.json](../../../workflow_execution/run_configuration/config/current_round.json)，观察窗口沿用原轮次，不会随迁移或日期变化自动滚动。

运行结果位于 workflow_execution/run_history/records/，每次独立目录；原始字段、证据、需求卡、搜索返回、SKU对照、人工复核、报告、清单及哈希均保留。

## 能力边界

已有功能是有限规则的 S1 最小流程。它可处理新评价ID，但不等于通用语言模型；模糊、否定、问询和未覆盖表达进入人工复核。现货供货核验、通用模型、新Actor启动、四平台趋势采集、测品反馈尚未实现，迁移没有把这些能力变成已完成。1688 Skill 本身含图片搜索代码，但流水线仍只调用文字搜索。

新 Python 环境位于本项目 runtime_support/python_environment/venv/，依赖锁在同模块 config/requirements.lock.txt。它使用本机已安装的 Python 3.10 基础运行时；不依赖旧工作区 venv。完整文件夹再次改位置后应重建 venv，因为虚拟环境自身并非跨路径可搬的完整Python发行版。

Apify 密钥继续由同一 Windows 用户的凭据管理器提供；1688 AK 沿用已有用户凭据配置。密钥没有复制到代码或恢复包。1688 Skill 源码已复制到 product_sourcing/1688_skill/vendor/，业务适配器使用相对根路径，未来更新由本项目自行决定。

## 恢复与文件保全

[迁移清单](../../migration/records/migration_manifest.json)记录源文件、目标路径、字节长度和SHA-256。`project_governance/migration/backup/original_project.zip` 保留迁移前全部155个Agent相关文件的原始字节，包括合并前代码；现行模块代码由原函数拆分，原始代码不丢失。

原工作区的功能代码与数据继续保留。paimon_model、开发者入驻网站、缓存和共享Git目录属于原工作区其他内容，明确保留原处，没有删除；恢复包不混入其他项目。活动状态入口迁至本项目，旧入口只保留指针。

目录独立不等于取消工具权限限制。索引策略是清晰区分当前规则、功能代码、原始证据和历史备份的配置，尚未实现向量数据库或宣称检索效果提升已验收。
''')
    index = ['# 核心模块索引', '', '| 二级核心目录 | 职责 | 三级独立模块 |', '|---|---|---|']
    registry = []
    for name, description in core.items():
        children = sorted(p.name for p in (ROOT / name).iterdir() if p.is_dir())
        index.append('| ' + name + ' | ' + description + ' | ' + '、'.join(children) + ' |')
        registry.append({'core_module': name, 'purpose': description, 'submodules': children})
    index += ['', '层级约定：项目根 → 核心工作模块 → 单一职责子模块 → src/config/docs/records/tests/scripts/vendor → 文件。',
              '', '拆分按职责和依赖边界进行；不为了增加目录数量把每行函数单独成模块。',
              '', '迁移原代码对应：analysis.py → 规范化/去重/痛点规则/分类/需求卡；providers.py → Apify/1688/结果解析/异常；matching.py → 查询规划/SKU核对；pipeline.py → 执行/报告/复核/记录核验/存储。',
              '', '[活动项目状态](../../project_state/docs/TASK_STATE.md) · [索引范围](../config/index_policy.json)']
    write('project_governance/workspace_registry/docs/MODULE_INDEX.md', '\n'.join(index))
    write('project_governance/workspace_registry/config/modules.json', json.dumps(registry, ensure_ascii=False, indent=2))
    write('project_governance/workspace_registry/config/index_policy.json', json.dumps({
        'status': 'scope_configuration_only_no_vector_database',
        'canonical_rules': ['project_governance/business_rules/docs/', 'project_governance/business_rules/schemas/', 'demand_discovery/pain_classification/src/rules.py'],
        'active_state': 'project_governance/project_state/docs/TASK_STATE.md',
        'code_glob': '*/*/src/*.py',
        'exclude': ['**/records/**', '**/backup/**', '**/vendor/**', '**/venv/**', '**/tests/**', '**/__pycache__/**', 'project_governance/migration/**', 'project_governance/implementation_history/**'],
        'evidence_policy': 'Source evidence is retrieved by manifest/reference when needed, not merged into current rule definitions'}, ensure_ascii=False, indent=2))
    state_path = ROOT / 'project_governance/project_state/docs/TASK_STATE.md'
    state = state_path.read_text(encoding='utf-8')
    old_env = str(SOURCE).replace('\\', '/') + '/.venv-1688-pilot/Scripts/python.exe'
    state = state.replace(old_env, 'D:/clothscout/runtime_support/python_environment/venv/Scripts/python.exe')
    state = state.replace('C:/Users/86130/.codex/skills/1688-product-find/SKILL.md', 'D:/clothscout/product_sourcing/1688_skill/vendor/1688-product-find/SKILL.md')
    state = state.replace('`clothing_agent/run.ps1`', '`D:/clothscout/workflow_execution/launcher/scripts/run.ps1`')
    banner = '''## 迁移接续（2026-09-07）

当前项目根已改为 **D:\\clothscout**，由用户指定；本文件是唯一活动状态。[新入口](../../user_guide/docs/START_HERE.md)和[模块索引](../../workspace_registry/docs/MODULE_INDEX.md)提供启动与目录说明。原工作区保留迁移前文件，不再维护第二份活动状态。

已按11个核心模块继续拆分独立子模块，迁移代码、155个原项目文件及1688 Skill源码；原始字节备份位于 migration/backup/，清单位于 migration/records/。新独立venv中的22项原测试、离线分析、真实历史快照重放已通过。完整保全与路径核验以 quality_assurance/migration_validation/records/ 的实际结果为准。没有新增收费采集或商品搜索。

API凭据继续由同一Windows用户安全存储提供，不导出密钥；新代码使用项目内1688 Skill副本和独立venv，不引用旧工作区作为运行依赖。基础Python仍使用本机 D:\\Python环境 安装。

以下保留完整业务背景与历史证据；原代码形态、旧脚本与旧路径描述仅代表当时状态，当前可执行入口以上述新说明为准。窗口继续沿用2026-08-30至09-06原轮次，不因迁移滚动。

'''
    state = state.replace('## 1. 新对话先做什么', banner + '## 1. 新对话先做什么', 1)
    state_path.write_text(state, encoding='utf-8')
    record['modular_replacements'] = {
        'clothing_agent/analysis.py': ['evidence_processing/review_normalization', 'evidence_processing/review_deduplication', 'evidence_processing/garment_context', 'demand_discovery/pain_classification', 'demand_discovery/demand_cards', 'demand_discovery/analysis_workflow', 'workflow_execution/run_configuration', 'runtime_support/text_identity', 'runtime_support/time_windows'],
        'clothing_agent/providers.py': ['data_acquisition/apify_reviews', 'product_sourcing/skill_adapter', 'product_sourcing/result_parsing', 'runtime_support/provider_errors'],
        'clothing_agent/matching.py': ['product_sourcing/query_planning', 'product_matching/sku_comparison'],
        'clothing_agent/pipeline.py': ['workflow_execution/pipeline', 'human_review/review_queue', 'report_delivery/markdown_report', 'quality_assurance/record_validation', 'runtime_support/json_storage'],
        **{key: [value] for key, value in extras.items()},
        'clothing_agent/__main__.py': ['workflow_execution/cli/src/main.py'],
        'clothing_agent/__init__.py': ['workflow_execution/pipeline/src/orchestrator.py'],
        'clothing_agent/.gitignore': ['project_governance/workspace_registry/config/index_policy.json'],
    }
    RECORD.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'core_modules': len(core), 'state': str(state_path)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
