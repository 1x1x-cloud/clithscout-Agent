"""ClothScout module; migrated without changing business thresholds."""
import re

def garment(title):
    if not isinstance(title, str):
        return None
    choices = [("trousers", r"\b(?:pants|trousers|jeans)\b|长裤|牛仔裤|休闲裤"),
               ("top", r"\b(?:top|tops|shirt|blouse|sweater|hoodie)\b|上衣|衬衫|卫衣"),
               ("dress", r"\bdress(?:es)?\b|连衣裙"),
               ("skirt", r"\bskirt\b|半身裙"), ("shorts", r"\bshorts\b|短裤")]
    hits = [category for category, pattern in choices if re.search(pattern, title, re.IGNORECASE)]
    return hits[0] if len(hits) == 1 else None
