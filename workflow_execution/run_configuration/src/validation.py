"""ClothScout module; migrated without changing business thresholds."""
from runtime_support.time_windows.src.clock import utc

def validate_config(config):
    try:
        start, end = utc(config["window"]["start"]), utc(config["window"]["end"])
        if start >= end or config["market"] != "US" or config["scope"] != "clothing":
            raise ValueError("Invalid window or unsupported market/scope")
        if config.get("search_strategy", "text") not in ("text", "image"):
            raise ValueError("Unsupported search strategy")
        for name, maximum in [("max_reviews", 10000), ("max_queries", 20), ("products_per_query", 3)]:
            value = config["limits"][name]
            if type(value) is not int or not 1 <= value <= maximum:
                raise ValueError("Invalid technical limit: " + name)
    except (KeyError, TypeError) as exc:
        raise ValueError("Explicit market, scope, window and limits are required") from exc
    return start, end
