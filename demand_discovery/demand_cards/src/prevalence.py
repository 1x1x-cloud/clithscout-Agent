"""Evaluate the user-approved AND gate using auditable review-sample evidence."""
from datetime import datetime
from decimal import Decimal
import re

from runtime_support.text_identity.src.identity import normalized

POLICY = {'version': 's1-prevalence-v1', 'min_effective_reviews': 5,
          'recommended_effective_reviews': 10, 'min_independent_buyers': 3,
          'min_distinct_support_texts': 3, 'min_problem_ratio': 0.2}
EMPTY = {'schema_version': 1, 'samples': [], 'reviews': []}
PURE_PRAISE = re.compile(
    r'(?:(?:love|like)(?: (?:it|this|these|them))?(?: (?:pants|top|dress|shirt|product))?'
    r'|(?:beautiful|great|nice|good)(?: (?:pants|top|dress|shirt|product))?'
    r'|(?:很)?好看|很好|喜欢)[.!。！\s]*')


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def validate_review_evidence(data):
    if not isinstance(data, dict) or type(data.get('schema_version')) is not int or data['schema_version'] != 1:
        raise ValueError('review_evidence_schema_invalid')
    for collection in ('samples', 'reviews'):
        if not isinstance(data.get(collection), list):
            raise ValueError('review_evidence_collection_invalid')
        seen = set()
        for row in data[collection]:
            if not isinstance(row, dict) or not _text(row.get('product_id')) or not _text(row.get('source_ref')):
                raise ValueError('review_evidence_provenance_required')
            stamp = datetime.fromisoformat(str(row.get('checked_at', '')).replace('Z', '+00:00'))
            if stamp.utcoffset() is None:
                raise ValueError('review_evidence_timezone_required')
            key = row['product_id'] if collection == 'samples' else (row['product_id'], row.get('review_id'))
            if collection == 'reviews' and not _text(row.get('review_id')):
                raise ValueError('review_evidence_review_id_required')
            if key in seen:
                raise ValueError('duplicate_review_evidence_identity')
            seen.add(key)
            fields = ('complete',) if collection == 'samples' else ('substantive', 'buyer_identity_verified', 'suspected_reused_account', 'is_repost')
            if any(field in row and type(row[field]) is not bool for field in fields):
                raise ValueError('review_evidence_boolean_invalid')
            if collection == 'samples':
                ids = row.get('review_ids')
                if not isinstance(ids, list) or not all(_text(i) for i in ids) or len(ids) != len(set(ids)):
                    raise ValueError('review_evidence_sample_ids_invalid')
                if not _text(row.get('market')) or not _text(row.get('rating_scope')) or not isinstance(row.get('window'), dict):
                    raise ValueError('review_evidence_sample_scope_required')
            elif any(field in row and row[field] is not None and not _text(row[field]) for field in ('buyer_id', 'thread_id')):
                raise ValueError('review_evidence_identity_invalid')
    return data


