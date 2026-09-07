# Apify API 接入检查

核验日期：2026-09-06。状态以 [TASK_STATE.md](../../../project_governance/project_state/docs/TASK_STATE.md) 为准。

## 后续实际采集入口

2026-09-07已按用户最新要求完成[三商品全星级Apify采集](keyword_products_apify_20260907/REPORT.md)，包含实际输入、限定执行脚本、运行回执、366条API评价及验收记录。后续评论采集路径和授权范围以TASK_STATE.md顶部最新确认维护；下方仅保留最初只读接入的历史状态。

## 成功验证快照：2026-09-06 15:21 UTC

用户已通过手动打开的密码窗口保存有效 Token。以用户执行身份读取 Windows 凭据后，运行信息、数据集元数据、数据集 items 三次 GET 均返回 HTTP 200；下载 16 条记录，与用户原附件按 reviewId 逐字段对账全部一致，顺序亦一致。没有发起新 Actor 运行、二星采集或定时任务。

- [验证记录](authenticated_20260906_152135/verification.json)：请求状态、逐字段比较和限制。
- [API 评价快照](authenticated_20260906_152135/api_reviews.json)：本次通过 API 获取的 16 条评价，不覆盖用户原附件。
- [运行选定字段](authenticated_20260906_152135/run_selected_fields.json)和[数据集选定字段](authenticated_20260906_152135/dataset_selected_fields.json)：标注为选定字段，不冒充完整原响应。
- [只读验证脚本](verify_existing_run.py)：仅验证已知运行，不含新建采集或调度操作。

只读访问已接通，无需重新配置凭据。沙箱账户不能访问用户的 Windows 凭据，后续访问需用用户执行身份；不得因沙箱返回缺失而重复要求用户输入 Token。新运行权限、连续采集、费用上限与业务数据完整性尚未验证。

## 以下为此前失败与修复过程

后续配置诊断：沙箱使用独立 Windows 身份，看不到用户的凭据；在用户身份下可读取该项，但实存内容只有 U+0016（Ctrl+V），没有 Token 文本。两次携带该无效值的请求返回空正文 HTTP 400，随后停止网络请求并定位输入问题。已改用支持粘贴的掩码密码窗口 [configure_apify_token.ps1](configure_apify_token.ps1)，保存时经标准输入管道交给 [store_apify_token.py](store_apify_token.py)，不把密钥写入命令参数或项目文件。详见 [诊断记录](credential_diagnosis.json)。不要重复使用下方历史 getpass 输入方式；新的保存状态见 token_input_status.json。

## 实际结果

已从项目 Python 环境直接向 Apify API 发出一次 GET 请求，访问用户截图所示运行；没有连接 Chrome，也没有启动新采集。服务返回 HTTP 403，错误为 `insufficient-permissions`，要求有效 API token 及对应权限。实际记录见 [run_probe.json](run_probe.json)。

API 网络请求已经到达服务端；账号/资源认证尚未完成。运行结果没有通过 API 下载成功，原来的 16 条分析仍来自用户附件，不能说本次 API 已取回它们。

检查范围：当前进程的 Apify 环境变量、用户/系统 APIFY_TOKEN 与 APIFY_API_TOKEN 环境变量，以及项目专用的 Windows 凭据项；均未配置。没有枚举其他服务的凭据，没有显示任何密钥。

本机已有 keyring，实际后端为 `keyring.backends.Windows.WinVaultKeyring`；CLI 的 `set <service> <username>` 命令已通过帮助输出核对。

## 旧终端输入方法（当前不再使用）

1. 在 Apify Console 的 Integrations 页面取得有权访问目标运行的 API token。[官方认证说明](https://docs.apify.com/api/v2#authentication)
2. 在本机 PowerShell 中执行以下命令，按隐藏输入提示粘贴 token 并回车。此命令使用 Windows 凭据管理器，不把 token 写入项目文件或命令行参数。

```powershell
& 'C:\Users\86130\Documents\ChatGPT\yuans\.venv-1688-pilot\Scripts\python.exe' -m keyring set clothing-agent-apify APIFY_TOKEN
```

凭据位置约定：service 为 `clothing-agent-apify`，username 为 `APIFY_TOKEN`。无需在聊天里发送 token。此文档只提供设置方法，助手没有运行 set 或写入凭据。

## 配置后的验证顺序

- 在程序内从指定 keyring 项读取 token，并放入 HTTPS 请求的 Authorization Bearer 头；不打印 token、不放入 URL、不保存带认证头的日志。
- 先只读本次运行与其 defaultDatasetId 的结果，校验是否与用户提供的 16 条记录对应。
- 原始 API 返回另存新快照，核对评价 ID 与原文；不覆盖用户原附件。
- 新采集调用、预算、持续频率分别落实；本次接入检查未发出任何启动、付费或调度请求。

官方 Get run 文档描述可凭运行 ID 读取部分字段，但本次目标实际返回 403，应以实际资源权限为准；不重复无凭据请求。[Get run](https://docs.apify.com/api/v2/actor-run-get) / [Get dataset items](https://docs.apify.com/api/v2/dataset-items-get)

本次是一次清晰的权限响应，不是三次失败熔断；没有自动审批拒绝。下一步缺少的是用户本机的 API 凭据配置。
