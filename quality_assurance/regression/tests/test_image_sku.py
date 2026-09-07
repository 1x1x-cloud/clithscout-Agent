"""Synthetic workflow checks; examples are not market or supplier evidence."""
import contextlib
import copy
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from demand_discovery.analysis_workflow.src.analyze import analyze
from product_sourcing.query_planning.src.planner import plan_searches
from product_sourcing.skill_adapter.src.client import search_1688
from runtime_support.project_paths.src.paths import PROJECT_ROOT
from workflow_execution.pipeline.src.orchestrator import run_pipeline
from workflow_execution.cli.src.main import main
from quality_assurance.regression.tests.test_pipeline import CONFIG, review
from quality_assurance.regression.fixtures.qualified_reviews import qualified_analysis, write_qualified, expanded_targets

IMAGE = 'https://example.invalid/product-main.jpg'


def image_config():
    return dict(copy.deepcopy(CONFIG), search_strategy='image')


def image_analysis(rows=None):
    return qualified_analysis(rows or [review(productMainImage=IMAGE)], image_config())


def plans_for(rows=None, config=None):
    result = image_analysis(rows)
    return plan_searches(result['demand_cards'], config or image_config(), result['evidence'])


def dimension(value, unit='cm', basis='garment_length'):
    return dict(name='inseam', value=value, unit=unit, basis=basis)


def dossier():
    provenance = dict(source_ref='https://example.invalid/specification', checked_at='2026-09-06T09:00:00Z')
    return {'schema_version': 1, 'sku_records': [
        dict(platform='tiktok', product_id='synthetic-product', sku_id='synthetic-sku',
             measurements=[dimension(85)], materials={'cotton': 100}, composition_complete=True, **provenance),
        dict(platform='1688', product_id='candidate', sku_id='candidate-sku',
             measurements=[dimension(30, 'inch')], materials={'cotton': 95, 'elastane': 5}, composition_complete=True, **provenance)],
        'review_targets': [dict(review_id='synthetic-new-id', source_product_id='synthetic-product',
            source_sku_id='synthetic-sku', issue='too_long',
            measurements=[dict(name='inseam', min=75, max=77, unit='cm', basis='garment_length')],
            materials={'cotton': 90}, **provenance)]}


def candidate(**changes):
    return dict(dict(product_id='candidate', title='休闲长裤', sku_id='candidate-sku',
                     sku_title='黑色 M', image_url='https://example.invalid/candidate.jpg',
                     detail_url='https://example.invalid/candidate', stock_amount=12), **changes)


def payload():
    return {'success': True, 'markdown': '| Original provider table |\n|---|\n| candidate |',
            'data': {'data': {'success': True, 'search_type': 'image_similarity',
                             'source_image': IMAGE, 'similar_products': [candidate()]}}}


class ImagePlanningCases(unittest.TestCase):
    def test_duplicate_review_image_conflicts_are_not_discarded(self):
        plan = plans_for([review(productMainImage=IMAGE), review(productMainImage='https://example.invalid/different.jpg')])[0]
        self.assertEqual(plan['status'], 'blocked')
        self.assertEqual(plan['reason'], 'conflicting_product_main_images')
        self.assertGreaterEqual(len(plan['evidence_ids']), 2)

    def test_product_main_image_has_traceable_source_not_review_photo(self):
        row = review(productMainImage=IMAGE, images=['https://example.invalid/review.jpg'],
                     authorAvatar='https://example.invalid/avatar.jpg')
        plan = plans_for([row])[0]
        self.assertEqual(plan['search_type'], 'image')
        self.assertEqual(plan['image'], IMAGE)
        self.assertEqual(plan['source_product_id'], row['productId'])
        self.assertEqual(plan['status'], 'ready')
        self.assertEqual(plan['source_sku_ids'], [row['skuId']])
        self.assertTrue(plan['evidence_ids'])

    def test_no_image_does_not_fall_back_to_text_or_avatar(self):
        for value in (None, '', 'file:///secret', 'https://user:pass@example.invalid/x', 'http://127.0.0.1/x'):
            with self.subTest(value=value):
                plan = plans_for([review(productMainImage=value, authorAvatar=IMAGE)])[0]
                self.assertEqual(plan['status'], 'blocked')
                self.assertNotIn('query', plan)

    def test_conflicting_main_images_require_review(self):
        plans = plans_for([review(productMainImage=IMAGE), review(reviewId='r2', productMainImage='https://example.invalid/other.jpg')])
        self.assertEqual(len(plans), 1)
        self.assertEqual(plans[0]['reason'], 'conflicting_product_main_images')

    def test_same_product_merges_pain_cards_but_other_product_stays_separate(self):
        rows = [review('Pants are too long and too big', productMainImage=IMAGE),
                review(productId='other-product', reviewId='r2', productMainImage=IMAGE)]
        plans = plans_for(rows)
        self.assertEqual(len(plans), 2)
        self.assertEqual(len({p['query_id'] for p in plans}), 2)
        self.assertEqual(sum(p['status'] == 'ready' for p in plans), 1)
        self.assertEqual(sum(p['status'] == 'deferred_query_limit' for p in plans), 1)
        self.assertEqual(sorted(len(p['demand_ids']) for p in plans), [1, 2])

    def test_no_evidence_is_blocked_not_title_search(self):
        result = image_analysis()
        plans = plan_searches(result['demand_cards'], image_config())
        self.assertEqual(plans[0]['status'], 'blocked')


