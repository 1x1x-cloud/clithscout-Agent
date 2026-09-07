"""ClothScout module; migrated without changing business thresholds."""
from workflow_execution.run_configuration.src.validation import validate_config
from runtime_support.time_windows.src.clock import utc
from runtime_support.text_identity.src.identity import digest, normalized
from evidence_processing.review_deduplication.src.grouping import review_signatures
from evidence_processing.garment_context.src.classifier import garment
from demand_discovery.pain_classification.src.classifier import classify

def normalize_reviews(rows, config):
    start, end = validate_config(config)
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("Review export must be a JSON array of objects")
    if len(rows) > config["limits"]["max_reviews"]:
        raise ValueError("Review file exceeds configured limit")
    signatures = review_signatures(rows)
    evidence, seen_ids = [], {}
    for index, row in enumerate(rows):
        raw_text = row.get("content")
        text = raw_text if isinstance(raw_text, str) else ""
        hits, kind, flags = classify(text)
        eid = "EV-" + digest([row.get("reviewId"), index, row.get("productId"), text])
        try:
            in_window = start <= utc(row.get("timestamp")) < end
        except (ValueError, TypeError):
            in_window = None
            flags.append("missing_or_invalid_timestamp")
        rid = str(row["reviewId"]) if row.get("reviewId") else None
        conflict = bool(rid and len(signatures[rid]) > 1)
        if conflict:
            flags.append("conflicting_review_id")
        if not rid:
            flags.append("missing_review_id")
        if not row.get("productId") or not row.get("productUrl"):
            flags.append("missing_product_context")
        if row.get("status") != "Success":
            flags.append("source_status_not_success")
        if raw_text is not None and not isinstance(raw_text, str):
            flags.append("invalid_content_type")
        duplicate = seen_ids.get(rid) if rid else None
        if rid:
            seen_ids.setdefault(rid, eid)
        evidence.append({"evidence_id": eid, "raw_row": index + 1, "review_id": rid,
                         "product_id": str(row["productId"]) if row.get("productId") else None,
                         "sku_id": str(row["skuId"]) if row.get("skuId") else None,
                         "original_text": raw_text, "source_url": row.get("productUrl"),
                         "product_title_as_reported": row.get("productTitle"),
                         "product_main_image_as_reported": row.get("productMainImage"),
                         "source_shop_id_as_reported": row.get("sourceShopId"),
                         "published_at": row.get("timestamp"), "read_at_as_reported": row.get("scrapedAt"),
                         "market_as_reported": row.get("authorCountry"),
                         "market_basis": "Actor country field; buyer residence not independently verified",
                         "verified_purchase_as_reported": row.get("authorVerified"), "rating": row.get("rating"),
                         "in_window": in_window, "category": garment(row.get("productTitle")),
                         "kind": kind, "extractions": hits, "flags": flags,
                         "duplicate_of": duplicate, "id_conflict": conflict,
                         "text_signal_group": digest([row.get("productId"), normalized(text)]),
                         "independent_buyer_verified": False})
    return evidence
