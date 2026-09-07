# 默认图片输入修正实施计划

目标：落实用户已确认的“原主图下载 → 转JPEG → 上传”，不增加找货次数，不更改SKU判断。依据是同图JPEG真实对照已返回3款，见TASK_STATE中的对照报告。

架构：在现有skill_adapter/src增加image_input.py，负责有界公网下载、JPEG转换、图片凭据验证和回放复制。流水线只在live图片模式准备图片；原搜索计划保持不变，另存image_input及本地文件；适配器仅接受已准备且哈希匹配的JPEG。回放复制归档文件并保留原CLI回填路径，旧URL快照仍按旧来源核对。

技术：已有Python 3.10、Pillow、unittest，网络用标准库HTTP/SSL；不增加依赖、不改vendor。下载连接固定到已验证的公网IP，TLS校验原域名；重定向逐跳校验，最多3跳；5MiB输入/输出、20百万像素、800×800最长边、JPEG质量90、透明底转白色。超限或无效图片停止，不退回URL或文字。

1. [x] 添加回归用例test_image_input.py，首先证明当前适配器仍接受未准备的URL，违反新的输入约定：`with self.assertRaises(ProviderError): search_1688(plan, cli)`。再覆盖真实转换、失败不搜索、同图来源绑定、哈希篡改和无网络回放。
2. [x] 实现`prepare_image(url, run_dir, query_id)`，记录原文件/JPEG相对路径、哈希、尺寸、格式及下载时间；实现`verified_jpeg(image_input, source_url)`和`copy_image_input(image_input, source_run, target_run)`。图片路径限制在对应运行目录，下载错误按稳定错误码落盘。
3. [x] 流水线live分支先准备再调用`search_fn(dict(plan, image_input=...))`；保存完整未改写CLI返回，按实际上传路径检查source_image。replay/recheck分支复用图片凭据和文件，不重新下载。准备失败时实际search_calls为0。
4. [x] 适配器把`--image`设为校验后的本地JPEG；报告分清已归档像素与历史仅URL引用。原计划不增加字段，维持历史计划完全相等检查。
5. [x] 更新现有流程规范、START_HERE和TASK_STATE；跑针对性测试、完整回归、旧真实URL/文字快照回放、归档WebP与真实JPEG返回的离线链路检查。通过独立代码审查后完成交付；本次不追加真实搜索。

执行命令：项目venv运行`-B -m unittest quality_assurance.regression.tests.test_image_input -v`；完整回归为`workflow_execution/launcher/scripts/run.ps1 -Test`。验收记录存quality_assurance/delivery_checks/records/default_jpeg_input_20260907。当前目录无Git仓库，先保存before_changes.zip，不初始化仓库或提交其他文件。
