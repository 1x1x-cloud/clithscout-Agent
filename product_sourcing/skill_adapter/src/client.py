"""ClothScout module; migrated without changing business thresholds."""
import json, os, subprocess, sys
from pathlib import Path
from runtime_support.provider_errors.src.errors import ProviderError

def search_1688(plan, cli_path):
    path = Path(cli_path).resolve()
    if not path.is_file() or path.name != "cli.py":
        raise ProviderError("1688_cli_path_missing")
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    if plan.get("status", "ready") != "ready":
        raise ProviderError("1688_search_plan_not_ready")
    search_type = plan.get("search_type", "text")
    if search_type == "image":
        from product_sourcing.query_planning.src.image_planner import valid_image_url
        if not valid_image_url(plan.get("image")):
            raise ProviderError("1688_invalid_source_image")
        from product_sourcing.skill_adapter.src.image_input import verified_jpeg
        image_path = verified_jpeg(plan.get("image_input"), plan["image"])
        query_args = ["image_search", "--image", image_path]
    elif search_type == "text":
        query_args = ["text_search", "--query", plan["query"]]
    else:
        raise ProviderError("1688_unknown_search_type")
    command = [sys.executable, "-B", str(path), *query_args,
               "--limit", str(plan["limit"]), "--score-level", "high",
               "--purchase-amount", "1", "--tags", "4306497"]
    try:
        result = subprocess.run(command, shell=False, capture_output=True, text=True, encoding="utf-8",
                                env=env, timeout=90, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired:
        raise ProviderError("1688_cli_timeout_no_retry") from None
    except OSError:
        raise ProviderError("1688_cli_unavailable") from None
    # stderr may include upstream diagnostic material; do not persist it or echo it.
    try:
        payload = json.loads(result.stdout)
    except (json.JSONDecodeError, UnicodeError):
        raise ProviderError("1688_cli_non_json_output") from None
    if result.returncode != 0:
        raise ProviderError("1688_cli_nonzero_exit")
    return payload
