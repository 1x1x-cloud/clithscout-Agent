"""ClothScout module; migrated without changing business thresholds."""
import re
from runtime_support.text_identity.src.identity import digest

CATEGORIES = {"trousers": "长裤", "top": "上衣", "dress": "连衣裙", "skirt": "半身裙", "shorts": "短裤"}


def plan_searches(cards, config, evidence=None):
    cards = [c for c in cards if c.get('sourcing_eligible') is True and c.get('prevalence', {}).get('approved') is True]
    if config.get("search_strategy", "text") == "image":
        from product_sourcing.query_planning.src.image_planner import plan_image_searches
        return plan_image_searches(cards, evidence or [], config)
    plans = []
    keys = sorted({(c["category"], c["product_id"]) for c in cards if c["scope"] == "current" and c["category"] in CATEGORIES})
    for category, product_id in keys:
        relevant = [c for c in cards if c["scope"] == "current" and c["category"] == category and c["product_id"] == product_id]
        if not relevant:
            continue
        titles = " ".join(relevant[0].get("source_titles_as_reported", []))
        translations = [(r"\bstriped?\b", "条纹"), (r"\bhalter\b", "挂脖"),
                        (r"\bknit(?:ted)?\b", "针织"), (r"\bdrawstring\b", "抽绳"), (r"\bwide[- ]leg\b", "阔腿")]
        context_terms = [label for pattern, label in translations if re.search(pattern, titles, re.IGNORECASE)]
        query = " ".join(context_terms + [CATEGORIES[category], "国内现货 提供具体SKU尺码表和成衣尺寸"])
        plans.append({"query_id": "Q-" + digest(query), "query": query,
                      "demand_ids": [c["demand_id"] for c in relevant],
                      "purpose": "同品类探索；缺少目标规格，不声称已解决痛点或同款",
                      "query_basis": "商品标题提供品类/款式背景；不是评论者要求保留这些属性。尺码表是核验资料，不是已确认商品属性",
                      "context_terms_from_title": context_terms,
                      "limit": config["limits"]["products_per_query"],
                      "purchase_amount": 1, "purchase_amount_basis": "CLI报价输入，不是采购决定",
                      "score_level": "high", "tags": "4306497"})
    merged = {}
    for plan in plans:
        if plan["query_id"] in merged:
            merged[plan["query_id"]]["demand_ids"].extend(plan["demand_ids"])
        else:
            merged[plan["query_id"]] = plan
    return list(merged.values())[:config["limits"]["max_queries"]]
