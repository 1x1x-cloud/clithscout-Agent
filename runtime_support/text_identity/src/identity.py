"""ClothScout module; migrated without changing business thresholds."""
import hashlib, json, re

def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]


def normalized(text):
    return re.sub(r"\s+", " ", text.casefold()).strip()
