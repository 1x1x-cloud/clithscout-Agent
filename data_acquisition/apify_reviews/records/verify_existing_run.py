"""Read only the previously authorized Apify run and compare its existing dataset."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib, json, re, urllib.error, urllib.parse, urllib.request
import keyring

BASE = Path(__file__).resolve().parent
RUN_ID = "BxW4clbdEnaMPvPbW"
REFERENCE = BASE.parent / "shop_negative_reviews_2026-09-06/user_run_20260906_144758/raw_reviews.json"
OUT = BASE / ("authenticated_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"))
OUT.mkdir(exist_ok=False)
token = keyring.get_password("clothing-agent-apify", "APIFY_TOKEN")
report = {"checked_at_utc": datetime.now(timezone.utc).isoformat(), "run_id": RUN_ID,
          "credential_present": bool(token), "credential_exposed": False, "http_requests": [],
          "new_actor_runs_started": 0, "request_methods": ["GET"], "errors": []}
report["credential_shape"] = {
    "leading_or_trailing_whitespace": bool(token and token != token.strip()),
    "contains_line_break": bool(token and ("\n" in token or "\r" in token)),
    "contains_non_ascii": bool(token and not token.isascii()),
    "has_apify_api_prefix": bool(token and token.startswith("apify_api_")),
    "has_bearer_prefix": bool(token and token.lower().startswith("bearer ")),
}

class ProbeFailure(Exception):
    pass

def store_json(name, value):
    text = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if token and token in text:
        raise ProbeFailure("Refused to write response containing the credential.")
    (OUT / name).write_text(text, encoding="utf-8")

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(NoRedirect())
def read(path):
    url = "https://api.apify.com/v2/" + path
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token, "Accept": "application/json"}, method="GET")
    record = {"path": path, "method": "GET"}
    report["http_requests"].append(record)
    try:
        with opener.open(req, timeout=25) as res:
            payload = res.read()
            record["status"] = res.status
            record["response_sha256"] = hashlib.sha256(payload).hexdigest()
            return json.loads(payload)
    except urllib.error.HTTPError as exc:
        record["status"] = exc.code
        raw_error = exc.read(4000).decode("utf-8", "replace")
        safe_error = raw_error.replace(token, "[REDACTED]") if token else raw_error
        safe_error = re.sub(r"apify_api_[A-Za-z0-9_-]+", "[REDACTED]", safe_error)
        record["error_content_type"] = exc.headers.get("Content-Type")
        record["safe_error_excerpt"] = safe_error[:1000]
        try:
            error = json.loads(raw_error).get("error", {})
            kind = str(error.get("type", "http-error"))
            record["error_type"] = kind if re.fullmatch(r"[a-zA-Z0-9_-]+", kind) else "http-error"
        except Exception:
            record["error_type"] = "http-error"
        raise ProbeFailure("Apify GET failed with HTTP " + str(exc.code))
    except urllib.error.URLError:
        raise ProbeFailure("Network connection failed; no automatic retry.")

try:
    if not token:
        raise ProbeFailure("Project Apify credential is still absent from Windows Credential Manager.")
    if any(ord(c) < 33 or ord(c) > 126 for c in token):
        raise ProbeFailure("Stored credential contains invalid characters; stopped before making an HTTP request.")
    run = read("actor-runs/" + RUN_ID)["data"]
    selected = {k: run.get(k) for k in ("id","actId","status","startedAt","finishedAt","defaultDatasetId",
                 "defaultKeyValueStoreId","buildId","buildNumber","generalAccess","usageTotalUsd")}
    store_json("run_selected_fields.json", selected)
    if run.get("id") != RUN_ID or run.get("status") != "SUCCEEDED":
        raise ProbeFailure("Run ID/status does not match the completed run expected for this check.")
    dataset_id = run.get("defaultDatasetId")
    if not isinstance(dataset_id, str) or not re.fullmatch(r"[A-Za-z0-9]+", dataset_id):
        raise ProbeFailure("Run returned no valid default dataset ID.")
    dataset = read("datasets/" + dataset_id)["data"]
    selected_dataset = {k: dataset.get(k) for k in ("id","itemCount","createdAt","modifiedAt")}
    store_json("dataset_selected_fields.json", selected_dataset)
    total = dataset.get("itemCount")
    if not isinstance(total, int) or total < 0 or total > 1000:
        raise ProbeFailure("Dataset count is unexpected for a 16-row verification; stopped before bulk read.")
    items = []
    offset = 0
    pages = 0
    while offset < total and pages < 10:
        query = urllib.parse.urlencode({"format":"json", "offset":offset, "limit":min(100, total-offset)})
        page = read("datasets/" + dataset_id + "/items?" + query)
        if not isinstance(page, list) or not page:
            raise ProbeFailure("Dataset pagination ended unexpectedly.")
        items.extend(page)
        offset += len(page)
        pages += 1
    if len(items) != total:
        raise ProbeFailure("Downloaded row count does not match dataset metadata.")
    store_json("api_reviews.json", items)
    original = json.loads(REFERENCE.read_text(encoding="utf-8-sig"))
    original_by_id = {r["reviewId"]: r for r in original}
    api_by_id = {r.get("reviewId"): r for r in items}
    identity_match = set(original_by_id) == set(api_by_id) and len(api_by_id) == len(items)
    differences = []
    if identity_match:
        for rid, prior in original_by_id.items():
            now = api_by_id[rid]
            for field in set(prior) | set(now):
                if field not in prior or field not in now or prior.get(field) != now.get(field):
                    differences.append({"review_id":rid,"field":field})
    else:
        report["errors"].append("Review ID set differs from the attachment.")
    report.update({"run_status":run["status"],"dataset_id":dataset_id,"api_rows":len(items),
                   "reference_rows":len(original), "review_id_set_matches":identity_match,
                   "all_fields_match_by_review_id":identity_match and not differences,
                   "field_differences":differences, "file_order_matches":items == original,
                   "reference_sha256":hashlib.sha256(REFERENCE.read_bytes()).hexdigest(),
                   "api_reviews_file_sha256":hashlib.sha256((OUT/"api_reviews.json").read_bytes()).hexdigest(),
                   "comparison_scope":"Every returned field by reviewId; formatting/order reported separately.",
                   "limits":"Read access verified for this existing run/dataset; new-run permission, recurring execution and billing not tested."})
except ProbeFailure as exc:
    report["errors"].append(str(exc))
except Exception as exc:
    report["errors"].append("Unexpected check failure: " + type(exc).__name__)
finally:
    report["authenticated_read_passed"] = not report["errors"] and report.get("all_fields_match_by_review_id",False)
    store_json("verification.json", report)
    print(json.dumps({"output_directory":str(OUT), **report},ensure_ascii=False,indent=2))
    token = None
if not report["authenticated_read_passed"]:
    raise SystemExit(1)
