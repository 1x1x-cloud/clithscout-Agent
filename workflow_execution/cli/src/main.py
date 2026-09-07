import argparse
import hashlib
import json
from pathlib import Path
import sys

from runtime_support.json_storage.src.storage import load_json
from workflow_execution.pipeline.src.orchestrator import run_pipeline
from runtime_support.project_paths.src.paths import PROJECT_ROOT, CONFIG_FILE, RUNS, project_path
from runtime_support.provider_errors.src.errors import ProviderError
from product_sourcing.skill_adapter.src.client import search_1688


def main():
    parser = argparse.ArgumentParser(description="服装差评需求与1688找货对照；只读取已有Apify运行")
    parser.add_argument("--config", default=str(CONFIG_FILE))
    sources = parser.add_mutually_exclusive_group()
    sources.add_argument("--reviews", type=Path)
    sources.add_argument("--live-read", action="store_true")
    sources.add_argument("--replay-run", type=Path)
    sources.add_argument("--recheck-run", type=Path, help="复用图片查询快照，用新SKU资料离线复核")
    parser.add_argument("--existing-run-id")
    parser.add_argument("--live-search", action="store_true")
    parser.add_argument("--image-search", action="store_true", help="用原商品主图召回相似款；联网仍需 --live-search")
    parser.add_argument("--sku-evidence", type=Path, help="原SKU、候选SKU与差评目标资料JSON")
    parser.add_argument("--review-evidence", type=Path, help="全星级样本覆盖、有效评价及买家去重依据JSON")
    parser.add_argument("--output-root", type=Path, default=RUNS)
    args = parser.parse_args()
    config = load_json(Path(args.config))
    if args.image_search:
        config = dict(config, search_strategy="image")
    sku_evidence = args.sku_evidence
    root = PROJECT_ROOT
    reviews = args.reviews or root / config["local_review_file"]
    run_id, search_fn, mode, provenance = None, None, "none", None
    if args.existing_run_id and not args.live_read:
        parser.error("--existing-run-id requires --live-read")
    if args.recheck_run and not args.sku_evidence:
        parser.error("--recheck-run requires --sku-evidence")
    if args.live_read:
        reviews, run_id = None, args.existing_run_id or config["apify_existing_run_id"]
    if args.replay_run or args.recheck_run:
        if args.live_search or args.image_search or args.review_evidence or (args.replay_run and args.sku_evidence):
            parser.error("Replay uses its saved search strategy and SKU evidence; overrides are not allowed")
        previous = (args.replay_run or args.recheck_run).resolve()
        manifest = load_json(previous / "manifest.json")
        for name, expected in manifest["artifact_sha256"].items():
            file = (previous / name).resolve()
            if previous not in file.parents or hashlib.sha256(file.read_bytes()).hexdigest() != expected:
                raise ProviderError("replay_artifact_integrity_failed")
        config = manifest["config"]
        if args.recheck_run:
            if config.get("search_strategy") != "image":
                parser.error("Recheck requires an image-search run")
        else:
            sku_evidence = previous / "sku_evidence.json" if (previous / "sku_evidence.json").is_file() else None
        reviews = previous / "raw_reviews.json"
        mode = "recheck" if args.recheck_run else "replay"
        provenance = str(previous)
        def search_fn(plan):
            record_path = previous / "searches" / (plan["query_id"] + ".json")
            if not record_path.exists():
                raise ProviderError("replay_query_not_available")
            record = load_json(record_path)
            if record["plan"] != plan or record.get("error"):
                raise ProviderError("replay_query_mismatch_or_previous_failure")
            return record
        if manifest.get("steps", {}).get("search") == "not_requested":
            search_fn = None
    elif args.live_search:
        mode = "live"
        search_fn = lambda plan: search_1688(plan, project_path(config["1688_cli"]))
    out = run_pipeline(config, args.output_root, reviews_path=reviews, run_id=run_id,
                       search_fn=search_fn, search_mode=mode, replay_provenance=provenance,
                       sku_evidence_path=sku_evidence, review_evidence_path=args.review_evidence)
    manifest = load_json(out / "manifest.json")
    print(json.dumps({"output_directory": str(out.resolve()), "status": manifest["status"],
                      "counts": manifest.get("counts"), "errors": manifest["errors"]}, ensure_ascii=False, indent=2))
    return 0 if manifest["status"] == "completed" else 1


def entrypoint():
    """Keep the same redacted failure contract for every command-line launcher."""
    try:
        return main()
    except (ProviderError, ValueError, OSError, KeyError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc) if isinstance(exc, ProviderError) else type(exc).__name__}))
        return 1


if __name__ == "__main__":
    sys.exit(entrypoint())
