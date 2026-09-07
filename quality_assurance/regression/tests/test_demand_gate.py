"""User-approved prevalence boundaries; all fixtures are synthetic."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from demand_discovery.analysis_workflow.src.analyze import analyze
from workflow_execution.pipeline.src.orchestrator import run_pipeline
from quality_assurance.regression.tests.test_pipeline import CONFIG, review


def sample(total=5, supporters=3):
    texts = ['Top is too big', '这件上衣偏大', 'This top runs large']
    rows = [review(texts[i % 3] + (' ' + str(i) if i >= 3 else ''),
                   reviewId='r' + str(i), productTitle='Knit top', skuId='sku' + str(i))
            for i in range(supporters)]
    rows += [review('Fits perfectly' if i == supporters else 'Detailed positive fit feedback ' + str(i),
                    reviewId='r' + str(i), rating=5, productTitle='Knit top')
             for i in range(supporters, total)]
    source = dict(source_ref='https://example.invalid/complete-synthetic-export', checked_at='2026-09-07T00:00:00Z')
    info = {'schema_version': 1, 'samples': [dict(product_id='synthetic-product', market='US',
        window=copy.deepcopy(CONFIG['window']), rating_scope='all', complete=True,
        review_ids=[r['reviewId'] for r in rows], **source)],
        'reviews': [dict(product_id=r['productId'], review_id=r['reviewId'], substantive=True,
            buyer_id='buyer' + str(i), buyer_identity_verified=True, **source) for i, r in enumerate(rows)]}
    return rows, info


class PrevalenceCases(unittest.TestCase):
    def evaluate(self, total=5, supporters=3):
        rows, info = sample(total, supporters)
        return analyze(rows, CONFIG, review_evidence=info)

    def test_one_and_two_feedbacks_are_signals_only(self):
        for count in (1, 2):
            result = self.evaluate(count, count)
            self.assertEqual(result['demand_cards'], [])
            self.assertEqual(len(result['problem_signals']), 1)
            self.assertFalse(result['problem_signals'][0]['sourcing_eligible'])

    def test_all_three_gates_pass_and_preserve_skus(self):
        result = self.evaluate()
        card = result['demand_cards'][0]
        stats = card['prevalence']
        self.assertEqual((stats['effective_sample_count'], stats['independent_buyer_count'], stats['problem_ratio']), (5, 3, 0.6))
        self.assertEqual(len(card['support_evidence_ids']), 3)
        self.assertTrue(card['sourcing_eligible'])
        self.assertEqual({e['sku_id'] for e in result['evidence'][:3]}, {'sku0','sku1','sku2'})
        self.assertIn('sample_below_recommended_10', stats['warnings'])

    def test_and_boundary_not_or(self):
        self.assertEqual(len(self.evaluate(15)['demand_cards']), 1)
        for total, supporters in [(16, 3), (4, 3), (10, 2)]:
            self.assertEqual(self.evaluate(total, supporters)['demand_cards'], [])

    def test_low_star_only_missing_or_mismatched_coverage_stays_unknown(self):
        rows, info = sample()
        for bad in [None, dict(info, samples=[]), dict(info, samples=[dict(info['samples'][0], rating_scope='one_star')]),
                    dict(info, samples=[dict(info['samples'][0], review_ids=['r0'])])]:
            result = analyze(rows, CONFIG, review_evidence=bad)
            self.assertEqual(result['demand_cards'], [])
            self.assertIsNone(result['problem_signals'][0]['prevalence']['problem_ratio'])

    def test_different_text_is_not_buyer_identity(self):
        rows, info = sample()
        for r in info['reviews']: r.pop('buyer_id')
        result = analyze(rows, CONFIG, review_evidence=info)
        self.assertEqual(result['demand_cards'], [])
        self.assertIsNone(result['problem_signals'][0]['prevalence']['independent_buyer_count'])

    def test_same_buyer_text_and_thread_do_not_inflate_support(self):
        for mode in ('buyer', 'text', 'thread', 'suspect', 'repost'):
            rows, info = sample()
            if mode == 'buyer': info['reviews'][1]['buyer_id'] = info['reviews'][0]['buyer_id']
            if mode == 'text': rows[1]['content'] = rows[0]['content']
            if mode == 'thread':
                for r in info['reviews'][:2]: r['thread_id'] = 'one-thread'
            if mode == 'suspect': info['reviews'][0]['suspected_reused_account'] = True
            if mode == 'repost': info['reviews'][0]['is_repost'] = True
            result = analyze(rows, CONFIG, review_evidence=info)
            self.assertEqual(result['demand_cards'], [], mode)

    def test_unknown_scope_must_not_silently_lower_denominator(self):
        for change in ({'timestamp': None}, {'authorCountry': None}):
            rows, info = sample()
            rows.append(review('Substantive review without confirmed scope', reviewId='unknown', **change))
            result = analyze(rows, CONFIG, review_evidence=info)
            self.assertEqual(result['demand_cards'], [])
            self.assertIsNone(result['problem_signals'][0]['prevalence']['problem_ratio'])

    def test_audited_pure_praise_still_cannot_complete_sample(self):
        for text in ('Great product!', 'Love these pants!', 'Beautiful top', '很好看'):
            rows, info = sample()
            rows[3]['content'] = text
            result = analyze(rows, CONFIG, review_evidence=info)
            self.assertEqual(result['demand_cards'], [], text)

    def test_invalid_annotation_and_masked_buyer_fail_closed(self):
        for change in ({'buyer_id': 'a***b'}, {'buyer_identity_verified': False}):
            rows, info = sample()
            info['reviews'][0].update(change)
            result = analyze(rows, CONFIG, review_evidence=info)
            self.assertEqual(result['demand_cards'], [])
        for change in ({'substantive': 'true'}, {'source_ref': ''}, {'review_id': 'unmatched'}):
            rows, info = sample()
            info['reviews'][0].update(change)
            with self.assertRaises(ValueError):
                analyze(rows, CONFIG, review_evidence=info)

    def test_praise_empty_and_unresolved_substance_do_not_shrink_denominator_silently(self):
        rows, info = sample()
        rows[3]['content'] = 'Love it!'
        rows[4]['content'] = ''
        result = analyze(rows, CONFIG, review_evidence=info)
        self.assertEqual(result['problem_signals'][0]['prevalence']['effective_sample_count'], 3)
        self.assertEqual(result['demand_cards'], [])
        rows, info = sample()
        info['reviews'] = info['reviews'][:3]
        result = analyze(rows, CONFIG, review_evidence=info)
        self.assertEqual(result['demand_cards'], [])
        self.assertIsNone(result['problem_signals'][0]['prevalence']['problem_ratio'])

    def test_no_evidence_single_review_never_downloads_or_searches(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'reviews.json'; path.write_text(json.dumps([review(productMainImage='https://example.invalid/main.jpg')]))
            with patch('workflow_execution.pipeline.src.orchestrator.prepare_image', side_effect=AssertionError('download')):
                out=run_pipeline(dict(CONFIG, search_strategy='image'), Path(folder)/'runs', reviews_path=path,
                    search_fn=lambda p: self.fail('unqualified signal searched'), search_mode='live')
            self.assertEqual(json.loads((out/'demand_cards.json').read_text(encoding='utf-8')), [])
            self.assertEqual(len(json.loads((out/'problem_signals.json').read_text(encoding='utf-8'))),1)
            self.assertEqual(json.loads((out/'manifest.json').read_text(encoding='utf-8'))['counts']['search_calls'],0)

    def test_sourcing_planners_refuse_legacy_cards_and_unqualified_signals(self):
        from product_sourcing.query_planning.src.planner import plan_searches
        from product_sourcing.query_planning.src.image_planner import plan_image_searches
        from demand_discovery.demand_cards.src.builder import _group_candidates
        result = analyze([review(productMainImage='https://example.invalid/main.jpg')], CONFIG)
        legacy_cards = _group_candidates(result['evidence'], CONFIG)
        for cards in (legacy_cards, result['problem_signals']):
            self.assertEqual(plan_searches(cards, CONFIG, result['evidence']), [])
            self.assertEqual(plan_image_searches(cards, result['evidence'], CONFIG), [])

    def test_structural_errors_cannot_turn_18_75_percent_into_20_percent(self):
        from product_sourcing.query_planning.src.planner import plan_searches
        for mode in ('id_conflict', 'invalid_content_type', 'failed_empty_payload'):
            rows, info = sample(16, 3)
            if mode == 'id_conflict':
                rows.append(dict(rows[-1], content='Conflicting positive feedback'))
            elif mode == 'invalid_content_type':
                rows[-1]['content'] = {'invalid': 'body'}
            else:
                rows[-1].update(content='', status='Failed')
            result = analyze(rows, CONFIG, review_evidence=info)
            with self.subTest(mode=mode):
                self.assertEqual(result['demand_cards'], [])
                self.assertIsNone(result['problem_signals'][0]['prevalence']['problem_ratio'])
                self.assertTrue(result['problem_signals'][0]['prevalence']['unresolved_evidence_ids'])
                self.assertEqual(plan_searches(result['demand_cards'], CONFIG), [])


if __name__ == '__main__': unittest.main()
