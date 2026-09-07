"""ClothScout module; migrated without changing business thresholds."""
from collections import Counter
from evidence_processing.review_normalization.src.normalizer import normalize_reviews
from demand_discovery.demand_cards.src.builder import build_findings

def analyze(rows, config, review_evidence=None):
    evidence = normalize_reviews(rows, config)
    signals, cards = build_findings(evidence, config, review_evidence)
    return {"evidence": evidence, "demand_cards": cards, "problem_signals": signals,
            "summary": {"raw_rows": len(rows), "in_window_rows": sum(e["in_window"] is True for e in evidence),
                        "outside_window_rows": sum(e["in_window"] is False for e in evidence),
                        "unknown_time_rows": sum(e["in_window"] is None for e in evidence),
                        "duplicate_rows": sum(bool(e["duplicate_of"]) for e in evidence),
                        "id_conflict_rows": sum(e["id_conflict"] for e in evidence),
                        "kinds": dict(Counter(e["kind"] for e in evidence)),
                        "independent_buyers": None, "negative_review_rate": None,
                        "current_cards": sum(c["scope"] == "current" for c in cards),
                        "current_problem_signals": sum(c["scope"] == "current" for c in signals),
                        "unhandled_rows": sum(bool(e["flags"]) for e in evidence)}}
