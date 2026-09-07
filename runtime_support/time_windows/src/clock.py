"""ClothScout module; migrated without changing business thresholds."""
from datetime import datetime, timezone

def utc(value):
    if not isinstance(value, str):
        raise ValueError("Timestamp requires a timezone")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timestamp requires a timezone")
    return parsed.astimezone(timezone.utc)
