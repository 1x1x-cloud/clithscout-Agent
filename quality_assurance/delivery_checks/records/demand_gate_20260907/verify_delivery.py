"""Offline delivery verification; writes new snapshots, never overwrites source runs."""
import contextlib
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from workflow_execution.pipeline.src.orchestrator import run_pipeline
from workflow_execution.cli.src.main import main
from quality_assurance.regression.tests.test_demand_gate import sample

OUT = Path(__file__).parent


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cli(args):
    buffer = io.StringIO()
    with patch('sys.argv', ['clothscout', *args]), contextlib.redirect_stdout(buffer):
        code = main()
    assert code == 0, buffer.getvalue()
    return Path(json.loads(buffer.getvalue())['output_directory'])


def verify():
    baseline = read(OUT / 'baseline.json')
    checks = {}
    checks['protected_48_files_unchanged'] = all(sha(ROOT / p) == h for p, h in baseline['protected_files'].items())
    with zipfile.ZipFile(OUT / 'before_changes.zip') as archive:
        checks['baseline_backup_intact'] = all(hashlib.sha256(archive.read(p)).hexdigest() == h
                                               for p, h in baseline['backup_files'].items())
    output = io.StringIO()
    tests = unittest.TextTestRunner(stream=output, verbosity=2).run(
        unittest.defaultTestLoader.discover(str(ROOT / 'quality_assurance/regression/tests')))
    (OUT / 'tests.txt').write_text(output.getvalue(), encoding='utf-8')
    checks['regression_tests'] = tests.wasSuccessful()
    config = read(ROOT / 'workflow_execution/run_configuration/config/current_round.json')
    source = ROOT / config['local_review_file']
    # Every run below is local or saved-response replay. No network may open.
    with patch('socket.create_connection', side_effect=AssertionError('Delivery checks must remain offline')):
        fresh = run_pipeline(dict(config, search_strategy='image'), ROOT / 'workflow_execution/run_history/records', reviews_path=source)
        manifest = read(fresh / 'manifest.json')
        analysis = read(fresh / 'analysis.json')
        current = [s for s in analysis['problem_signals'] if s['scope'] == 'current']
        checks['real_sample_one_lead_no_card_no_query'] = (manifest['status'] == 'completed'
            and manifest['counts']['raw_rows'] == 16 and len(current) == 1
            and analysis['demand_cards'] == [] and read(fresh / 'search_plan.json') == []
            and manifest['counts']['search_calls'] == 0 and not (fresh / 'images').exists())
        checks['real_sample_unknown_ratio_and_buyers'] = (current[0]['prevalence']['problem_ratio'] is None
            and current[0]['prevalence']['independent_buyer_count'] is None)
        checks['real_raw_preserved'] = read(fresh / 'raw_reviews.json') == read(source)
        ev = {e['evidence_id']: e for e in analysis['evidence']}
        support = [ev[r] for r in current[0]['support_evidence_ids']]
        checks['real_original_text_and_sku_retained'] = (len(support) == 1
            and support[0]['review_id'] == '7679900019943687949'
            and support[0]['sku_id'] == '1732475515663127030'
            and support[0]['original_text'] == 'Ugly top and way too big. Returninh')

        replays = []
        for name in ('20260906T154237Z_38cd565c', '20260906T165943Z_fc9a7de8'):
            old = ROOT / 'workflow_execution/run_history/records' / name
            old_manifest = read(old / 'manifest.json')
            replay = cli(['--replay-run', str(old)])
            replays.append(str(replay.relative_to(ROOT)))
            checks[name + '_old_hashes_intact'] = all(sha(old / p) == h for p, h in old_manifest['artifact_sha256'].items())
            checks[name + '_analysis_and_plan_preserved'] = all(read(replay / p) == read(old / p)
                for p in ('analysis.json', 'demand_cards.json', 'search_plan.json'))
            records = [read(p) for p in (old / 'searches').glob('*.json')]
            checks[name + '_search_sources_and_times_preserved'] = all(
                all(read(replay / 'searches' / (r['plan']['query_id'] + '.json'))[k] == r[k]
                    for k in ('plan', 'payload', 'checked_at')) for r in records)
            checks[name + '_historical_banner'] = '历史分析回放' in (replay / 'REPORT.md').read_text(encoding='utf-8')

        synthetic = OUT / 'synthetic'
        synthetic.mkdir(exist_ok=True)
        rows, info = sample()
        for row in rows:
            row['productMainImage'] = 'https://example.invalid/synthetic-main.jpg'
        for name, data in [('reviews.json', rows), ('review_evidence.json', info),
                           ('config.json', dict(config, sample_kind='synthetic_example'))]:
            (synthetic / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        demo = cli(['--reviews', str(synthetic / 'reviews.json'), '--review-evidence', str(synthetic / 'review_evidence.json'),
                    '--config', str(synthetic / 'config.json'), '--image-search', '--output-root', str(synthetic / 'runs')])
        cards = read(demo / 'demand_cards.json')
        checks['qualified_cli_import'] = (len(cards) == 1 and cards[0]['prevalence']['approved'] is True
            and cards[0]['prevalence']['effective_sample_count'] == 5
            and cards[0]['prevalence']['independent_buyer_count'] == 3
            and cards[0]['prevalence']['problem_ratio'] == 0.6
            and len(read(demo / 'search_plan.json')) == 1
            and read(demo / 'manifest.json')['counts']['search_calls'] == 0)
        checks['synthetic_is_labelled'] = '合成测试示例' in (demo / 'REPORT.md').read_text(encoding='utf-8')

    docs = [ROOT / p for p in baseline['backup_files'] if p.endswith('.md')]
    docs.append(ROOT / 'project_governance/business_rules/docs/2026-09-07-review-evidence.md')
    missing = []
    for doc in docs:
        for link in re.findall(r'\]\(([^)]+)\)', doc.read_text(encoding='utf-8')):
            if not link.startswith(('http:', 'https:', '#')) and not (doc.parent / link).exists():
                missing.append({'document': str(doc.relative_to(ROOT)), 'link': link})
    checks['changed_doc_links_resolve'] = not missing
    result = {'checked_at': datetime.now(timezone.utc).isoformat(), 'passed': all(checks.values()),
        'checks': checks, 'functional_tests': tests.testsRun, 'test_failures': len(tests.failures), 'test_errors': len(tests.errors),
        'fresh_real_run': str(fresh.relative_to(ROOT)), 'historical_replays': replays,
        'synthetic_cli_run': str(demo.relative_to(ROOT)), 'missing_links': missing,
        'limits': 'Offline code and snapshot verification only. Imported coverage and buyer identities require authentic source evidence; no new Actor, live 1688, supplier messages or purchasing.'}
    (OUT / 'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(verify())
