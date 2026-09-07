"""Switch documented project entry points after verified migration, preserving sources."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

root = Path('D:/clothscout').resolve()
source = Path('C:/Users/86130/Documents/ChatGPT/yuans').resolve()
assert root == Path('D:/clothscout') and source != root
manifest_file = root / 'project_governance/migration/records/migration_manifest.json'
manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
evidence = 'quality_assurance/migration_validation/records/20260906T162416547718Z/verification.json'
verified = json.loads((root / evidence).read_text(encoding='utf-8'))
assert verified['passed'] and verified['functional_tests'] == 24 and verified['original_files'] == 155
archive_path = root / manifest['archive']
assert hashlib.sha256(archive_path.read_bytes()).hexdigest() == manifest['archive_sha256']
old_entries = ['CONTINUE_CLOTHING_AGENT.md', 'tiktok_us_data_acceptance_2026-09-05/TASK_STATE.md']
source_inventory = {r['archive_member']: r for r in manifest['source_files']}
# Verify every original file before modifying the two authorized entry pointers.
assert all(Path(r['source']).is_file() and hashlib.sha256(Path(r['source']).read_bytes()).hexdigest() == r['source_sha256'] for r in manifest['source_files'])
with zipfile.ZipFile(archive_path) as archive:
    for name in old_entries:
        assert hashlib.sha256(archive.read(name)).hexdigest() == source_inventory[name]['source_sha256']

state_file = root / 'project_governance/project_state/docs/TASK_STATE.md'
state = state_file.read_text(encoding='utf-8')
state = state.replace('最后更新：2026-09-06（Asia/Shanghai）。', '最后更新：2026-09-07（Asia/Shanghai）。目录迁移已验收，当前活动项目为 **D:\\clothscout**；迁移结果与业务能力分别见下文。\n\n业务快照（2026-09-06）：', 1)
old = '已按11个核心模块继续拆分独立子模块，迁移代码、155个原项目文件及1688 Skill源码；原始字节备份位于 migration/backup/，清单位于 migration/records/。新独立venv中的22项原测试、离线分析、真实历史快照重放已通过。完整保全与路径核验以 quality_assurance/migration_validation/records/ 的实际结果为准。没有新增收费采集或商品搜索。'
new = ('迁移验收完成：**11个核心模块、45个独立子模块**；155个原项目文件的ZIP备份逐文件SHA-256一致，47个1688 Skill文件逐文件一致。独立venv内原22项测试与新增2项启动错误测试全部通过；离线分析、历史快照回放和入口链接检查通过。'
       '[迁移验收记录](../../../' + evidence + ')与[交付说明](../../migration/docs/COMPLETION.md)列明范围。原工作区功能代码与数据保留，旧状态及接续入口改为路径指针；迁移前原文完整保存在恢复包。没有新增收费采集或商品搜索。')
assert old in state
state = state.replace(old, new)
old = 'API凭据继续由同一Windows用户安全存储提供，不导出密钥；'
new = 'Apify与1688已有凭据在同一Windows用户身份下通过新环境本地读取检查（[记录](../../../quality_assurance/migration_validation/records/credential_availability.json)）；未联网重验服务端权限，不导出密钥。'
assert old in state
state = state.replace(old, new)
state_file.write_text(state, encoding='utf-8')

guide_file = root / 'project_governance/user_guide/docs/START_HERE.md'
guide = guide_file.read_text(encoding='utf-8')
guide = guide.replace('## 运行', '以后在 Codex 中打开 **D:\\clothscout** 作为项目目录，新任务先读取本入口或上方状态文件。当前对话的原工作目录不会因文件迁移自动改变。\n\n[本次迁移验收与保全说明](../../migration/docs/COMPLETION.md)记录验证范围。\n\n## 运行', 1)
guide_file.write_text(guide, encoding='utf-8')

completion = '''# 迁移交付记录 · 2026-09-07

用户指定的新项目根为 **D:\\clothscout**。当前业务状态唯一维护在 [TASK_STATE.md](../../project_state/docs/TASK_STATE.md)，本文件只记录迁移交付事实。

## 目录与代码

项目根只含11个核心目录，共45个独立子模块。核心层没有散落的源文件、配置或报告；文件继续归入子模块的 src/config/docs/records/tests/scripts/vendor。完整清单见 [模块索引](../../workspace_registry/docs/MODULE_INDEX.md)。原分析、数据接口、匹配和执行代码已按职责拆分；配置与启动路径根据新根计算。

## 最小验收结果

| 验收项 | 已验证结果 |
|---|---|
| 原文件保全 | 155个相关源文件进入ZIP，逐文件长度与SHA-256匹配；源目录迁移前逐文件再次核对 |
| Skill保全 | 47个1688 Skill文件逐文件SHA-256一致 |
| 目录结构 | 11个核心目录、45个子模块；模块登记与实际目录一致 |
| 独立运行 | 新venv运行，不依赖旧工作区代码、数据或Skill路径；切换到临时工作目录仍可运行 |
| 功能测试 | 原22项 + 新增2项启动器错误处理测试，24项通过 |
| 真实数据回放 | 原16条评价不变、需求卡不变；历史3条商品匹配决策不变，合格候选仍为0 |
| 文档入口 | 项目状态、使用说明、模块索引的文件链接可解析 |
| 凭据 | Apify/1688本地可读；不复制密钥，未联网重验服务端权限 |
| 独立审查 | 启动器失败JSON契约和Windows临时目录清理问题已修复并复审 |

结构化证据：[迁移验收](../../../quality_assurance/migration_validation/records/20260906T162416547718Z/verification.json)、同目录 tests.txt、[凭据检查](../../../quality_assurance/migration_validation/records/credential_availability.json)。验收期间未启动新Actor或采购搜索，未改变原轮次窗口。

## 文件保全与恢复

[迁移清单](../records/migration_manifest.json)维护源→目标映射、源码拆分对应、SHA-256和明确保留在原处的其他内容。恢复包为 [original_project.zip](../backup/original_project.zip)。ZIP中的目录相对于旧工作区，可解压到单独的空目录检查、提取原文件；不要直接覆盖现行模块。

旧功能代码、数据和用户未提交文件保留原处。只有旧 CONTINUE_CLOTHING_AGENT.md 和旧 TASK_STATE.md 改为新目录指针，原文已在ZIP中逐字节保全。其他项目 paimon_model、开发者入驻网站、共享Git及缓存保留原目录；不视为本Agent运行依赖。

迁移脚本留在本模块 src/，仅为迁移过程档案，正常使用走 [项目入口](../../user_guide/docs/START_HERE.md)。不要向已使用的目录重新运行初始化迁移脚本。

## 验证范围

本次验证文件保全、重构行为一致性、运行环境和路径。未新增四平台趋势采集、模型推理、图片找货串联、供货核验、向量数据库或测品反馈。目录结构和索引范围已配置，检索效果尚未实测。独立venv仍依赖本机基础Python安装，凭据仍依赖同一用户的本地安全存储。自定义目录不取消工具权限策略。
'''
completion_path = root / 'project_governance/migration/docs/COMPLETION.md'
completion_path.parent.mkdir(parents=True, exist_ok=True)
completion_path.write_text(completion, encoding='utf-8')

pointer = '''# 服装选品 Agent 已迁移

2026-09-07：用户指定的新项目目录为 **D:\\clothscout**。本文件仅为迁移指针，不再维护业务状态。

- [新项目入口](D:/clothscout/project_governance/user_guide/docs/START_HERE.md)
- [唯一活动项目状态](D:/clothscout/project_governance/project_state/docs/TASK_STATE.md)
- [模块索引](D:/clothscout/project_governance/workspace_registry/docs/MODULE_INDEX.md)
- [文件保全与验收说明](D:/clothscout/project_governance/migration/docs/COMPLETION.md)

后续请打开 D:\\clothscout 作为工作目录，并先读取其项目状态。旧功能代码与数据保留；本文件迁移前的完整原文位于 D:/clothscout/project_governance/migration/backup/original_project.zip 的对应路径。
'''
updates = []
for name in old_entries:
    path = (source / name).resolve()
    assert source in path.parents
    path.write_text(pointer, encoding='utf-8')
    updates.append({'source': name, 'before_sha256': source_inventory[name]['source_sha256'],
                    'after_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                    'reason': 'Authorized migration pointer; original bytes retained in verified ZIP'})
manifest['source_pointer_updates'] = updates
manifest['completed_at'] = datetime.now(timezone.utc).isoformat()
manifest['verification_record'] = evidence
manifest['credential_check'] = 'quality_assurance/migration_validation/records/credential_availability.json'
manifest['core_modules'] = 11
manifest['submodules'] = 45
for file in Path(__file__).parent.glob('*.py'):
    shutil.copyfile(file, root / 'project_governance/migration/src' / file.name)
manifest['generated_files'] = sorted({p.relative_to(root).as_posix() for pattern in ('*/*/src/*.py', '*/*/scripts/*.py', '*/*/scripts/*.ps1', '*/*/tests/*.py', '*/*/config/*', 'project_governance/*/docs/*.md') for p in root.glob(pattern) if p.is_file()})
manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'completed_at': manifest['completed_at'], 'root': str(root), 'source_pointers_updated': old_entries,
                  'original_files_deleted': 0, 'original_file_backups': 155, 'core_modules': 11, 'submodules': 45}, ensure_ascii=False, indent=2))