def assess_sample(evidence, config, data, product_id):
    """A full all-star sample claim must match exactly the supplied review IDs."""
    annotations = {(r['product_id'], r['review_id']): r for r in data['reviews']}
    rows = [e for e in evidence if e['product_id'] == product_id and e['in_window'] is True
            and e['market_as_reported'] == config['market']]
    sample = next((r for r in data['samples'] if r['product_id'] == product_id), None)
    coverage = bool(sample and sample.get('complete') is True and sample.get('rating_scope') == 'all'
                    and sample['market'] == config['market'] and sample['window'] == config['window']
                    and set(sample['review_ids']) == {r['review_id'] for r in rows}
                    and all(r['review_id'] for r in rows))
    suspects = {r.get('buyer_id') for r in data['reviews'] if r.get('suspected_reused_account') and r.get('buyer_id')}
    seen_text, seen_threads = set(), set()
    valid, exclusions = [], []
    unresolved = [e['evidence_id'] for e in evidence if e['product_id'] == product_id
                  and e['in_window'] is not False and e['market_as_reported'] in (None, '', config['market'])
                  and (e['in_window'] is None or not e['market_as_reported'])]
    for e in rows:
        # Malformed or contradictory observations are unknown evidence, not known
        # exclusions. Dropping them could spuriously raise an issue's share.
        if e['id_conflict'] or set(e['flags']) & {
                'invalid_content_type', 'missing_review_id', 'missing_product_context', 'source_status_not_success'}:
            unresolved.append(e['evidence_id'])
            continue
        info = annotations.get((product_id, e['review_id']), {})
        text = normalized(e['original_text']) if isinstance(e['original_text'], str) else ''
        reason = None
        if e['duplicate_of']:
            reason = 'duplicate_review_id'
        elif not text or PURE_PRAISE.fullmatch(text):
            reason = 'empty_or_pure_praise'
        elif info.get('suspected_reused_account') or info.get('buyer_id') in suspects:
            reason = 'suspected_reused_account'
        elif info.get('is_repost'):
            reason = 'reposted_content'
        elif info.get('substantive') is False:
            reason = 'non_substantive_as_reviewed'
        elif e['flags'] and any(f != 'uncovered_expression' for f in e['flags']):
            # Unresolved identity/reading/semantic issues must not silently reduce a denominator.
            unresolved.append(e['evidence_id'])
            continue
        elif info.get('substantive') is not True and e['kind'] not in ('specific_complaint', 'positive_fit', 'delivery'):
            unresolved.append(e['evidence_id'])
            continue
        if not reason and text in seen_text:
            reason = 'duplicate_body'
        thread = info.get('thread_id')
        if not reason and thread and thread in seen_threads:
            reason = 'same_discussion_thread'
        if reason:
            exclusions.append({'evidence_id': e['evidence_id'], 'reason': reason})
            continue
        seen_text.add(text)
        if thread:
            seen_threads.add(thread)
        valid.append(e)
    return {'valid': valid, 'annotations': annotations, 'sample_source': sample,
            'coverage_confirmed': coverage and not unresolved, 'unresolved_evidence_ids': unresolved,
            'exclusions': exclusions}


def evaluate_issue(sample, support, scope):
    valid = sample['valid'] if scope == 'current' else []
    support_ids = {e['evidence_id'] for e in support}
    effective = [e for e in valid if e['evidence_id'] in support_ids]
    identities = [sample['annotations'].get((e['product_id'], e['review_id']), {}) for e in effective]
    identity_known = bool(identities) and all(r.get('buyer_identity_verified') is True and _text(r.get('buyer_id'))
                                            and '*' not in r['buyer_id'] for r in identities)
    buyers = len({r['buyer_id'] for r in identities}) if identity_known else None
    coverage = sample['coverage_confirmed'] and scope == 'current'
    numerator, denominator = len(effective), len(valid)
    ratio = float(Decimal(numerator) / Decimal(denominator)) if coverage and denominator else None
    minimum_sample = denominator >= POLICY['min_effective_reviews']
    minimum_people = buyers is not None and buyers >= POLICY['min_independent_buyers']
    # Avoid rounded percentages turning 19.99... into a pass.
    ratio_met = coverage and denominator > 0 and Decimal(numerator) >= Decimal(denominator) * Decimal(str(POLICY['min_problem_ratio']))
    distinct = len({e['text_signal_group'] for e in effective})
    approved = bool(coverage and minimum_sample and minimum_people and ratio_met
                    and distinct >= POLICY['min_distinct_support_texts'])
    return {'policy': dict(POLICY), 'coverage_confirmed': coverage,
            'sample_source': sample['sample_source'], 'support_record_count': len(support),
            'effective_support_count': numerator, 'effective_sample_count': denominator,
            'distinct_support_text_count': distinct, 'independent_buyer_count': buyers,
            'problem_ratio': ratio, 'gates': {'sample_size': minimum_sample, 'independent_buyers': minimum_people,
            'problem_ratio': bool(ratio_met)}, 'approved': approved,
            'effective_evidence_ids': [e['evidence_id'] for e in valid],
            'effective_support_evidence_ids': [e['evidence_id'] for e in effective],
            'unresolved_evidence_ids': sample['unresolved_evidence_ids'], 'exclusions': sample['exclusions'],
            'warnings': ['sample_below_recommended_10'] if denominator < POLICY['recommended_effective_reviews'] else [],
            'limitation': 'Imported provenance and identity assertions are not independently verified by the program.'}
