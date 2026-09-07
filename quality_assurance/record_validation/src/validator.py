"""ClothScout module; migrated without changing business thresholds."""
from runtime_support.json_storage.src.storage import now

def validate_run(rows, analysis, matches):
    errors = []
    if len(rows) != len(analysis["evidence"]):
        errors.append("evidence_row_count")
    evidence = {e["evidence_id"]: e for e in analysis["evidence"]}
    for e in evidence.values():
        if e["original_text"] != rows[e["raw_row"] - 1].get("content"):
            errors.append("original_text_changed")
        for extraction in e["extractions"]:
            if extraction["quote"] not in (e["original_text"] or ""):
                errors.append("unsupported_excerpt")
    cards = {c["demand_id"]: c for c in analysis["demand_cards"]}
    for card in cards.values():
        if 'problem_signals' in analysis and (not card.get('sourcing_eligible') or not card.get('prevalence', {}).get('approved')):
            errors.append('unqualified_demand_card')
        refs = card["support_evidence_ids"] + card["counter_evidence_ids"]
        if not refs or any(ref not in evidence for ref in refs):
            errors.append("invalid_evidence_reference")
        if card["scope"] == "current" and any(evidence[ref]["in_window"] is not True for ref in refs):
            errors.append("historical_evidence_in_current_card")
    for signal in analysis.get('problem_signals', []):
        if any(ref not in evidence for ref in signal['support_evidence_ids']):
            errors.append('invalid_signal_evidence_reference')
    for match in matches:
        if match["demand_id"] not in cards:
            errors.append("invalid_demand_reference")
        if match["eligible_for_test"] or match["supply_verified"] or match["verified_stock"] is not None:
            errors.append("unsupported_procurement_approval")
    return {"checked_at": now(), "passed": not errors, "errors": errors,
            "scope": "Record integrity, excerpts, references, time separation and conservative candidate gate; not source truth or extraction accuracy."}
