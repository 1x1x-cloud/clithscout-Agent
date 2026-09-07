"""ClothScout module; migrated without changing business thresholds."""
from collections import defaultdict
from runtime_support.text_identity.src.identity import digest

def review_signatures(rows):
    signatures = defaultdict(set)
    for row in rows:
        if row.get("reviewId"):
            signatures[str(row["reviewId"])].add(digest({k: row.get(k) for k in
                ("content", "productId", "skuId", "timestamp", "rating", "authorCountry", "productTitle", "productUrl", "status")}))
    return signatures
