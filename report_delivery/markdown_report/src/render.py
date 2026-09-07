"""ClothScout module; migrated without changing business thresholds."""
from demand_discovery.demand_cards.src.prevalence import POLICY

REASONS = {
    'missing_product_main_image': '缺少原商品主图',
    'conflicting_product_main_images': '同商品的主图记录存在冲突，需确认使用哪张',
    'invalid_product_main_image': '原商品主图 URL 无效',
    'missing_or_mismatched_image_evidence': '主图证据缺失或原商品身份不一致',
    'configured_query_limit': '达到本轮查询上限，留待后续处理',
    'exact_platform_product_sku_binding': '资料已按平台、商品和具体 SKU 对齐',
    'missing_exact_sku_specification': '缺少原商品或候选商品对应 SKU 的规格资料',
    'target_identity_mismatch': '目标资料与本条评价所购商品或 SKU 不一致',
    'missing_review_specific_target': '尚未提供与本条差评关联的明确目标',
    'missing_explicit_measurement_targets': '缺少目标部位、测量口径及可接受尺寸范围',
    'missing_explicit_material_targets': '缺少明确的目标面料成分要求',
    'explicit_ranges_only_no_fit_guarantee': '仅核对明确尺寸范围，实际合身效果待实物验证',
    'composition_only_performance_requires_sample': '仅核对成分比例，触感、透视、缩水等性能待实物验证',
}


def detail_text(detail):
    if 'material' in detail:
        def percent(value):
            return '待确认' if value is None else f'{value}%'
        return (f"{detail['material']}：原 SKU {percent(detail['original_percent'])}，"
                f"候选 SKU {percent(detail['candidate_percent'])}，目标最低 {detail['min_percent']}%")
    def measured(value):
        return '缺少同部位、同口径实测' if not value else f"{value['value']} {value['unit']}"
    target = detail['target']
    return (f"{target['name']}（{target['basis']}）：原 SKU {measured(detail['original'])}，"
            f"候选 SKU {measured(detail['candidate'])}，目标 {target['min']}–{target['max']} {target['unit']}")


def cell(value):
    return str(value if value is not None else "待确认").replace("|", "\\|").replace("\n", " ").replace("\r", " ").replace("<", "&lt;").replace(">", "&gt;")


