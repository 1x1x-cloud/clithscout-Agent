"""ClothScout module; migrated without changing business thresholds."""
from collections import defaultdict
from copy import deepcopy
from runtime_support.text_identity.src.identity import digest
from demand_discovery.pain_classification.src.rules import ISSUES

def _group_candidates(evidence, config):
    groups = defaultdict(list)
    for e in evidence:
        if e["duplicate_of"] or e["flags"]:
            continue
        scope = "current" if e["in_window"] and e["market_as_reported"] == config["market"] else "historical_or_other_market"
        for hit in e["extractions"]:
            groups[(scope, e["product_id"], hit["issue"])].append(e)
    cards = []
    for (scope, pid, issue), support in groups.items():
        categories = {e["category"] for e in support}
        category = next(iter(categories)) if len(categories) == 1 else None
        counter = [e["evidence_id"] for e in evidence if e["product_id"] == pid
                   and e["kind"] == "positive_fit" and issue in ("too_long", "too_short", "too_big", "too_small", "fit_unspecified")
                   and e["in_window"] == support[0]["in_window"] and e["market_as_reported"] == config["market"]
                   and not e["flags"] and not e["duplicate_of"]]
        cards.append({"demand_id": "S1-" + digest([scope, pid, issue]), "method": "S1",
                      "status": "待补证据" if scope == "current" else "历史或其他市场线索",
                      "scope": scope, "product_id": pid, "issue": issue, "category": category,
                      "source_titles_as_reported": sorted({e["product_title_as_reported"] for e in support if e["product_title_as_reported"]}),
                      "statement": ISSUES[issue]["statement"], "population": None, "scenario": None,
                      "must_conditions": [{"condition": ISSUES[issue]["statement"] + "，需明确可检验目标",
                                           "evidence_ids": [e["evidence_id"] for e in support]}],
                      "preferences": [], "target_measurements": None,
                      "unknown": [ISSUES[issue]["unknown"], "采购数量、目标价格、交付要求", "其他独立使用者的证据"],
                      "hypotheses": [], "support_evidence_ids": [e["evidence_id"] for e in support],
                      "counter_evidence_ids": counter,
                      "counter_limit": "合身正面评价仅为同商品对照；买家和尺码可能不同",
                      "distinct_text_signals": len({e["text_signal_group"] for e in support}),
                      "window": config["window"], "market_basis": support[0]["market_basis"],
                      "manual_review": {"status": "pending", "version": 1},
                      "extraction_method": "finite_rules_v1"})
    return cards


def build_findings(evidence, config, review_evidence=None):
    from demand_discovery.demand_cards.src.prevalence import EMPTY, validate_review_evidence, assess_sample, evaluate_issue
    data = validate_review_evidence(review_evidence if review_evidence is not None else EMPTY)
    known = {(e['product_id'], e['review_id']) for e in evidence}
    if any((r['product_id'], r['review_id']) not in known for r in data['reviews']):
        raise ValueError('review_evidence_not_in_input')
    lookup = {e['evidence_id']: e for e in evidence}
    samples, signals, cards = {}, [], []
    for candidate in _group_candidates(evidence, config):
        pid = candidate['product_id']
        if pid not in samples:
            samples[pid] = assess_sample(evidence, config, data, pid)
        support = [lookup[ref] for ref in candidate['support_evidence_ids']]
        stats = evaluate_issue(samples[pid], support, candidate['scope'])
        signal = deepcopy(candidate)
        signal['signal_id'] = 'PS-' + signal.pop('demand_id')[3:]
        signal.update(status='已达到需求卡门槛' if stats['approved'] else '待补证据',
                      prevalence=stats, sourcing_eligible=stats['approved'])
        signals.append(signal)
        if stats['approved']:
            candidate.update(status='可进行商品匹配', prevalence=stats, sourcing_eligible=True,
                             signal_id=signal['signal_id'], support_evidence_ids=stats['effective_support_evidence_ids'])
            candidate['counter_evidence_ids'] = [r for r in candidate['counter_evidence_ids'] if r in stats['effective_evidence_ids']]
            candidate['must_conditions'][0]['evidence_ids'] = candidate['support_evidence_ids']
            candidate['distinct_text_signals'] = stats['distinct_support_text_count']
            candidate['unknown'].remove('其他独立使用者的证据')
            cards.append(candidate)
    return signals, cards


def build_cards(evidence, config, review_evidence=None):
    return build_findings(evidence, config, review_evidence)[1]
