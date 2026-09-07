"""ClothScout module; migrated without changing business thresholds."""
import hashlib, json, re
import urllib.error, urllib.parse, urllib.request
from runtime_support.provider_errors.src.errors import ProviderError

def valid_id(value):
    return isinstance(value, str) and bool(re.fullmatch(r"[A-Za-z0-9]+", value))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class ApifyReader:
    def __init__(self):
        import keyring
        token = keyring.get_password("clothing-agent-apify", "APIFY_TOKEN")
        if not token or any(ord(c) < 33 or ord(c) > 126 for c in token):
            raise ProviderError("apify_credential_unavailable_in_this_windows_identity")
        self._token = token
        self.requests = []
        self._opener = urllib.request.build_opener(NoRedirect())

    def __call__(self, path):
        if not re.fullmatch(r"(?:actor-runs/[A-Za-z0-9]+|datasets/[A-Za-z0-9]+(?:/items\?format=json&offset=\d+&limit=\d+)?)", path):
            raise ProviderError("apify_path_rejected")
        request = urllib.request.Request("https://api.apify.com/v2/" + path, method="GET",
                    headers={"Authorization": "Bearer " + self._token, "Accept": "application/json"})
        record = {"path": path, "method": "GET"}
        self.requests.append(record)
        try:
            with self._opener.open(request, timeout=25) as response:
                body = response.read(20 * 1024 * 1024 + 1)
                record["status"] = response.status
                if len(body) > 20 * 1024 * 1024:
                    raise ProviderError("apify_response_size_limit")
                text = body.decode("utf-8")
                if self._token in text:
                    raise ProviderError("credential_in_response_rejected")
                record["sha256"] = hashlib.sha256(body).hexdigest()
                return json.loads(text)
        except urllib.error.HTTPError as exc:
            record["status"] = exc.code
            raise ProviderError("apify_http_" + str(exc.code)) from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise ProviderError("apify_network_failed_no_retry") from None
        except (UnicodeError, json.JSONDecodeError):
            raise ProviderError("apify_invalid_json") from None

    def close(self):
        self._token = None


def fetch_reviews(run_id, max_reviews, get=None, page_size=100):
    if not valid_id(run_id) or not 1 <= page_size <= 100 or not 1 <= max_reviews <= 10000:
        raise ProviderError("apify_invalid_run_or_limit")
    owned = get is None
    get = ApifyReader() if owned else get
    try:
        run = get("actor-runs/" + run_id).get("data", {})
        if run.get("id") != run_id or run.get("status") != "SUCCEEDED":
            raise ProviderError("apify_run_not_succeeded")
        dataset_id = run.get("defaultDatasetId")
        if not valid_id(dataset_id):
            raise ProviderError("apify_missing_dataset")
        dataset_path = "datasets/" + dataset_id
        metadata = get(dataset_path).get("data", {})
        total = metadata.get("itemCount")
        if metadata.get("id") != dataset_id or type(total) is not int or total < 0 or total > max_reviews:
            raise ProviderError("apify_dataset_count_invalid_or_over_limit")
        rows = []
        while len(rows) < total:
            limit = min(page_size, total - len(rows))
            query = urllib.parse.urlencode({"format": "json", "offset": len(rows), "limit": limit})
            page = get(dataset_path + "/items?" + query)
            if not isinstance(page, list) or not 1 <= len(page) <= limit:
                raise ProviderError("apify_incomplete_or_invalid_page")
            rows.extend(page)
        after = get(dataset_path).get("data", {})
        if any(metadata.get(key) != after.get(key) for key in ("id", "itemCount", "modifiedAt")):
            raise ProviderError("apify_dataset_changed_during_read")
        return rows, {"source": "apify_existing_run", "run_id": run_id, "dataset_id": dataset_id,
                      "run_status": run["status"], "item_count": total,
                      "dataset_modified_at": metadata.get("modifiedAt"),
                      "http_requests": getattr(get, "requests", []), "new_actor_runs_started": 0}
    finally:
        if owned:
            get.close()