def render_report(out, manifest, analysis, matches, searches, plans=None):
    summary = analysis["summary"]
    lines = ["# 服装差评 → 找货对照报告", "",
             "本报告由有限规则引擎自动生成；未覆盖、含糊和矛盾表达进入人工复核。", "",
             f"运行状态：**{manifest['status']}**；开始时间：{manifest['started_at']}。",
             f"观察窗口：{manifest['config']['window']['start']}（含）至 {manifest['config']['window']['end']}（不含）；US 为来源字段所报市场。", "",
             f"原始评价 {summary['raw_rows']} 条；窗口内 {summary['in_window_rows']} 条；窗口外 {summary['outside_window_rows']} 条；时间未知 {summary['unknown_time_rows']} 条。",
             f"当前需求卡 {summary['current_cards']} 张；商品对照 {len(matches)} 条；合格现货测品候选 {sum(m['eligible_for_test'] for m in matches)} 条。",
             f"未覆盖/需人工解释的记录 {summary['unhandled_rows']} 条；重复记录 {summary['duplicate_rows']} 条；ID内容冲突记录 {summary['id_conflict_rows']} 条。", "",
             "上述是返回记录数；各商品问题占比与独立买家人数须有全星级覆盖和去重依据。未知值不按零处理；占比仅适用于所列市场和窗口。", ""]
    evidence = {e["evidence_id"]: e for e in analysis["evidence"]}
    if manifest.get('analysis_rule_source') == 'archived_analysis':
        lines.insert(2, '历史分析回放：需求卡与查询计划沿用原快照规则，不代表本次重新达到普遍性门槛；没有启动新的商品查询。\n')
    if 'problem_signals' in analysis:
        lines.extend(['## 问题线索与需求卡门槛', '',
            f"同商品有效评价至少{POLICY['min_effective_reviews']}条、同问题独立买家至少{POLICY['min_independent_buyers']}人、问题占比至少{POLICY['min_problem_ratio']:.0%}，三项须同时满足。{POLICY['recommended_effective_reviews']}条为建议样本量。分母必须是有覆盖依据的全星级有效评价；不同正文不等于不同买家。", '',
            '| 商品 / 问题 | 有效样本 | 支持记录 / 有效支持 / 不同正文 / 独立买家 | 问题占比 | 状态 |',
            '|---|---|---|---|---|'])
        signal_quotes = []
        for signal in analysis['problem_signals']:
            if signal['scope'] != 'current':
                continue
            p = signal['prevalence']
            ratio = '待确认（覆盖或有效性依据不足）' if p['problem_ratio'] is None else f"{p['problem_ratio']:.1%}"
            lines.append(f"| {cell(signal['product_id'])} / {cell(signal['statement'])} | {p['effective_sample_count']} | {p['support_record_count']} / {p['effective_support_count']} / {p['distinct_support_text_count']} / {cell(p['independent_buyer_count'])} | {ratio} | {cell(signal['status'])} |")
            for ref in signal['support_evidence_ids']:
                e = evidence[ref]
                signal_quotes.extend(['', f"> {cell(e['original_text'])}", '',
                    f"线索证据：{ref}；评价 {cell(e['review_id'])}；原 SKU {cell(e['sku_id'])}。", ''])
        lines.extend(signal_quotes)
        lines.extend(['', '未达到门槛的线索不生成需求卡、不触发找货。排除、去重与未确认原因见 problem_signals.json；覆盖和买家依据见 review_evidence.json。', ''])
    if manifest.get('search_mode') == 'synthetic_test' or manifest['config'].get('sample_kind') == 'synthetic_example':
        lines.insert(2, '合成测试示例：评价、商品和规格为测试输入，不代表真实市场或供应商资料。\n')
    lines.extend(['## 当前需求与原文', ''])
    for card in analysis["demand_cards"]:
        if card["scope"] != "current":
            continue
        lines.extend([f"### {card['demand_id']} · {card['statement']}", "",
                      f"状态：{card['status']}；同商品不同正文信号 {card['distinct_text_signals']} 组（不是独立买家数）。", ""])
        for ref in card["support_evidence_ids"]:
            e = evidence[ref]
            lines.extend([f"> {cell(e['original_text'])}", "",
                          f"证据：{ref}；评价 ID：{cell(e['review_id'])}；来源商品：{cell(e['product_id'])}；时间：{cell(e['published_at'])}。", ""])
        missing_label = "原评论提取时的缺项（补充资料核对见下文）：" if manifest['config'].get('search_strategy') == 'image' else "待确认："
        lines.extend([missing_label + "；".join(card["unknown"]) + "。", ""])
    if not summary["current_cards"]:
        lines.extend(["本次未生成当前需求卡；不等于市场没有需求。", ""])
    image_plans = [p for p in (plans or []) if p.get('search_type') == 'image']
    if image_plans:
        lines.extend(["## 原商品主图 → 图片找相似款", "",
                      "主图来自评价记录 productMainImage。已准备的图片保留原文件、上传JPEG与SHA-256；离线计划及旧URL记录未必归档像素，以下逐项标明。相似度不证明同款、面料或尺寸。", ""])
        for plan in image_plans:
            lines.extend([f"- 原商品：{cell(plan['source_product_id'])}；所购 SKU：{cell('、'.join(plan['source_sku_ids']))}。",
                          f"- 主图：{cell(plan.get('image'))}",
                          f"- 查询计划：{ {'ready': '就绪', 'blocked': '待补主图资料', 'deferred_query_limit': '本轮暂缓'}[plan['status']]}；原因：{cell(REASONS.get(plan.get('reason'), '主图可用于查询'))}；证据：{cell('、'.join(plan['evidence_ids']))}。", ""])
            archived = next((r.get('image_input') for r in searches if r['plan']['query_id'] == plan['query_id']), None)
            if archived:
                lines.extend([f"- 原图归档：[{cell(archived['original']['file'])}]({archived['original']['file']})；SHA-256：{cell(archived['original']['sha256'])}。",
                              f"- 上传JPEG：[{cell(archived['jpeg']['file'])}]({archived['jpeg']['file']})；SHA-256：{cell(archived['jpeg']['sha256'])}。",
                              f"- 原图下载时间：{cell(archived['downloaded_at'])}；完整转换记录见 images/。", ""])
            else:
                lines.extend(["- 尚无完整JPEG输入归档；本项只保留URL来源，或图片准备失败（见 images/ 与执行问题）。", ""])
    lines.extend(["## 1688 工具原始展示", "", "以下表格为工具返回的原文；价格、卖点和配送标签均未独立核实。", ""])
    for record in searches:
        lines.extend([f"查询用途：{record['plan']['purpose']}。模式：{record['mode']}；来源检查时间：{record['checked_at']}。", ""])
        payload = record.get("payload")
        markdown = payload.get("markdown") if isinstance(payload, dict) else None
        lines.extend([markdown if isinstance(markdown, str) else "没有取得有效工具展示内容。", ""])
        if record.get("error"):
            lines.extend(["查询受限：" + record["error"] + "。不据此认定没有供给。", ""])
    if not searches:
        lines.extend(["本次没有执行商品查询。查询计划见 search_plan.json。", ""])
    lines.extend(["## 逐项商品核对", "",
                  "| 商品 ID / SKU | 满足（已提供资料对照） | 冲突 | 未知 | 结论 |",
                  "|---|---|---|---|---|"])
    for match in matches:
        def fields(status):
            return "；".join(c["condition"] for c in match["conditions"] if c["status"] == status) or "无"
        lines.append(f"| {cell(match['product_id'])} / {cell(match['sku_id'])} | {cell(fields('met'))} | {cell(fields('conflict'))} | {cell(fields('unknown'))} | {match['decision']} |")
    if any(m.get('spec_checks') for m in matches):
        lines.extend(["", "## 差评、尺码、面料与具体 SKU", "",
                      "满足仅表示已提供资料符合明确目标；引用内容和实物未自动验证，穿着效果及供货仍待复核。", ""])
        for match in matches:
            lines.extend([f"### 候选 {cell(match['product_id'])} / {cell(match['sku_id'])}", "",
                          f"候选主图：{cell(match['source_product'].get('image_url'))}；详情：{cell(match['source_product'].get('detail_url'))}。", ""])
            for source in match.get('source_reviews', []):
                lines.extend([f"> {cell(source['original_text'])}", "",
                              f"原商品 / SKU：{cell(source['product_id'])} / {cell(source['sku_id'])}；评价：{cell(source['review_id'])}；来源：{cell(source['source_url'])}。", ""])
            lines.extend(["| 评价 | 核对项 | 状态 | 依据与缺项 |", "|---|---|---|---|"])
            for check in match.get('spec_checks', []):
                status = {'met': '满足（资料对照）', 'conflict': '冲突', 'unknown': '待确认'}[check['status']]
                lines.append(f"| {cell(check['review_id'])} | {cell(check['condition'])} | {status} | {cell(REASONS.get(check['reason'], check['reason']))} |")
                if check.get('details'):
                    lines.append(f"| | 对照数值 | | {cell('；'.join(detail_text(d) for d in check['details']))} |")
                if check['dimension'] == 'sku':
                    for role, field in [('原 SKU', 'source_specification'), ('候选 SKU', 'candidate_specification')]:
                        source = check.get(field)
                        if source:
                            lines.append(f"| | {role}资料来源 | | {cell(source['source_ref'])}；核对时间：{cell(source['checked_at'])}；尺码标签：{cell(source.get('size_label'))} |")
                if check['dimension'] == 'size' and check.get('target'):
                    target = check['target']
                    lines.append(f"| | 目标资料来源 | | {cell(target['source_ref'])}；核对时间：{cell(target['checked_at'])} |")
            lines.extend(["", "资料原文、来源与核对时间：product_matches.json 的 spec_checks；输入归档：sku_evidence.json。", ""])
    lines.extend(["", "## 下一步复核", ""])
    if summary['current_cards']:
        lines.extend(["- 补逐项核对中仍待确认的所购尺码、目标及实测资料；“太大”本身不能推导 S 码或修身版。",
                      "- 核对替代商品的具体 SKU、规格、实际可采购状态、价格数量条件及交付信息。"])
    else:
        lines.extend(["- 先补同商品全星级评价覆盖、有效性与独立买家去重依据，再重新检查需求卡门槛；暂不进入找货或测品。"])
    lines.extend([
                  "- manual_review.json 保留未覆盖正文、异常、未查询需求及逐商品待办。",
                  "- 问题线索（含历史或其他市场）见 problem_signals.json；历史规则回放仍保留原 demand_cards.json，不混入新查询。", "",
                  "程序完成不代表业务候选合格。本版未接入通用语言模型、新 Actor 采集、四平台趋势或采购审批；未验证 CTR、点击下单率及推荐效果。", "",
                  "原始数据见 raw_reviews.json；逐条证据见 evidence.json；全部来源返回见 searches/；执行与校验见 manifest.json、validation.json。", ""])
    if manifest["errors"]:
        lines.extend(["执行问题：" + "；".join(manifest["errors"]), ""])
    (out / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
