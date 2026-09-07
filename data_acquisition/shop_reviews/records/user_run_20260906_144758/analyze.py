"""Analyze a user-supplied review export; never starts remote collection."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import csv, hashlib, json, shutil

BASE = Path(__file__).resolve().parent
WORKSPACE = BASE.parents[2]
SOURCE = Path(r"C:\Users\86130\.codex\attachments\a465db0f-e98a-4de8-b92e-c0f486140f33\pasted-text.txt")
SCREENSHOT = Path(r"C:\Users\86130\AppData\Local\Temp\codex-clipboard-e46a17fa-d257-4f34-8f67-dcae0567c056.png")
START = datetime.fromisoformat("2026-08-30T09:05:42+00:00")
END = datetime.fromisoformat("2026-09-06T09:05:42+00:00")
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def write_json(name, value):
    (BASE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
def snapshot(source, name):
    dest = BASE / name
    if dest.exists():
        if sha(source) != sha(dest):
            raise RuntimeError("Existing snapshot differs; refusing overwrite: " + str(dest))
    else:
        shutil.copy2(source, dest)
    return {"source": str(source), "snapshot": name, "sha256": sha(source), "copy_matches": sha(source) == sha(dest)}

provenance = [snapshot(SOURCE, "raw_reviews.json"), snapshot(SCREENSHOT, "run_screenshot.png")]
raw = json.loads((BASE / "raw_reviews.json").read_text(encoding="utf-8-sig"))
# Analyst annotations refer to observed review IDs, not keywords invented as evidence.
annotations = {
"7679488102971655949": ("material", "对聚酯外观/触感的负面评价；不能据此证实成分，也不能推断必须纯棉。"),
"7675760801130694414": ("fit", "尺码/合身表述含糊，未明确哪个部位偏大或偏小，不推导具体尺寸。"),
"7671947598756005645": ("generic_quality", "笼统质量不满，未给出可检验的缺陷。"),
"7667229258603874061": ("fit", "仅说不合身，方向及部位未知；与相近时间另一个 SKU 评价可能相关。"),
"7667229237183416077": ("fit", "仅说不合身，方向及部位未知；与相近时间另一个 SKU 评价可能相关。"),
"7666285943252043534": ("drape", "认为裤子没有预期飘逸，并自述已退货；不能从中确定必须材质/克重。"),
"7679900019943687949": ("fit", "明确上衣对该评价者太大；审美不满主观，具体尺码、部位和差值未知，退货状态未确认。"),
"7679625345650984718": ("delivery", "自述未收到订单；不能按面料或版型问题处理。"),
"7679203048200242957": ("delivery", "西班牙语 No recibido，意为未收到；不能按面料或版型问题处理。"),
"7670511149582927629": ("delivery", "自述未送达；与相近时间另一个 SKU 评价可能相关。"),
"7670511005911942926": ("delivery", "自述未送达；与相近时间另一个 SKU 评价可能相关。"),
"7667187073610270478": ("empty", "只有低星、无正文，不提炼具体痛点。"),
"7664844254631888654": ("empty", "只有低星、无正文，不提炼具体痛点。"),
"7662128901435246349": ("delivery", "自述未收到包裹；不能按面料或版型问题处理。"),
"7659832827920025357": ("material", "认为面料触感廉价；没有描述粗糙、扎肤、起球或具体替代材质。"),
"7654591523830761229": ("delivery", "自述未收到商品；不能按面料或版型问题处理。"),
}
group_defs = [
("POSSIBLE-RELATED-01", ["7667229258603874061", "7667229237183416077"],
 "同一商品、相同脱敏作者标记、相同正文、不同 SKU，间隔约 11 秒；可能相关，不能确认真实身份相同。"),
("POSSIBLE-RELATED-02", ["7670511149582927629", "7670511005911942926"],
 "同一商品、相同脱敏作者标记、近似未收到货描述、不同 SKU，间隔约 20 秒；可能相关，不能确认真实身份相同。"),
]
groups = {rid: gid for gid, ids, _ in group_defs for rid in ids}
evidence = []
for n, r in enumerate(raw, 1):
    category, note = annotations[r["reviewId"]]
    published = datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00"))
    evidence.append({
        "evidence_id": f"TSR-{n:03d}", "raw_row_1_based": n,
        "platform": "TikTok Shop", "source_kind": "user_supplied_actor_export",
        "review_id": r["reviewId"], "product_id": r["productId"], "sku_id": r["skuId"],
        "source_url": r["productUrl"], "rating": r["rating"],
        "original_text": r["content"], "published_at_utc": r["timestamp"],
        "provider_scraped_at_utc": r["scrapedAt"],
        "in_fixed_window": START <= published < END, "category": category,
        "interpretation": note, "possible_related_group": groups.get(r["reviewId"]),
        "country_as_reported": r.get("authorCountry"),
        "verified_purchase_as_reported": r.get("authorVerified"),
        "sku_size_label": None, "sku_color_label": None, "garment_measurements": None,
        "market_verification": "Actor output reports US; not independently verified buyer residence.",
        "source_verification": "User supplied export and run screenshot; original review not independently reopened.",
    })
product_groups = []
for pid in dict.fromkeys(r["productId"] for r in raw):
    items = [e for e in evidence if e["product_id"] == pid]
    product_groups.append({
        "product_id": pid, "title_as_reported": next(r["productTitle"] for r in raw if r["productId"] == pid),
        "review_rows": len(items), "in_fixed_window": sum(e["in_fixed_window"] for e in items),
        "categories": dict(Counter(e["category"] for e in items)),
        "coverage": "Returned sample only; total one-star review count and feed completeness unknown.",
    })
dates = [datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00")) for r in raw]
summary = {
    "run_record": "user_run_20260906_144758",
    "state_reference": "../../TASK_STATE.md",
    "schema_reference": "../../../docs/superpowers/specs/2026-09-06-clothing-demand-agent-v1-design.md",
    "verified_at_utc": datetime.now(timezone.utc).isoformat(),
    "provenance": provenance,
    "screenshot_observations": {"status": "Succeeded", "dataset_results": 16, "cost_usd_displayed": 0.032,
        "duration_seconds_displayed": 31, "billing_ledger_verified": False,
        "input_settings_independently_read": False},
    "counts": {"rows": len(raw), "unique_review_ids": len({r["reviewId"] for r in raw}),
        "duplicate_review_id_rows": len(raw)-len({r["reviewId"] for r in raw}),
        "products": len(product_groups), "nonempty_text": sum(bool(r["content"].strip()) for r in raw),
        "in_fixed_window": sum(e["in_fixed_window"] for e in evidence),
        "outside_fixed_window": sum(not e["in_fixed_window"] for e in evidence),
        "possible_related_groups": len(group_defs), "independent_buyers": None,
        "reported_us": sum(r.get("authorCountry") == "US" for r in raw),
        "reported_verified_purchase": sum(r.get("authorVerified") is True for r in raw)},
    "categories": dict(Counter(e["category"] for e in evidence)),
    "review_dates": {"earliest": min(dates).isoformat(), "latest": max(dates).isoformat()},
    "fixed_window_snapshot": {"start_inclusive_utc": START.isoformat(), "end_exclusive_utc": END.isoformat(), "rolled": False},
    "products": product_groups,
    "possible_related_groups": [{"id": g, "review_ids": ids, "basis": reason, "confirmed_duplicate": False}
                                for g, ids, reason in group_defs],
    "limits": ["No full-rating denominator; cannot estimate a product's negative-review rate or pain prevalence.",
               "SKU IDs are present but size/color labels and measurements are absent.",
               "One manual run is evidence of returned samples, not unattended reliability or complete history.",
               "User execution does not by itself resolve provider commercial-use scope.",
               "No purchase conversion, inventory or product problem resolution verified."],
    "agent_actions": {"paid_collection_started": False, "credentials_read": False, "browser_connected": False,
                      "supplier_contacted": False, "procurement_search_started": False},
}
cards = [
 {"demand_id": "S1-TSR-CURRENT-01", "method": "S1", "status": "待补证据", "window_scope": "current_fixed_window",
  "support_evidence_ids": ["TSR-007"], "product_id": "1732331935794958838", "sku_id": "1732475515663127030",
  "demand_statement": "该上衣的一位评价者认为衣服明显太大，希望获得更合身的穿着效果。",
  "confirmed_from_text": ["评价者表示上衣太大"], "counter_evidence_ids": [],
  "unknown": ["所购尺码名称", "胸围/腰围/衣长等偏大部位", "目标成衣尺寸", "偏差是否跨尺码存在", "其他独立同类评价"],
  "hypotheses": ["尺码标注或成衣尺寸可能与期望不符；尚不能排除选码或个人版型偏好问题。"],
  "do_not_infer": ["必须修身版", "必须小个子尺码", "应买 S 码", "具体胸围或衣长", "该商品普遍偏大"],
  "matching_status": "需要具体尺寸与原商品尺码对照，尚不足以验证某款现货已解决问题",
  "procurement_candidates": []},
 {"demand_id": "S1-TSR-HISTORY-01", "method": "S1", "status": "线索", "window_scope": "outside_current_window",
  "support_evidence_ids": ["TSR-006"], "product_id": "1732410109013955024",
  "demand_statement": "一条历史评价希望裤子有更好的飘逸/垂坠表现。",
  "unknown": ["目标垂坠表现", "具体成分与结构", "当前仍存在的独立需求"], "procurement_candidates": []},
 {"demand_id": "S1-TSR-HISTORY-02", "method": "S1", "status": "线索", "window_scope": "outside_current_window",
  "support_evidence_ids": ["TSR-001", "TSR-015"],
  "demand_statement": "两个商品的历史评价分别对聚酯外观触感和面料廉价感表达不满；保留不同上下文。",
  "unknown": ["可接受的触感", "必须成分", "可测量的品质条件", "当前同类需求"],
  "do_not_infer": ["消费者均要求纯棉", "聚酯成分本身证实质量差", "两条评价要求相同替代面料"],
  "procurement_candidates": []}
]
write_json("evidence.json", evidence)
write_json("analysis.json", summary)
write_json("demand_cards.json", cards)
with (BASE / "review_analysis.csv").open("w", encoding="utf-8-sig", newline="") as f:
    columns = ["evidence_id", "review_id", "product_id", "sku_id", "rating", "published_at_utc",
               "in_fixed_window", "category", "original_text", "interpretation", "possible_related_group", "source_url"]
    writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(evidence)
write_json("next_input_two_star.json", {
    "urls": [], "productIds": ["1732331935794958838", "1732381281439289620", "1732410109013955024"],
    "country": "US", "maxReviewsPerTarget": 10, "sortBy": "newest", "starRating": 2, "withPhotosOnly": False})
errors = []
if len(raw) != 16: errors.append("Rows differ from screenshot result count")
if set(annotations) != {r["reviewId"] for r in raw}: errors.append("Annotations do not cover exactly the source IDs")
if len({r["reviewId"] for r in raw}) != len(raw): errors.append("Duplicate review IDs")
if not all(r["status"] == "Success" and r["rating"] == 1 for r in raw): errors.append("Unexpected status or rating")
expected_current = {"7679900019943687949"}
if {e["review_id"] for e in evidence if e["in_fixed_window"]} != expected_current:
    errors.append("Unexpected fixed-window result")
seeds = list(csv.DictReader((WORKSPACE / "tiktok_us_data_acceptance_2026-09-05/category_601152_2026-09-06/products.csv").open(encoding="utf-8-sig")))
if not {r["productId"] for r in raw} <= {p["product_id"] for p in seeds}: errors.append("Product outside original seeds")
if not all(r["productUrl"].rstrip("/").endswith(r["productId"]) for r in raw): errors.append("URL/product mismatch")
for r in raw:
    for key in ["reviewId", "productId", "skuId"]:
        if not isinstance(r[key], str): errors.append("Identifier must remain a string: " + key)
if any(e["original_text"] != raw[e["raw_row_1_based"]-1]["content"] for e in evidence):
    errors.append("Evidence text changed")
for card in cards:
    if not set(card["support_evidence_ids"]) <= {e["evidence_id"] for e in evidence}: errors.append("Missing evidence reference")
    if card["window_scope"] == "current_fixed_window":
        if any(not e["in_fixed_window"] for e in evidence if e["evidence_id"] in card["support_evidence_ids"]):
            errors.append("Historical evidence leaked into current card")
parsed = []
for p in BASE.glob("*.json"):
    if p.name == "validation.json": continue
    json.loads(p.read_text(encoding="utf-8-sig"))
    parsed.append(p.name)
with (BASE / "review_analysis.csv").open(encoding="utf-8-sig", newline="") as f:
    csv_rows = list(csv.DictReader(f))
if len(csv_rows) != len(evidence): errors.append("CSV row count mismatch")
for index, row in enumerate(csv_rows):
    if row["original_text"] != raw[index]["content"]: errors.append("CSV text mismatch")
validation = {"verified_at_utc": datetime.now(timezone.utc).isoformat(), "json_files_parsed": parsed,
    "csv_rows_checked": len(csv_rows), "source_hashes_match": all(p["copy_matches"] for p in provenance),
    "scope": "Import integrity, ID/product references, original text preservation, fixed-window filtering, evidence references and record consistency; no independent source-page, buyer identity or supplier verification.",
    "errors": errors, "passed": not errors}
write_json("validation.json", validation)
print(json.dumps({"counts": summary["counts"], "categories": summary["categories"],
    "products": [{"product_id": p["product_id"], "review_rows": p["review_rows"], "in_fixed_window": p["in_fixed_window"]} for p in product_groups],
    "validation": validation}, ensure_ascii=False, indent=2))
if errors: raise SystemExit(1)