class ImageAdapterCases(unittest.TestCase):
    def test_response_must_identify_the_same_image_search(self):
        from product_sourcing.result_parsing.src.parser import parse_search
        from runtime_support.provider_errors.src.errors import ProviderError
        for field, value in [('source_image', 'https://example.invalid/other.jpg'), ('search_type', 'text')]:
            data = payload()
            data['data']['data'][field] = value
            with self.subTest(field=field), self.assertRaises(ProviderError):
                parse_search(data, expected_image=IMAGE)

    def test_image_subprocess_uses_argument_list_and_preserves_full_response(self):
        from PIL import Image
        from product_sourcing.skill_adapter.src.image_input import prepare_image
        plan = dict(search_type='image', image=IMAGE, limit=3, status='ready')
        returned = subprocess.CompletedProcess([], 0, json.dumps(payload()), '')
        fixture = io.BytesIO()
        Image.new('RGB', (2, 2)).save(fixture, format='JPEG')
        with tempfile.TemporaryDirectory() as directory, patch('product_sourcing.skill_adapter.src.image_input.download_image', return_value=(fixture.getvalue(), IMAGE, 'image/jpeg')):
            plan['image_input'] = prepare_image(IMAGE, Path(directory), 'QI-test')
            with patch('product_sourcing.skill_adapter.src.client.subprocess.run', return_value=returned) as execute:
                result = search_1688(plan, PROJECT_ROOT / 'product_sourcing/1688_skill/vendor/1688-product-find/cli.py')
        args, kwargs = execute.call_args
        self.assertEqual(args[0][3:6], ['image_search', '--image', plan['image_input']['cli_image_path']])
        self.assertNotIn('--query', args[0])
        self.assertFalse(kwargs['shell'])
        self.assertEqual(result, payload())


