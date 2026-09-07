"""Plan bounded image retrieval from the product main image cited by a demand."""
import ipaddress
from urllib.parse import urlsplit

from runtime_support.text_identity.src.identity import digest


def valid_image_url(value):
    if not isinstance(value, str) or not value or any(c.isspace() for c in value):
        return False
    try:
        url = urlsplit(value)
        if url.scheme not in ('http', 'https') or not url.hostname or url.username or url.password:
            return False
        host = url.hostname.lower().rstrip('.')
        if host == 'localhost' or host.endswith(('.localhost', '.local')):
            return False
        try:
            if not ipaddress.ip_address(host).is_global:
                return False
        except ValueError:
            if '.' not in host:
                return False
        return bool(url.path) and url.port in (None, 80, 443)
    except ValueError:
        return False


def plan_image_searches(cards, evidence, config):
    cards = [c for c in cards if c.get('sourcing_eligible') is True and c.get('prevalence', {}).get('approved') is True]
    lookup = {e['evidence_id']: e for e in evidence}
    plans, scheduled = [], 0
    for pid in sorted({c['product_id'] for c in cards if c['scope'] == 'current'}):
        relevant = [c for c in cards if c['scope'] == 'current' and c['product_id'] == pid]
        refs = sorted({ref for c in relevant for ref in c['support_evidence_ids']})
        sources = [lookup[ref] for ref in refs if ref in lookup and lookup[ref]['product_id'] == pid]
        missing_refs = len(sources) != len(refs)
        # Duplicate observations do not add demand support, but their main-image
        # claims still have to agree with the cited original observation.
        text_groups = {e['text_signal_group'] for e in sources}
        sources += [e for e in evidence if e['evidence_id'] not in refs and e['product_id'] == pid
                    and (e.get('duplicate_of') in refs or (e['text_signal_group'] in text_groups
                         and e['in_window'] is True and e['market_as_reported'] == config['market']))]
        refs = sorted(set(refs) | {e['evidence_id'] for e in sources})
        images = sorted({e['product_main_image_as_reported'] for e in sources
                         if isinstance(e.get('product_main_image_as_reported'), str) and e['product_main_image_as_reported']})
        malformed = any(e.get('product_main_image_as_reported') is not None and
                        not isinstance(e['product_main_image_as_reported'], str) for e in sources)
        reason = ('missing_product_main_image' if not images else
                  'conflicting_product_main_images' if len(images) > 1 else
                  'invalid_product_main_image' if malformed or not valid_image_url(images[0]) else None)
        if missing_refs:
            reason = 'missing_or_mismatched_image_evidence'
        status = 'blocked' if reason else 'ready'
        if status == 'ready':
            if scheduled >= config['limits']['max_queries']:
                status, reason = 'deferred_query_limit', 'configured_query_limit'
            else:
                scheduled += 1
        plans.append({
            'query_id': 'QI-' + digest([pid, images]), 'search_type': 'image',
            'image': images[0] if len(images) == 1 and valid_image_url(images[0]) else None,
            'image_candidates_as_reported': images, 'source_product_id': pid,
            'source_sku_ids': sorted({e['sku_id'] for e in sources if e.get('sku_id')}),
            'evidence_ids': refs, 'review_ids': sorted({e['review_id'] for e in sources if e.get('review_id')}),
            'source_urls': sorted({e['source_url'] for e in sources if isinstance(e.get('source_url'), str)}),
            'demand_ids': [c['demand_id'] for c in relevant], 'status': status, 'reason': reason,
            'purpose': '原商品主图召回相似款，再按差评与具体SKU核对规格',
            'query_basis': '评价来源 productMainImage；URL引用未归档图片像素；图片相似不证明同款或痛点解决',
            'limit': config['limits']['products_per_query'], 'purchase_amount': 1,
            'purchase_amount_basis': 'CLI报价输入，不是采购决定', 'score_level': 'high', 'tags': '4306497'})
    return plans
