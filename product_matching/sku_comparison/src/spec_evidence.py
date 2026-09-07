"""Validate externally supplied SKU snapshots and review-specific targets."""
from datetime import datetime
from decimal import Decimal
import math

from demand_discovery.pain_classification.src.rules import ISSUES

BASES = {'garment_length', 'garment_flat_width', 'garment_circumference', 'body_circumference'}
EMPTY_EVIDENCE = {'schema_version': 1, 'sku_records': [], 'review_targets': []}


def name_key(value):
    return value.strip().casefold()


def number(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError('specification_number_invalid')
    return Decimal(str(value))


def text(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('specification_text_required')
    return value


def provenance(record):
    text(record.get('source_ref'))
    stamp = datetime.fromisoformat(text(record.get('checked_at')).replace('Z', '+00:00'))
    if stamp.utcoffset() is None:
        raise ValueError('specification_timezone_required')


def measurements(items, target=False):
    if not isinstance(items, list):
        raise ValueError('measurements_must_be_array')
    seen = set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError('measurement_must_be_object')
        key = (name_key(text(item.get('name'))), item.get('basis'))
        if key[1] not in BASES or item.get('unit') not in ('cm', 'inch') or key in seen:
            raise ValueError('measurement_identity_or_unit_invalid')
        seen.add(key)
        if target:
            minimum, maximum = number(item.get('min')), number(item.get('max'))
            if minimum < 0 or maximum <= 0 or minimum > maximum:
                raise ValueError('measurement_range_invalid')
        elif number(item.get('value')) <= 0:
            raise ValueError('measurement_must_be_positive')


def materials(items, complete=False):
    if not isinstance(items, dict):
        raise ValueError('materials_must_be_object')
    seen, total = set(), Decimal(0)
    for name, amount in items.items():
        key = name_key(text(name))
        value = number(amount)
        if key in seen or not 0 <= value <= 100:
            raise ValueError('material_identity_or_percentage_invalid')
        seen.add(key)
        total += value
    if total > 100 or (complete and total != 100):
        raise ValueError('material_composition_total_invalid')


def validate_spec_evidence(data):
    if not isinstance(data, dict) or type(data.get('schema_version')) is not int or data['schema_version'] != 1:
        raise ValueError('specification_schema_version_invalid')
    for collection in ('sku_records', 'review_targets'):
        if not isinstance(data.get(collection), list):
            raise ValueError('specification_collections_required')
    identities = set()
    for record in data['sku_records']:
        if not isinstance(record, dict):
            raise ValueError('sku_record_must_be_object')
        identity = tuple(text(record.get(k)) for k in ('platform', 'product_id', 'sku_id'))
        if identity[0] not in ('tiktok', '1688') or identity in identities:
            raise ValueError('sku_identity_duplicate_or_invalid')
        identities.add(identity)
        provenance(record)
        if 'size_label' in record:
            text(record['size_label'])
        if type(record.get('composition_complete', False)) is not bool:
            raise ValueError('composition_complete_must_be_boolean')
        measurements(record.get('measurements', []))
        materials(record.get('materials', {}), record.get('composition_complete', False))
    identities = set()
    for record in data['review_targets']:
        if not isinstance(record, dict):
            raise ValueError('review_target_must_be_object')
        identity = tuple(text(record.get(k)) for k in ('review_id', 'issue'))
        for key in ('source_product_id', 'source_sku_id'):
            text(record.get(key))
        if identity in identities or identity[1] not in ISSUES:
            raise ValueError('review_target_duplicate_or_issue_invalid')
        identities.add(identity)
        provenance(record)
        measurements(record.get('measurements', []), target=True)
        materials(record.get('materials', {}))
    return data


def in_cm(value, unit):
    return number(value) * (Decimal('2.54') if unit == 'inch' else Decimal(1))
