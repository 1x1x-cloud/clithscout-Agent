"""ClothScout module; migrated without changing business thresholds."""


def build_review_queue(analysis, matches, searches, plans=None):
    searched_ids = {did for s in searches if not s.get("error") for did in s["plan"]["demand_ids"]}
    queue = {"evidence": [{"evidence_id": e["evidence_id"], "flags": e["flags"], "text": e["original_text"]}
                          for e in analysis["evidence"] if e["flags"]],
             "demands": [{"demand_id": c["demand_id"], "scope": c["scope"], "unknown": c["unknown"],
                          "search_executed": c["demand_id"] in searched_ids,
                          "search_limit": "Historical, unknown category, query cap or unrequested search may defer retrieval"}
                         for c in analysis["demand_cards"]],
             "products": [{"product_id": m["product_id"], "sku_id": m["sku_id"], "demand_id": m["demand_id"],
                          "decision": m["decision"], "action": m["next_action"]} for m in matches]}
    queue['image_searches'] = [dict(p, search_executed=any(s['plan']['query_id'] == p['query_id'] for s in searches))
                               for p in (plans or []) if p.get('search_type') == 'image']
    queue['sku_specifications'] = [dict(c, demand_id=m['demand_id']) for m in matches
                                    for c in m.get('spec_checks', []) if c['status'] != 'met']
    queue['problem_signals'] = [{'signal_id': s['signal_id'], 'product_id': s['product_id'],
        'issue': s['issue'], 'scope': s['scope'], 'status': s['status'],
        'prevalence': s['prevalence'], 'sourcing_eligible': s['sourcing_eligible']}
        for s in analysis.get('problem_signals', [])]
    return queue
