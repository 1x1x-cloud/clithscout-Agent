"""Check existing credentials in the same Windows identity; never print values."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

root = Path('D:/clothscout').resolve()
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / 'product_sourcing/1688_skill/vendor/1688-product-find/scripts'))
from data_acquisition.apify_reviews.src.client import ApifyReader
from _auth import get_ak_from_env

result = {'checked_at': datetime.now(timezone.utc).isoformat(), 'network_requests': 0,
          'scope': 'Local credential availability only; no provider authentication request or new search.'}
try:
    reader = ApifyReader()
    result['apify_local_credential_available'] = True
    reader.close()
except Exception as exc:
    result['apify_local_credential_available'] = False
    result['apify_error_type'] = type(exc).__name__
try:
    ak_id, ak_secret = get_ak_from_env()
    result['1688_local_credential_available'] = bool(ak_id and ak_secret)
    ak_id = ak_secret = None
except Exception as exc:
    result['1688_local_credential_available'] = False
    result['1688_error_type'] = type(exc).__name__
target = root / 'quality_assurance/migration_validation/records/credential_availability.json'
target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
