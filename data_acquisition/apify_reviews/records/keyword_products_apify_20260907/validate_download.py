"""Validate the saved API result without network access or changing raw evidence."""
from collections import Counter
from datetime import datetime
from pathlib import Path
import csv
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
PILOT = ROOT / "data_acquisition/fastmoss_catalog/records/keyword_product_review_pilot_20260907"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def time(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None
    return parsed


def normalize_dom_text(value):
    if value.startswith('"') and value.endswith('"'):
        value = json.loads(value)
    return re.sub(r"\s+", " ", value).strip()


def main():
    rows = read(OUT / "api_reviews.json")
    products = read(PILOT / "products.json")
    config = read(ROOT / "workflow_execution/run_configuration/config/current_round.json")
    run = read(OUT / "run_latest.json")
    source = read(OUT / "dataset_read_provenance.json")
    requested = read(OUT / "actor_input.json")
    submitted = read(OUT / "submitted_input.json")
    assert run["id"] == "NjEXpgqOIip3PeBcU" and run["status"] == "SUCCEEDED"
    assert run["options"]["maxTotalChargeUsd"] == 2 and run["usageTotalUsd"] < 2
    assert requested["starRating"] == 0 and requested["withPhotosOnly"] is False
    assert submitted == dict(requested, maxProductsPerShop=5)
    assert len(rows) == source["item_count"] == run["chargedEventCounts"]["review-scraped"] == 366
    assert len({r["reviewId"] for r in rows}) == len(rows)
    assert {r["productId"] for r in rows} == set(requested["productIds"])
    for row in rows:
        assert row["status"] == "Success" and type(row["rating"]) is int and 1 <= row["rating"] <= 5
        assert all(isinstance(row[k], str) and row[k].isdigit() for k in ["productId", "reviewId", "skuId", "sourceShopId"])
        assert row["productId"] in row["productUrl"]
        time(row["timestamp"])
    start, end = time(config["window"]["start"]), time(config["window"]["end"])
    current = [r for r in rows if start <= time(r["timestamp"]) < end]
    save("window_reviews.json", current)
    log = (OUT / "run_log.redacted.txt").read_text(encoding="utf-8")
    summaries = []
    for product in products:
        pid = product["product_id"]
        selected = [r for r in rows if r["productId"] == pid]
        in_window = [r for r in current if r["productId"] == pid]
        counts = re.search(r"\[product " + pid + r"\] pushed (\d+) reviews \(total reported: (\d+)\)", log)
        assert counts and int(counts[1]) == int(counts[2]) == len(selected)
        assert len(selected) < requested["maxReviewsPerTarget"]
        assert {r["sourceShopId"] for r in selected} == {product["shop_id"]}
        assert len({r["productTitle"] for r in selected}) == 1
        nonempty = [r for r in selected if r["content"].strip()]
        repeated = [n for n in Counter(normalize_dom_text(r["content"]) for r in nonempty).values() if n > 1]
        summaries.append({
            "product_id": pid, "name": product["short_name"], "rows": len(selected), "unique_review_ids": len(selected),
            "rating_counts": dict(Counter(r["rating"] for r in selected)), "window_rows": len(in_window),
            "window_nonempty_bodies": sum(bool(r["content"].strip()) for r in in_window),
            "empty_bodies": len(selected) - len(nonempty), "duplicate_nonempty_body_groups": len(repeated),
            "author_countries_reported": dict(Counter(r.get("authorCountry") for r in selected)),
            "unique_sku_ids": len({r["skuId"] for r in selected}),
            "log_reported_total": int(counts[2]), "read_count_matches_public_feed_report": True,
            "previous_web_global_count": product["global_review_count_display"],
            "difference_from_previous_web_count": len(selected) - product["global_review_count_display"],
            "complete_business_sample": None, "valid_review_denominator": None, "independent_buyers": None,
            "sku_color_size_mapping_from_actor": None,
            "notes": "数量覆盖匹配本次Actor公开流报告；不证明平台所有历史/已删除/不可见评价。有效性和买家身份仍需核验。"
        })
    prior = read(PILOT / "source_reviews.transcribed.json")
    extra = read(PILOT / "bra_page_02.transcribed.json")
    comparisons = []
    for group in prior + [extra]:
        for idx, row in enumerate(group["reviews"]):
            matched = [r for r in rows if r["productId"] == group["product_id"] and r["rating"] == row["rating"]
                       and normalize_dom_text(r["content"]) == normalize_dom_text(row["text"])]
            comparisons.append({"product_id": group["product_id"], "web_page": group.get("page", 1),
                "web_row_index": idx, "web_variant_label": row["variant_label"], "web_date_label": row["date"],
                "match_count": len(matched), "review_id": matched[0]["reviewId"] if len(matched) == 1 else None,
                "sku_id": matched[0]["skuId"] if len(matched) == 1 else None,
                "api_timestamp": matched[0]["timestamp"] if len(matched) == 1 else None,
                "api_author_verified": matched[0]["authorVerified"] if len(matched) == 1 else None,
                "match_basis": "同商品、同星级、正文仅规范化快照引号与空白后唯一匹配；颜色尺码仍来自先前网页快照"})
    save("previous_sample_crosscheck.json", comparisons)
    summary = {"run_id": run["id"], "dataset_id": run["defaultDatasetId"], "new_actor_runs": 1,
        "actor_total_cost_usd": run["usageTotalUsd"], "cap_usd": 2, "review_rows": len(rows), "window": config["window"],
        "window_rows": len(current), "products": summaries, "all_fields": sorted({k for r in rows for k in r}),
        "stable_buyer_id_field_returned": False, "demand_cards_generated": 0, "sourcing_queries": 0,
        "raw_source_sha256": hashlib.sha256((OUT / "api_reviews.json").read_bytes()).hexdigest()}
    save("collection_summary.json", summary)
    with (OUT / "collection_summary.csv").open("w", encoding="utf-8-sig", newline="") as file:
        fields = ["product_id", "name", "rows", "window_rows", "window_nonempty_bodies", "empty_bodies", "unique_sku_ids"]
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(summaries)
    protected = read(PILOT / "validation.json")["protected_files"]
    for path, record in protected.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == record["sha256"]
    for name, expected in read(PILOT / "validation.json")["artifact_sha256"].items():
        assert hashlib.sha256((PILOT / name).read_bytes()).hexdigest() == expected
    validation = {"status": "passed", "run_id": run["id"], "download_count": len(rows), "unique_review_ids": len(rows),
        "all_product_shop_ids_match": True, "all_ids_are_strings": True, "all_timestamps_timezone_aware": True,
        "all_sku_ids_present": True, "all_star_request_verified": True, "actor_log_totals_match": True,
        "dataset_stable_during_download": True, "per_product_cap_hit": False, "cost_cap_hit": False,
        "previous_web_reviews_checked": len(comparisons), "previous_web_reviews_uniquely_matched": sum(x["match_count"] == 1 for x in comparisons),
        "historical_protected_files_unchanged": True, "browser_pilot_snapshot_unchanged": True,
        "network_requests_for_validation": 0, "limits": "未核验稳定买家、所有评价有效性、全部SKU颜色尺码、适用表或面料；未运行需求生成和找货。"}
    save("download_validation.json", validation)
    print(json.dumps({"summary": summary, "validation": validation}, ensure_ascii=False))


if __name__ == "__main__":
    main()
