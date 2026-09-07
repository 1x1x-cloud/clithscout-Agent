"""Synthetic, fully evidenced cohorts for testing downstream sourcing and SKU behavior.

Generated identities and annotations are test fixtures, never business evidence.
"""
import copy
import json
from collections import defaultdict


def qualified_sample(seeds, config):
    rows = copy.deepcopy(seeds)
    groups = defaultdict(list)
    for row in seeds:
        groups[row['productId']].append(row)
    for pid, original in groups.items():
        seen = set()
        for row in original:
            if row['content'] in seen:
                continue
            seen.add(row['content'])
            for i in (1, 2):
                rows.append(dict(row, reviewId=row['reviewId'] + '__independent_' + str(i),
                                 content=row['content'] + ' Synthetic wearer ' + str(i)))
        for i in range(2):
            rows.append(dict(original[0], reviewId=pid + '__positive_' + str(i), rating=5,
                             content='Fits perfectly' if i == 0 else 'True to size'))
    source = dict(source_ref='https://example.invalid/synthetic-review-audit', checked_at='2026-09-07T00:00:00Z')
    identities = {(r['productId'], r['reviewId']) for r in rows}
    info = {'schema_version': 1, 'samples': [dict(product_id=pid, market=config['market'],
        window=copy.deepcopy(config['window']), rating_scope='all', complete=True,
        review_ids=sorted({r['reviewId'] for r in rows if r['productId'] == pid}), **source) for pid in groups],
        'reviews': [dict(product_id=pid, review_id=rid, buyer_id='synthetic:' + pid + ':' + rid,
                         buyer_identity_verified=True, substantive=True, **source) for pid, rid in sorted(identities)]}
    return rows, info


def qualified_analysis(seeds, config):
    from demand_discovery.analysis_workflow.src.analyze import analyze
    rows, info = qualified_sample(seeds, config)
    result = analyze(rows, config, review_evidence=info)
    assert result['demand_cards'], 'Downstream fixture must pass the production demand gate'
    return result


def write_qualified(source, seeds, config):
    rows, info = qualified_sample(seeds, config)
    source.write_text(json.dumps(rows), encoding='utf-8')
    evidence = source.with_name('review_evidence.json')
    evidence.write_text(json.dumps(info), encoding='utf-8')
    return evidence


def expanded_targets(data):
    data = copy.deepcopy(data)
    for target in list(data['review_targets']):
        for i in (1, 2):
            data['review_targets'].append(dict(target, review_id=target['review_id'] + '__independent_' + str(i)))
    return data
