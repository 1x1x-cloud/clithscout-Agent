"""Compare exact SKU snapshots against explicit targets tied to each complaint."""
from product_matching.sku_comparison.src.comparison import compare_product
from product_matching.sku_comparison.src.spec_evidence import in_cm, name_key, number


def aggregate(statuses):
    if 'conflict' in statuses:
        return 'conflict'
    return 'met' if statuses and all(s == 'met' for s in statuses) else 'unknown'


def measurement_checks(source, candidate, target):
    targets = target.get('measurements', [])
    if not targets:
        return 'unknown', 'missing_explicit_measurement_targets', []
    def index(record):
        return {(name_key(m['name']), m['basis']): m for m in record.get('measurements', [])}
    originals, candidates = index(source), index(candidate)
    details = []
    for requirement in targets:
        key = (name_key(requirement['name']), requirement['basis'])
        original, offered = originals.get(key), candidates.get(key)
        detail = {'target': requirement, 'original': original, 'candidate': offered, 'status': 'unknown'}
        if original and offered:
            value = in_cm(offered['value'], offered['unit'])
            lower = in_cm(requirement['min'], requirement['unit'])
            upper = in_cm(requirement['max'], requirement['unit'])
            detail.update(status='met' if lower <= value <= upper else 'conflict',
                          candidate_cm=str(value), original_cm=str(in_cm(original['value'], original['unit'])))
        else:
            detail['reason'] = 'missing_matching_measurement_name_and_basis'
        details.append(detail)
    return aggregate([d['status'] for d in details]), 'explicit_ranges_only_no_fit_guarantee', details


def material_checks(source, candidate, target):
    targets = target.get('materials', {})
    if not targets:
        return 'unknown', 'missing_explicit_material_targets', []
    original = {name_key(k): v for k, v in source.get('materials', {}).items()}
    offered = {name_key(k): v for k, v in candidate.get('materials', {}).items()}
    details = []
    for name, minimum in targets.items():
        key = name_key(name)
        before = original.get(key, 0 if source.get('composition_complete') else None)
        after = offered.get(key, 0 if candidate.get('composition_complete') else None)
        status = 'unknown' if before is None or after is None else ('met' if number(after) >= number(minimum) else 'conflict')
        details.append({'material': name, 'min_percent': minimum, 'original_percent': before,
                        'candidate_percent': after, 'status': status})
    return aggregate([d['status'] for d in details]), 'composition_only_performance_requires_sample', details


def inspect_product(card, product, evidence, dossier):
    result = compare_product(card, product)
    if card.get('category') is None:
        result['style_related'] = 'unknown'
        result['conditions'][0]['status'] = 'unknown'
        result['decision'] = '待人工核验'
    result['conditions'][1]['reason'] = '规格对照仅针对已提供目标；实际合身、触感和其他穿着表现仍需实物复核'
    records = {(r['platform'], r['product_id'], r['sku_id']): r for r in dossier['sku_records']}
    targets = {(r['review_id'], r['issue']): r for r in dossier['review_targets']}
    offered = records.get(('1688', result['product_id'], result['sku_id']))
    support = [e for e in evidence if e['evidence_id'] in card['support_evidence_ids']]
    checks, source_reviews = [], []
    for review in support:
        source = records.get(('tiktok', review['product_id'], review['sku_id']))
        target = targets.get((review['review_id'], card['issue']))
        target_mismatch = bool(target and (target['source_product_id'] != review['product_id'] or
                                          target['source_sku_id'] != review['sku_id']))
        source_reviews.append({k: review.get(k) for k in (
            'evidence_id', 'review_id', 'product_id', 'sku_id', 'original_text', 'source_url',
            'product_main_image_as_reported', 'published_at', 'read_at_as_reported')})
        shared = {'review_id': review['review_id'], 'evidence_ids': [review['evidence_id']],
                  'source_product_id': review['product_id'], 'source_sku_id': review['sku_id'],
                  'candidate_product_id': result['product_id'], 'candidate_sku_id': result['sku_id'],
                  'source_specification': source, 'candidate_specification': offered, 'target': target,
                  'basis': '导入资料的身份和数值对照；引用内容与实物未自动验证'}
        checks.append(dict(shared, dimension='sku', condition='具体原商品与候选SKU资料绑定',
                           status='met' if source and offered else 'unknown',
                           reason='exact_platform_product_sku_binding' if source and offered else 'missing_exact_sku_specification'))
        for dimension, label, compare in (('size', '尺码与成衣尺寸符合已提供目标', measurement_checks),
                                           ('material', '面料成分符合已提供目标', material_checks)):
            if target_mismatch:
                status, reason, details = 'unknown', 'target_identity_mismatch', []
            elif not source or not offered:
                status, reason, details = 'unknown', 'missing_exact_sku_specification', []
            elif not target:
                status, reason, details = 'unknown', 'missing_review_specific_target', []
            else:
                status, reason, details = compare(source, offered, target)
            checks.append(dict(shared, dimension=dimension, condition=label, status=status, reason=reason, details=details))
    result.update(source_reviews=source_reviews, spec_checks=checks,
                  retrieval_relation='image_similarity_as_reported',
                  similarity_score_as_reported=product.get('similarity_score'),
                  specification_status=aggregate([c['status'] for c in checks]),
                  next_action='按spec_checks补原SKU/候选SKU资料及明确目标；尺码合身与面料性能另做实物复核，再核供货')
    result['conditions'] = [result['conditions'][0], result['conditions'][1], *checks, result['conditions'][-1]]
    if result['style_related'] == 'conflict' or result['specification_status'] == 'conflict':
        result['decision'] = '排除：品类/SKU或已提供目标规格冲突'
    return result
