"""One bounded Apify run for the three confirmed keyword products.

Default is offline validation. 'start' sends one POST, 'collect' resumes GETs.
An attempt marker prevents duplicate paid starts, including ambiguous timeouts.
"""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from data_acquisition.apify_reviews.src.client import fetch_reviews, NoRedirect

ACTOR_ID = "zk1NwTZ5eTPYhRcvF"
PRODUCTS = ["1732357239054307594", "1732510609891758832", "1731650530027868452"]
OPTIONS = {"build": "0.0.8", "timeout": 600, "memory": 512,
           "maxTotalChargeUsd": 2, "restartOnError": "false", "waitForFinish": 0}
TERMINAL = {"SUCCEEDED", "FAILED", "TIMED-OUT", "ABORTED"}


def now():
    return datetime.now(timezone.utc).isoformat()


def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_input():
    value = json.loads((OUT / "actor_input.json").read_text(encoding="utf-8"))
    observed = json.loads((ROOT / "data_acquisition/fastmoss_catalog/records/keyword_product_review_pilot_20260907/products.json").read_text(encoding="utf-8"))
    expected = {"urls": [], "productIds": PRODUCTS, "country": "US", "maxReviewsPerTarget": 300,
                "sortBy": "newest", "starRating": 0, "withPhotosOnly": False}
    outputs = ["Rating", "Content", "Timestamp", "AuthorHandle", "AuthorName", "AuthorAvatar", "AuthorVerified",
               "AuthorCountry", "Images", "SkuId", "ProductTitle", "ProductMainImage", "ProductUrl", "SourceShopId", "InputUrl"]
    expected.update({"output" + name: True for name in outputs})
    if value != expected or [p["product_id"] for p in observed] != PRODUCTS:
        raise ValueError("input_or_product_scope_changed")
    if any(type(value[k]) is not int for k in ["maxReviewsPerTarget", "starRating"]):
        raise ValueError("invalid_integer_fields")
    config = json.loads((ROOT / "workflow_execution/run_configuration/config/current_round.json").read_text(encoding="utf-8"))
    if 3 * value["maxReviewsPerTarget"] > config["limits"]["max_reviews"]:
        raise ValueError("over_existing_technical_review_limit")
    return value


