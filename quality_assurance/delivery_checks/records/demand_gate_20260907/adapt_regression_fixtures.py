"""One-time, scoped migration of downstream test setup to qualified synthetic cohorts."""
from pathlib import Path

root = Path('quality_assurance/regression/tests')
p = root / 'test_pipeline.py'
s = p.read_text(encoding='utf-8')
s = s.replace('from workflow_execution.cli.src.main import main', 'from workflow_execution.cli.src.main import main\nfrom quality_assurance.regression.fixtures.qualified_reviews import qualified_analysis, write_qualified')
s = s.replace('card = result["demand_cards"][0]', 'card = result["problem_signals"][0]')
s = s.replace('result["demand_cards"][0]["distinct_text_signals"]', 'result["problem_signals"][0]["distinct_text_signals"]')
s = s.replace('result["demand_cards"][0]["counter_evidence_ids"]', 'result["problem_signals"][0]["counter_evidence_ids"]')
s = s.replace('[c["scope"] for c in result["demand_cards"]]', '[c["scope"] for c in result["problem_signals"]]')
s = s.replace('len(plan_searches(result["demand_cards"], CONFIG)), 1', 'len(plan_searches(result["demand_cards"], CONFIG)), 0')
s = s.replace('card = analyze([review(', 'card = qualified_analysis([review(')
s = s.replace('result = analyze([review(productId="p1"', 'result = qualified_analysis([review(productId="p1"')
s = s.replace('source.write_text(json.dumps([review()]), encoding="utf-8")', 'review_info = write_qualified(source, [review()], CONFIG)')
s = s.replace('reviews_path=source, search_fn=fail)', 'reviews_path=source, search_fn=fail, review_evidence_path=review_info)')
s = s.replace('source.write_text(json.dumps([review()]))\n            out = run_pipeline(CONFIG, Path(d)', 'review_info = write_qualified(source, [review()], CONFIG)\n            out = run_pipeline(CONFIG, Path(d)')
s = s.replace('search_fn=lambda _: {"success": False, "markdown": None})', 'search_fn=lambda _: {"success": False, "markdown": None}, review_evidence_path=review_info)')
# Extraction assertions must test the lead too; an empty card list alone no longer proves no pain.
s = s.replace('analyze([review(text)], CONFIG)["demand_cards"], []', 'analyze([review(text)], CONFIG)["problem_signals"], []')
p.write_text(s, encoding='utf-8')

p = root / 'test_image_sku.py'
s = p.read_text(encoding='utf-8')
s = s.replace('from quality_assurance.regression.tests.test_pipeline import CONFIG, review', 'from quality_assurance.regression.tests.test_pipeline import CONFIG, review\nfrom quality_assurance.regression.fixtures.qualified_reviews import qualified_analysis, write_qualified, expanded_targets')
s = s.replace('return analyze(rows or', 'return qualified_analysis(rows or')
s = s.replace("self.assertEqual(len(plan['evidence_ids']), 2)", "self.assertGreaterEqual(len(plan['evidence_ids']), 2)")
s = s.replace('validate_spec_evidence(data)\n        return inspect_product', 'data = expanded_targets(data)\n        validate_spec_evidence(data)\n        return inspect_product')
s = s.replace("review(reviewId='other-review', skuId='other-size'", "review('My pants are too long around the legs', reviewId='other-review', skuId='other-size'")
s = s.replace("self.assertEqual(len(result['spec_checks']), 6)", "self.assertEqual(len(result['spec_checks']), 18)")
s = s.replace("self.assertEqual(len(match['spec_checks']), 3)", "self.assertEqual(len(match['spec_checks']), 9)")
s = s.replace("source.write_text(json.dumps([review(productMainImage=IMAGE)]), encoding='utf-8')", "review_info = write_qualified(source, [review(productMainImage=IMAGE)], image_config())")
s = s.replace("reviews.write_text(json.dumps([review(productMainImage=IMAGE)]), encoding='utf-8')", "review_info = write_qualified(reviews, [review(productMainImage=IMAGE)], image_config())")
s = s.replace('reviews.write_text(json.dumps([review()]))', 'review_info = write_qualified(reviews, [review()], image_config())')
s = s.replace('source.write_text(json.dumps(rows))', "review_info = write_qualified(source, rows, config)\n            rows = json.loads(source.read_text(encoding='utf-8'))")
s = s.replace("specs.write_text(json.dumps(dossier()),", "specs.write_text(json.dumps(expanded_targets(dossier())),")
s = s.replace('reviews_path=source,', 'reviews_path=source, review_evidence_path=review_info,')
s = s.replace('reviews_path=reviews,', 'reviews_path=reviews, review_evidence_path=review_info,')
p.write_text(s, encoding='utf-8')

p = root / 'test_image_input.py'
s = p.read_text(encoding='utf-8')
s = s.replace('from quality_assurance.regression.tests.test_pipeline import review', 'from quality_assurance.regression.tests.test_pipeline import review\nfrom quality_assurance.regression.fixtures.qualified_reviews import write_qualified')
s = s.replace('source.write_text(json.dumps([review(productMainImage=IMAGE)]))', 'review_info = write_qualified(source, [review(productMainImage=IMAGE)], image_config())')
s = s.replace("source.write_text(json.dumps([review(productMainImage=IMAGE), review(productId='other', reviewId='other-review', productMainImage=IMAGE)]))", "review_info = write_qualified(source, [review(productMainImage=IMAGE), review(productId='other', reviewId='other-review', productMainImage=IMAGE)], image_config())")
s = s.replace('reviews_path=source,', 'reviews_path=source, review_evidence_path=review_info,')
s = s.replace('reviews_path=source)', 'reviews_path=source, review_evidence_path=review_info)')
p.write_text(s, encoding='utf-8')
