# 默认JPEG图片输入交付

用户要求：修正默认图片输入。已将真实图片搜索接为“原商品主图下载 → JPEG转换及归档 → 以本地路径上传”，原图URL仍保留在搜索计划中。原商品、评价和SKU的来源绑定不变。

## 实际改动

- [图片准备模块](../../../../product_sourcing/skill_adapter/src/image_input.py)处理公网下载、TLS域名验证、图片解码、白底转换、尺寸限制、原图与JPEG的SHA-256、回放文件复制。资源限制及字段定义唯一维护于[流程规范](../../../../project_governance/business_rules/docs/2026-09-07-image-sku-workflow.md)。
- [搜索适配器](../../../../product_sourcing/skill_adapter/src/client.py)仅把来源与哈希校验通过的本地JPEG交给原1688 CLI，不再直接传主图网址。未改vendor文件、品池、高相关性或本轮查询上限。
- [流水线](../../../../workflow_execution/pipeline/src/orchestrator.py)在live图片模式搜索前准备文件；失败先保存证据，再停止查询。新记录增加image_input，完整CLI返回保持原样，按实际上传路径核对source_image。离线计划不下载，旧URL记录继续兼容，回放复制归档文件并保留原时间。
- [报告](../../../../report_delivery/markdown_report/src/render.py)列出原图/JPEG链接、哈希和下载时间，区分已归档图片与旧URL引用。用法见[项目入口](../../../../project_governance/user_guide/docs/START_HERE.md)。

## 验证证据

1. **完整回归62项通过。** 包括WebP转换、超尺寸缩放、PNG透明底、来源与哈希不匹配、坏图不搜索、查询上限、公网/TLS边界、旧新回放，以及原有评价和SKU核对。开发初始用例先确认未准备的URL会被旧适配器接受，再实现拒绝与JPEG接入。
2. **真实主图GET和转换通过。** [读取核验](real_image_verification.json)确认新代码下载原图29,344字节，生成86,594字节JPEG；SHA-256与此前实际搜出3款的上传文件完全一致。该步骤只读取主图，不调用1688。
3. **历史真实快照保持一致。** [回放核验](legacy_replay_verification.json)覆盖原图片URL空结果及原文字3款结果；商品判断、原CLI内容和查询时间一致。新JPEG记录另由集成测试验证：运行目录搬动后仍可回放，原图与JPEG字节保持一致，没有网络调用。
4. **独立审查发现并修复1项P2。** 部分RGB/L PNG使用透明色元数据，旧转换分支会变成黑底；先用两个模式复现，再统一RGBA白底合成。新增用例及完整62项回归通过。最终审查结论见[交付核验](verification.json)。
5. **保全与范围。** vendor和原始评价共48个保护文件与修改前哈希一致。修改前44个现有代码/文档文件备份在before_changes.zip；原始运行快照未覆盖。新代码运行版本为0.2.1-jpeg-input。

## 实际验证范围

本阶段新增1688搜索为0；没有新Actor、供应商消息、订单或新业务候选。主图读取和转换已实测，默认流水线的CLI参数、图片归档与返回对账以隔离网络的集成测试验证，未再执行一轮真实搜索。此前JPEG成功查询仍是历史证据，不能把本次程序修正描述成一次新的商品/库存刷新，也不保证任意图片都有搜索结果。
