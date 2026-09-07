"""Read only the already used Actor's metadata; never starts a run."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import urllib.error
import urllib.request
import keyring

OUT = Path(__file__).resolve().parent
ACTOR_ID = "zk1NwTZ5eTPYhRcvF"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main():
    token = keyring.get_password("clothing-agent-apify", "APIFY_TOKEN")
    if not token or any(ord(c) < 33 or ord(c) > 126 for c in token):
        raise SystemExit("credential_unavailable_in_this_windows_identity")
    request = urllib.request.Request(
        "https://api.apify.com/v2/acts/" + ACTOR_ID,
        headers={"Authorization": "Bearer " + token, "Accept": "application/json"},
        method="GET",
    )
    opener = urllib.request.build_opener(NoRedirect())
    try:
        with opener.open(request, timeout=25) as response:
            raw = response.read(5 * 1024 * 1024 + 1)
            if len(raw) > 5 * 1024 * 1024:
                raise SystemExit("metadata_response_too_large")
            data = json.loads(raw)["data"]
            fields = ("id", "name", "username", "title", "description", "isPublic", "isDeprecated",
                      "defaultRunOptions", "taggedBuilds", "pricingInfos", "modifiedAt", "versions")
            selected = {k: data[k] for k in fields if k in data}
            result = {"read_at": datetime.now(timezone.utc).isoformat(), "http_status": response.status,
                      "new_runs_started": 0, "response_sha256": hashlib.sha256(raw).hexdigest(),
                      "actor_selected_fields": selected, "available_top_level_fields": sorted(data)}
            text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
            if token in text:
                raise SystemExit("credential_in_response_rejected")
            (OUT / "actor_metadata.json").write_text(text, encoding="utf-8")
            print(text)
    except urllib.error.HTTPError as exc:
        raise SystemExit("apify_http_" + str(exc.code)) from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise SystemExit("apify_network_failed_no_retry") from None
    finally:
        token = None


if __name__ == "__main__":
    main()
