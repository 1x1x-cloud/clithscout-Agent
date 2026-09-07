"""ClothScout module; migrated without changing business thresholds."""
from evidence_processing.garment_context.src.classifier import garment

def compare_product(card, product):
    title, sku = str(product.get("title") or ""), str(product.get("sku_title") or "")
    title_category, sku_category = garment(title), garment(sku)
    # Explicit single-component SKU outranks a multi-component offer title.
    if sku_category is None and any(word in sku for word in ("单裤", "仅裤", "裤子")) and not any(word in sku for word in ("上衣+", "上衣＋", "套装", "整套")):
        sku_category = "trousers"
    category = sku_category or title_category
    relation = "unknown" if category is None else ("met" if category == card["category"] else "conflict")
    conditions = [
        {"condition": "服装品类与本次线索对应", "status": relation,
         "evidence": {"title_as_reported": title, "sku_title_as_reported": sku},
         "limit": "标题/SKU文字初筛，不代表款式或实物核验"},
        {"condition": card["statement"] + "：替代商品满足明确目标", "status": "unknown",
         "reason": "原评论缺少可检验目标；返回的标题、尺码标签不能证明痛点解决",
         "evidence_ids": card["support_evidence_ids"]},
        {"condition": "具体SKU规格及材质/成衣尺寸", "status": "unknown",
         "reason": "SKU标签不是完整规格或实测"},
        {"condition": "当前可采购状态、价格数量条件、发货地和交付要求", "status": "unknown",
         "reason": "只有搜索返回；未完成V1供货核验"},
    ]
    return {"demand_id": card["demand_id"], "product_id": str(product["product_id"]),
            "sku_id": str(product["sku_id"]) if product.get("sku_id") is not None else None,
            "source_product": product, "conditions": conditions,
            "style_related": relation, "demand_satisfied": "unknown", "supply_verified": False,
            "verified_stock": None, "stock_as_reported": product.get("stock_amount"),
            "stock_limit": "CLI缺失值可能映射为0；包括正数在内均未独立核实",
            "eligible_for_test": False,
            "decision": "排除：品类/SKU冲突" if relation == "conflict" else "待人工核验",
            "next_action": "补原商品所购尺码和目标尺寸；对齐替代商品SKU后核验规格及供货",
            "ctr": None, "click_to_order_rate": None, "breakout_probability": None}