class SpecificationCases(unittest.TestCase):
    def test_unknown_original_category_is_not_a_proven_conflict(self):
        result = self.inspect(rows=[review(productTitle='Soft knitwear', productMainImage=IMAGE)])
        self.assertEqual(result['style_related'], 'unknown')
        self.assertNotIn('排除', result['decision'])

    def test_explicit_targets_do_not_keep_a_stale_missing_target_reason(self):
        result = self.inspect()
        self.assertEqual(result['specification_status'], 'met')
        self.assertNotIn('原评论缺少可检验目标', result['conditions'][1]['reason'])
        self.assertEqual(result['demand_satisfied'], 'unknown')

    def inspect(self, evidence=None, product=None, rows=None):
        from product_matching.sku_comparison.src.inspection import inspect_product
        from product_matching.sku_comparison.src.spec_evidence import validate_spec_evidence
        result = image_analysis(rows)
        data = evidence if evidence is not None else dossier()
        data = expanded_targets(data)
        validate_spec_evidence(data)
        return inspect_product(result['demand_cards'][0], product or candidate(), result['evidence'], data)

    def statuses(self, result):
        return {c['dimension']: c['status'] for c in result['spec_checks']}

    def test_traceable_measurements_convert_inches_but_never_approve_supply(self):
        result = self.inspect()
        self.assertEqual(self.statuses(result), {'sku': 'met', 'size': 'met', 'material': 'met'})
        self.assertFalse(result['eligible_for_test'])
        self.assertFalse(result['supply_verified'])
        self.assertEqual(result['demand_satisfied'], 'unknown')
        self.assertEqual(result['source_reviews'][0]['sku_id'], 'synthetic-sku')

    def test_size_labels_and_similarity_scores_do_not_satisfy_measurements(self):
        result = self.inspect({'schema_version': 1, 'sku_records': [], 'review_targets': []}, candidate(similarity_score=0.999))
        self.assertEqual(self.statuses(result), {'sku': 'unknown', 'size': 'unknown', 'material': 'unknown'})

    def test_wrong_candidate_sku_cannot_borrow_specs(self):
        result = self.inspect(product=candidate(sku_id='another-sku'))
        self.assertEqual(self.statuses(result), {'sku': 'unknown', 'size': 'unknown', 'material': 'unknown'})

    def test_wrong_original_sku_target_is_flagged(self):
        data = dossier()
        data['review_targets'][0]['source_sku_id'] = 'wrong-sku'
        result = self.inspect(data)
        self.assertEqual(self.statuses(result)['size'], 'unknown')
        self.assertIn('target_identity_mismatch', result['spec_checks'][1]['reason'])

    def test_outside_range_and_material_below_target_are_conflicts(self):
        data = dossier()
        data['sku_records'][1]['measurements'] = [dimension(90)]
        data['sku_records'][1]['materials'] = {'polyester': 100}
        result = self.inspect(data)
        self.assertEqual(self.statuses(result)['size'], 'conflict')
        self.assertEqual(self.statuses(result)['material'], 'conflict')
        self.assertIn('排除', result['decision'])

    def test_body_and_garment_measurements_are_not_interchangeable(self):
        data = dossier()
        data['sku_records'][1]['measurements'][0]['basis'] = 'body_circumference'
        self.assertEqual(self.statuses(self.inspect(data))['size'], 'unknown')

    def test_incomplete_composition_does_not_mean_missing_fiber_is_zero(self):
        data = dossier()
        data['sku_records'][1].update(materials={'polyester': 10}, composition_complete=False)
        self.assertEqual(self.statuses(self.inspect(data))['material'], 'unknown')

    def test_missing_original_measurements_does_not_claim_comparison_complete(self):
        data = dossier()
        data['sku_records'][0]['measurements'] = []
        self.assertEqual(self.statuses(self.inspect(data))['size'], 'unknown')

    def test_each_complaining_sku_gets_its_own_checks(self):
        rows = [review(productMainImage=IMAGE), review('My pants are too long around the legs', reviewId='other-review', skuId='other-size', productMainImage=IMAGE)]
        result = self.inspect(rows=rows)
        self.assertEqual(len(result['spec_checks']), 18)
        other = [c for c in result['spec_checks'] if c['review_id'] == 'other-review']
        self.assertTrue(all(c['status'] == 'unknown' for c in other))

    def test_invalid_and_duplicate_dossiers_are_rejected(self):
        from product_matching.sku_comparison.src.spec_evidence import validate_spec_evidence
        mutations = [
            lambda d: d['sku_records'].append(copy.deepcopy(d['sku_records'][0])),
            lambda d: d['sku_records'][0].update(product_id=123),
            lambda d: d['sku_records'][0].update(checked_at='2026-09-06'),
            lambda d: d['sku_records'][0].update(materials={'cotton': 120}),
            lambda d: d['review_targets'][0]['measurements'][0].update(min=100, max=90),
            lambda d: d['sku_records'][0]['measurements'][0].update(value=float('nan')),
            lambda d: d['sku_records'][0]['measurements'][0].update(unit='m'),
            lambda d: d['review_targets'].append(copy.deepcopy(d['review_targets'][0])),
        ]
        for mutate in mutations:
            data = dossier()
            mutate(data)
            with self.subTest(data=data), self.assertRaises(ValueError):
                validate_spec_evidence(data)