class Api:
    def __init__(self):
        import keyring
        self.token = keyring.get_password("clothing-agent-apify", "APIFY_TOKEN")
        if not self.token or any(ord(c) < 33 or ord(c) > 126 for c in self.token):
            raise ValueError("credential_unavailable_in_this_windows_identity")
        self.opener = urllib.request.build_opener(NoRedirect())
        self.requests = []

    def request(self, path, value=None, plain=False):
        method = "GET" if value is None else "POST"
        start_path = "actors/" + ACTOR_ID + "/runs?" + urllib.parse.urlencode(OPTIONS)
        get_ok = re.fullmatch(r"(?:actor-runs/[A-Za-z0-9]+(?:/log)?|datasets/[A-Za-z0-9]+(?:/items\?format=json&offset=\d+&limit=\d+)?|key-value-stores/[A-Za-z0-9]+/records/INPUT)", path)
        if (method == "POST" and path != start_path) or (method == "GET" and not get_ok):
            raise ValueError("request_scope_rejected")
        headers = {"Authorization": "Bearer " + self.token, "Accept": "application/json"}
        body = None
        if value is not None:
            body = json.dumps(value, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request("https://api.apify.com/v2/" + path, data=body, headers=headers, method=method)
        record = {"at": now(), "method": method, "path": path}
        self.requests.append(record)
        try:
            with self.opener.open(req, timeout=30) as response:
                raw = response.read(20 * 1024 * 1024 + 1)
                record["status"] = response.status
                if len(raw) > 20 * 1024 * 1024:
                    raise ValueError("response_size_limit")
                text = raw.decode("utf-8")
                if self.token in text:
                    raise ValueError("credential_in_response_rejected")
                record["sha256"] = hashlib.sha256(raw).hexdigest()
                if plain:
                    text = re.sub(r"apify_api_[A-Za-z0-9_-]+", "[REDACTED]", text)
                    text = re.sub(r"(?i)(token|password|secret|api_key)=([^&\s]+)", r"\1=[REDACTED]", text)
                    text = re.sub(r"https?://[^\s/@]+:[^\s/@]+@", "https://[REDACTED]@", text)
                    return text
                return json.loads(text)
        except urllib.error.HTTPError as exc:
            record["status"] = exc.code
            raise ValueError("apify_http_" + str(exc.code)) from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise ValueError("network_failed_no_retry") from None
        finally:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            write("http_" + stamp + ".json", self.requests)

    def __call__(self, path):
        return self.request(path)


def safe_run(run):
    keys = ["id", "actId", "status", "statusMessage", "startedAt", "finishedAt", "defaultDatasetId",
            "defaultKeyValueStoreId", "buildId", "buildNumber", "options", "usageTotalUsd", "chargedEventCounts",
            "pricingInfo", "exitCode", "isStatusMessageTerminal"]
    return {k: run[k] for k in keys if k in run}


def input_matches(submitted, requested):
    # Apify injects the documented default; shop caps do not affect product IDs.
    # Do not accept changes to requested filters, limits, IDs or output fields.
    return submitted == requested or submitted == dict(requested, maxProductsPerShop=5)


def start(api, value):
    marker = OUT / "start_attempt.json"
    with marker.open("x", encoding="utf-8") as file:
        json.dump({"at": now(), "actor_id": ACTOR_ID, "input_sha256": hashlib.sha256((OUT / "actor_input.json").read_bytes()).hexdigest(),
                   "options": OPTIONS, "automatic_retry": False}, file, ensure_ascii=False, indent=2)
    run = api.request("actors/" + ACTOR_ID + "/runs?" + urllib.parse.urlencode(OPTIONS), value)["data"]
    write("run_start.json", safe_run(run))
    if run.get("actId") != ACTOR_ID or not re.fullmatch(r"[A-Za-z0-9]+", str(run.get("id", ""))):
        raise ValueError("unexpected_run_identity")
    if run.get("options", {}).get("maxTotalChargeUsd") != 2:
        raise ValueError("run_cost_cap_not_confirmed_inspect_before_continuing")
    return {"run_id": run["id"], "status": run["status"], "max_total_charge_usd": 2, "new_runs_started": 1}


def collect(api, value):
    receipt = json.loads((OUT / "run_start.json").read_text(encoding="utf-8"))
    run_id = receipt["id"]
    run = api("actor-runs/" + run_id)["data"]
    if run.get("actId") != ACTOR_ID or run.get("id") != run_id:
        raise ValueError("unexpected_run_identity")
    write("run_latest.json", safe_run(run))
    if run["status"] not in TERMINAL:
        return {"run_id": run_id, "status": run["status"], "new_runs_started": 0}
    log = api.request("actor-runs/" + run_id + "/log", plain=True)
    (OUT / "run_log.redacted.txt").write_text(log, encoding="utf-8")
    submitted = api("key-value-stores/" + run["defaultKeyValueStoreId"] + "/records/INPUT")
    write("submitted_input.json", submitted)
    if not input_matches(submitted, value):
        raise ValueError("submitted_input_differs")
    if run["status"] != "SUCCEEDED":
        return {"run_id": run_id, "status": run["status"], "new_runs_started": 0, "log_saved": True}
    rows, source = fetch_reviews(run_id, 1000, get=api)
    write("api_reviews.json", rows)
    write("dataset_read_provenance.json", source)
    return {"run_id": run_id, "status": run["status"], "reviews": len(rows),
            "usage_total_usd": run.get("usageTotalUsd"), "new_runs_started": 0, "dataset_id": run["defaultDatasetId"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["dry-run", "start", "collect"], nargs="?", default="dry-run")
    args = parser.parse_args()
    value = validate_input()
    if args.mode == "dry-run":
        print(json.dumps({"offline_validation": "passed", "input": value, "options": OPTIONS, "network_requests": 0}, ensure_ascii=False))
        return
    api = Api()
    try:
        result = start(api, value) if args.mode == "start" else collect(api, value)
        write("command_" + args.mode + "_result.json", result)
        print(json.dumps(result, ensure_ascii=False))
    finally:
        api.token = None


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc) if isinstance(exc, ValueError) else type(exc).__name__, "automatic_retry": False}))
        raise SystemExit(1)
