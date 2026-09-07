# 迁移交付记录 · 2026-09-07

用户指定的新项目根为 **D:\clothscout**。当前业务状态唯一维护在 [TASK_STATE.md](../../project_state/docs/TASK_STATE.md)，本文件只记录迁移交付事实。

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