class ImagePipelineCases(unittest.TestCase):
    def test_recheck_applies_new_specs_without_repeating_image_search(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source, specs = root / 'reviews.json', root / 'specs.json'
            review_info = write_qualified(source, [review(productMainImage=IMAGE)], image_config())
            out = run_pipeline(image_config(), root / 'runs', reviews_path=source, review_evidence_path=review_info,
                               search_fn=lambda _: payload(), search_mode='synthetic_test')
            original = json.loads((out / 'product_matches.json').read_text(encoding='utf-8'))[0]
            original_spec_bytes = (out / 'sku_evidence.json').read_bytes()
            self.assertEqual(original['specification_status'], 'unknown')
            specs.write_text(json.dumps(expanded_targets(dossier())), encoding='utf-8')
            stdout = io.StringIO()
            with patch('sys.argv', ['clothscout', '--recheck-run', str(out), '--sku-evidence', str(specs), '--output-root', str(root / 'rechecked')]), \
                 patch('product_sourcing.skill_adapter.src.client.subprocess.run', side_effect=AssertionError('Network forbidden')), \
                 contextlib.redirect_stdout(stdout):
                code = main()
            self.assertEqual(code, 0, stdout.getvalue())
            checked = Path(json.loads(stdout.getvalue())['output_directory'])
            result = json.loads((checked / 'product_matches.json').read_text(encoding='utf-8'))[0]
            self.assertEqual(result['specification_status'], 'met')
            self.assertEqual(result['checked_at'], original['checked_at'])
            self.assertEqual(result['source_mode'], 'recheck')
            self.assertEqual((out / 'sku_evidence.json').read_bytes(), original_spec_bytes)

    def test_end_to_end_archives_specs_and_replays_without_network(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            reviews = root / 'reviews.json'
            specs = root / 'specs.json'
            review_info = write_qualified(reviews, [review(productMainImage=IMAGE)], image_config())
            specs.write_text(json.dumps(expanded_targets(dossier())), encoding='utf-8')
            calls = []
            def search(plan):
                calls.append(plan)
                return payload()
            out = run_pipeline(image_config(), root / 'runs', reviews_path=reviews, review_evidence_path=review_info, search_fn=search,
                               search_mode='synthetic_test', sku_evidence_path=specs)
            manifest = json.loads((out / 'manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['status'], 'completed', manifest['errors'])
            self.assertEqual(len(calls), 1)
            self.assertIn('sku_evidence.json', manifest['artifact_sha256'])
            match = json.loads((out / 'product_matches.json').read_text(encoding='utf-8'))[0]
            self.assertEqual(len(match['spec_checks']), 9)
            report = (out / 'REPORT.md').read_text(encoding='utf-8')
            for text in ['主图', 'synthetic-sku', 'candidate-sku', payload()['markdown'], '尺码', '面料']:
                self.assertIn(text, report)
            stdout = io.StringIO()
            with patch('sys.argv', ['clothscout', '--replay-run', str(out), '--output-root', str(root / 'replay')]), \
                 patch('product_sourcing.skill_adapter.src.client.subprocess.run', side_effect=AssertionError('Network forbidden')), \
                 contextlib.redirect_stdout(stdout):
                code = main()
            self.assertEqual(code, 0, stdout.getvalue())
            replay = Path(json.loads(stdout.getvalue())['output_directory'])
            again = json.loads((replay / 'product_matches.json').read_text(encoding='utf-8'))[0]
            self.assertEqual(match['checked_at'], again['checked_at'])
            self.assertEqual(match['spec_checks'], again['spec_checks'])

    def test_missing_image_remains_a_manual_task_and_does_not_search(self):
        with tempfile.TemporaryDirectory() as d:
            reviews = Path(d) / 'reviews.json'
            review_info = write_qualified(reviews, [review()], image_config())
            def fail(_):
                self.fail('Missing main image must not search')
            out = run_pipeline(image_config(), Path(d) / 'runs', reviews_path=reviews, review_evidence_path=review_info, search_fn=fail)
            manifest = json.loads((out / 'manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['counts']['search_calls'], 0)
            queue = json.loads((out / 'manual_review.json').read_text(encoding='utf-8'))
            self.assertEqual(queue['image_searches'][0]['status'], 'blocked')

    def test_failed_image_search_stops_other_queries_and_keeps_source(self):
        from runtime_support.provider_errors.src.errors import ProviderError
        with tempfile.TemporaryDirectory() as d:
            config = image_config()
            config['limits']['max_queries'] = 2
            rows = [review(productMainImage=IMAGE), review(productId='p2', reviewId='r2', productMainImage=IMAGE)]
            source = Path(d) / 'reviews.json'
            review_info = write_qualified(source, rows, config)
            rows = json.loads(source.read_text(encoding='utf-8'))
            calls = []
            def fail(plan):
                calls.append(plan)
                raise ProviderError('synthetic_failure')
            out = run_pipeline(config, Path(d) / 'runs', reviews_path=source, review_evidence_path=review_info, search_fn=fail)
            manifest = json.loads((out / 'manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(len(calls), 1)
            self.assertEqual(manifest['status'], 'partial')
            self.assertFalse(manifest['supply_absent'])
            self.assertEqual(json.loads((out / 'raw_reviews.json').read_text(encoding='utf-8')), rows)
