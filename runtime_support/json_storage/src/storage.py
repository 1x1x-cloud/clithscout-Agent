"""ClothScout module; migrated without changing business thresholds."""
import json
from datetime import datetime, timezone

def now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path):
    if path.stat().st_size > 20 * 1024 * 1024:
        raise ValueError("JSON file exceeds 20 MiB technical limit")
    return json.loads(path.read_text(encoding="utf-8-sig"))
