"""ClothScout module; migrated without changing business thresholds."""
from runtime_support.provider_errors.src.errors import ProviderError

def parse_search(payload, expected_image=None):
    if not isinstance(payload, dict) or payload.get("success") is not True:
        raise ProviderError("1688_search_failed")
    inner = payload.get("data", {})
    if isinstance(inner, dict) and "data" in inner:
        inner = inner["data"]
    if not isinstance(inner, dict) or inner.get("success") is not True or not isinstance(inner.get("similar_products"), list):
        raise ProviderError("1688_response_schema_changed")
    if expected_image is not None and (inner.get("search_type") != "image_similarity" or inner.get("source_image") != expected_image):
        raise ProviderError("1688_image_response_source_mismatch")
    if any(not isinstance(p, dict) or not p.get("product_id") for p in inner["similar_products"]):
        raise ProviderError("1688_product_identity_missing")
    return inner["similar_products"]
