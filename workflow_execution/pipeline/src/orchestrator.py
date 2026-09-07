"""ClothScout module; migrated without changing business thresholds."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from uuid import uuid4
from runtime_support.project_paths.src.paths import PROJECT_ROOT, active_source_files
from runtime_support.json_storage.src.storage import now, write_json, load_json
from runtime_support.provider_errors.src.errors import ProviderError
from workflow_execution.run_configuration.src.validation import validate_config
from demand_discovery.analysis_workflow.src.analyze import analyze
from data_acquisition.apify_reviews.src.client import fetch_reviews
from product_sourcing.query_planning.src.planner import plan_searches
from product_sourcing.result_parsing.src.parser import parse_search
from product_sourcing.skill_adapter.src.image_input import prepare_image, copy_image_input
from product_matching.sku_comparison.src.comparison import compare_product
from product_matching.sku_comparison.src.inspection import inspect_product
from product_matching.sku_comparison.src.spec_evidence import EMPTY_EVIDENCE, validate_spec_evidence
from demand_discovery.demand_cards.src.prevalence import EMPTY as EMPTY_REVIEWS, POLICY, validate_review_evidence
from quality_assurance.record_validation.src.validator import validate_run
from human_review.review_queue.src.builder import build_review_queue
from report_delivery.markdown_report.src.render import render_report
__version__ = '0.3.0-demand-gate'


def run_pipeline(config, output_root, reviews_path=None, run_id=None, search_fn=None,
                 search_mode="none", replay_provenance=None, sku_evidence_path=None, review_evidence_path=None):
    validate_config(config)
    image_mode = config.get("search_strategy", "text") == "image"
    if sku_evidence_path is not None and not image_mode:
        raise ValueError("SKU evidence requires image search mode")
    if (reviews_path is None) == (run_id is None):
        raise ValueError("Provide exactly one local review file or existing run ID")
    out = Path(output_root) / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    (out / "searches").mkdir()
    manifest = {"version": __version__, "run_id": out.name, "started_at": now(), "status": "running",
                "config": config, "steps": {}, "errors": [], "new_actor_runs_started": 0,
                "supply_absent": False, "search_mode": search_mode,
                "replay_provenance": replay_provenance, "source_code_sha256": {
                    str(p.relative_to(PROJECT_ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in active_source_files()}}
    write_json(out / "manifest.json", manifest)
    rows, analysis, matches, searches, plans = [], None, [], [], []
    try:
        review_info = EMPTY_REVIEWS
        if search_mode in ('replay', 'recheck'):
            if not replay_provenance or review_evidence_path is not None:
                raise ValueError('Historical analysis requires its saved review evidence')
            prior = Path(replay_provenance)
            archived_reviews = prior / 'review_evidence.json'
            if archived_reviews.exists():
                review_info = validate_review_evidence(load_json(archived_reviews))
            manifest['analysis_rule_source'] = 'archived_analysis'
            manifest['analysis_source_version'] = load_json(prior / 'manifest.json')['version']
        else:
            if review_evidence_path is not None:
                review_info = validate_review_evidence(load_json(Path(review_evidence_path)))
            manifest['analysis_rule_source'] = POLICY['version']
        write_json(out / 'review_evidence.json', review_info)
        specs = EMPTY_EVIDENCE
        if image_mode:
            if sku_evidence_path is not None:
                spec_bytes = Path(sku_evidence_path).read_bytes()
                specs = validate_spec_evidence(json.loads(spec_bytes.decode("utf-8-sig")))
                (out / "sku_evidence.json").write_bytes(spec_bytes)
            else:
                write_json(out / "sku_evidence.json", specs)
        if reviews_path is not None:
            path = Path(reviews_path).resolve()
            rows = load_json(path)
            original_bytes = path.read_bytes()
            (out / "source_reviews.json").write_bytes(original_bytes)
            source = {"source": "local_export", "path": str(path),
                      "sha256": hashlib.sha256(original_bytes).hexdigest()}
        else:
            rows, source = fetch_reviews(run_id, config["limits"]["max_reviews"])
        write_json(out / "raw_reviews.json", rows)
        write_json(out / "source.json", source)
        manifest["steps"]["read"] = "completed"
        write_json(out / "manifest.json", manifest)
        analysis = (load_json(prior / 'analysis.json') if search_mode in ('replay', 'recheck')
                    else analyze(rows, config, review_evidence=review_info))
        write_json(out / "analysis.json", analysis)
        write_json(out / "evidence.json", analysis["evidence"])
        write_json(out / "demand_cards.json", analysis["demand_cards"])
        write_json(out / 'problem_signals.json', analysis.get('problem_signals', []))
        plans = (load_json(prior / 'search_plan.json') if search_mode in ('replay', 'recheck')
                 else plan_searches(analysis["demand_cards"], config, analysis["evidence"]))
        write_json(out / "search_plan.json", plans)
        manifest["steps"]["analyze"] = "completed"
        manifest["steps"]["search"] = "not_requested" if search_fn is None else "running"
        write_json(out / "manifest.json", manifest)
        for plan in plans if search_fn is not None else []:
            if plan.get("status", "ready") != "ready":
                continue
            record = {"plan": plan, "mode": search_mode, "checked_at": now(), "search_invoked": False}
            try:
                request_plan = plan
                if image_mode and search_mode == "live":
                    record["image_input"] = prepare_image(plan["image"], out, plan["query_id"])
                    request_plan = dict(plan, image_input=record["image_input"])
                record["search_invoked"] = True
                response = search_fn(request_plan)
                # Replay preserves the source time, not the time of the new analysis.
                if search_mode in ("replay", "recheck"):
                    record["checked_at"] = response["checked_at"]
                    record["replayed_at"] = now()
                    if response.get("image_input"):
                        if response["image_input"].get("source_url") != plan.get("image"):
                            raise ProviderError("replay_image_source_mismatch")
                        record["image_input"] = copy_image_input(response["image_input"], replay_provenance, out)
                    response = response["payload"]
                record["payload"] = response
                expected_image = record.get("image_input", {}).get("cli_image_path", plan.get("image"))
                products = parse_search(response, expected_image=expected_image if image_mode else None)
                for product in products:
                    for card in analysis["demand_cards"]:
                        if card["demand_id"] in plan["demand_ids"]:
                            match = (inspect_product(card, product, analysis["evidence"], specs) if image_mode
                                     else compare_product(card, product))
                            match.update(query_id=plan["query_id"], checked_at=record["checked_at"], source_mode=search_mode)
                            matches.append(match)
            except ProviderError as exc:
                record["error"] = str(exc)
                manifest["errors"].append(str(exc))
            finally:
                searches.append(record)
                write_json(out / "searches" / (plan["query_id"] + ".json"), record)
            if record.get("error"):
                break  # No outer retry; stop all further queries after a provider failure.
        manifest["steps"]["search"] = ("failed" if manifest["errors"] else "completed") if search_fn else "not_requested"
        write_json(out / "product_matches.json", matches)
        queue = build_review_queue(analysis, matches, searches, plans)
        write_json(out / "manual_review.json", queue)
        validation = validate_run(rows, analysis, matches)
        write_json(out / "validation.json", validation)
        manifest["errors"].extend(validation["errors"])
        manifest["steps"]["compare"] = "completed"
        manifest["counts"] = {**analysis["summary"], "search_calls": sum(r["search_invoked"] for r in searches), "product_matches": len(matches),
                              "qualified_candidates": sum(m["eligible_for_test"] for m in matches)}
        manifest["status"] = "partial" if manifest["errors"] else "completed"
    except Exception as exc:
        safe = str(exc) if isinstance(exc, ProviderError) else "pipeline_" + type(exc).__name__
        manifest["errors"].append(safe)
        manifest["status"] = "partial" if analysis else "failed"
    finally:
        manifest["finished_at"] = now()
        try:
            if analysis:
                render_report(out, manifest, analysis, matches, searches, plans)
            else:
                (out / "REPORT.md").write_text("# 本次运行未完成\n\n" + "；".join(manifest["errors"]) + "\n\n查看 manifest.json；不能据此判定没有需求或供给。\n", encoding="utf-8")
        except Exception as exc:
            manifest["errors"].append("report_" + type(exc).__name__)
            manifest["status"] = "partial" if analysis else "failed"
        manifest["artifact_sha256"] = {str(p.relative_to(out)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
                                       for p in out.rglob("*") if p.is_file() and p.name != "manifest.json"}
        write_json(out / "manifest.json", manifest)
    return out
