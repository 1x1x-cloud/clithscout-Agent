"""One-shot, non-destructive migration into the explicitly authorized directory."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import zipfile

SOURCE = Path(__file__).resolve().parents[1]
SKILL = Path('C:/Users/86130/.codex/skills/1688-product-find')
PREFIX = 'tiktok_us_data_acceptance_2026-09-05'
MIG = 'project_governance/migration'
MAP = {}
CREATED = []


def sha(data):
    return hashlib.sha256(data).hexdigest()


def emit(relative, text):
    path = TARGET / relative
    if path.exists():
        raise RuntimeError('Refusing to overwrite: ' + relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + '\n', encoding='utf-8')
    CREATED.append(relative)
    return path


def source_text(name):
    return (SOURCE / 'clothing_agent' / name).read_text(encoding='utf-8-sig')


def select(name, names):
    text = source_text(name)
    lines = text.splitlines(keepends=True)
    selected = []
    for node in ast.parse(text).body:
        found = getattr(node, 'name', None)
        if isinstance(node, ast.Assign):
            found = getattr(node.targets[0], 'id', None)
        if found in names:
            selected.append(''.join(lines[node.lineno - 1:node.end_lineno]))
    if len(selected) != len(names):
        raise RuntimeError('Source definition set changed: ' + name + str(names))
    return '\n\n'.join(selected)


def module(relative, imports, body):
    emit(relative, '"""ClothScout module; migrated without changing business thresholds."""\n' + imports + '\n\n' + body)


def copy_to(source, relative):
    destination = TARGET / relative
    if destination.exists():
        raise RuntimeError('Destination collision: ' + relative)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    MAP[str(source.resolve())] = relative


def choose_destination(path):
    relative = path.relative_to(SOURCE).as_posix()
    if relative.startswith('clothing_agent/runs/'):
        return relative.replace('clothing_agent/runs/', 'workflow_execution/run_history/records/', 1)
    if relative.startswith('clothing_agent/verification/'):
        return relative.replace('clothing_agent/verification/', 'quality_assurance/delivery_checks/records/legacy/', 1)
    if relative.startswith(PREFIX + '/'):
        tail = relative[len(PREFIX) + 1:]
        routing = {
            'apify_api_connection_2026-09-06/': 'data_acquisition/apify_reviews/records/',
            'category_601152_2026-09-06/': 'data_acquisition/tiktok_catalog/records/',
            'fastmoss_visible_2026-09-06/': 'data_acquisition/fastmoss_catalog/records/',
            'four_platform_trends_2026-09-06/': 'data_acquisition/social_trends/records/',
            'non_browser_options_2026-09-06/': 'data_acquisition/provider_research/records/',
            'pilot_7d_1688_2026-09-06/': 'product_sourcing/manual_pilot/records/',
            'pinterest_keyword_trends_2026-09-06/': 'data_acquisition/pinterest_keywords/records/',
            'pinterest_sweater_jeans_2026-09-06/': 'data_acquisition/pinterest_saves/records/',
            'real_sample_demo_2026-09-06/': 'demand_discovery/historical_examples/records/',
            'shop_negative_reviews_2026-09-06/': 'data_acquisition/shop_reviews/records/',
        }
        for old, new in routing.items():
            if tail.startswith(old):
                return new + tail[len(old):]
        exact = {'TASK_STATE.md': 'project_governance/project_state/docs/TASK_STATE.md',
                 'field_dictionary.csv': 'project_governance/business_rules/schemas/field_dictionary.csv'}
        return exact.get(tail, 'quality_assurance/source_acceptance/records/' + tail)
    if relative.startswith('docs/superpowers/specs/'):
        return 'project_governance/business_rules/docs/' + path.name
    if relative.startswith('docs/superpowers/plans/'):
        return 'project_governance/implementation_history/docs/' + path.name
    return None  # Original source remains byte-exact inside the recovery ZIP.


def split_code():
    module('runtime_support/time_windows/src/clock.py', 'from datetime import datetime, timezone', select('analysis.py', ['utc']))
    module('runtime_support/text_identity/src/identity.py', 'import hashlib, json, re', select('analysis.py', ['digest', 'normalized']))
    module('runtime_support/provider_errors/src/errors.py', '', select('providers.py', ['ProviderError']))
    module('workflow_execution/run_configuration/src/validation.py', 'from runtime_support.time_windows.src.clock import utc', select('analysis.py', ['validate_config']))
    module('demand_discovery/pain_classification/src/rules.py', '', select('analysis.py', ['RULES', 'ISSUES']))
    module('demand_discovery/pain_classification/src/classifier.py', 'import re\nfrom runtime_support.text_identity.src.identity import normalized\nfrom demand_discovery.pain_classification.src.rules import RULES', select('analysis.py', ['classify']))
    module('evidence_processing/garment_context/src/classifier.py', 'import re', select('analysis.py', ['garment']))
    original = select('analysis.py', ['analyze'])
    front, rest = original.split('    groups = defaultdict(list)', 1)
    signature_start = front.index('    signatures = defaultdict(set)')
    signature_end = front.index('    evidence, seen_ids = [], {}')
    signature_body = front[signature_start:signature_end]
    module('evidence_processing/review_deduplication/src/grouping.py', 'from collections import defaultdict\nfrom runtime_support.text_identity.src.identity import digest',
           'def review_signatures(rows):\n' + signature_body + '    return signatures\n')
    front = front[:signature_start] + '    signatures = review_signatures(rows)\n' + front[signature_end:]
    front = front.replace('def analyze(rows, config):', 'def normalize_reviews(rows, config):', 1)
    module('evidence_processing/review_normalization/src/normalizer.py',
           'from workflow_execution.run_configuration.src.validation import validate_config\nfrom runtime_support.time_windows.src.clock import utc\nfrom runtime_support.text_identity.src.identity import digest, normalized\nfrom evidence_processing.review_deduplication.src.grouping import review_signatures\nfrom evidence_processing.garment_context.src.classifier import garment\nfrom demand_discovery.pain_classification.src.classifier import classify', front + '    return evidence\n')
    cards_body, return_body = ('    groups = defaultdict(list)' + rest).split('    return {"evidence": evidence', 1)
    module('demand_discovery/demand_cards/src/builder.py', 'from collections import defaultdict\nfrom runtime_support.text_identity.src.identity import digest\nfrom demand_discovery.pain_classification.src.rules import ISSUES',
           'def build_cards(evidence, config):\n' + cards_body + '    return cards\n')
    module('demand_discovery/analysis_workflow/src/analyze.py', 'from collections import Counter\nfrom evidence_processing.review_normalization.src.normalizer import normalize_reviews\nfrom demand_discovery.demand_cards.src.builder import build_cards',
           'def analyze(rows, config):\n    evidence = normalize_reviews(rows, config)\n    cards = build_cards(evidence, config)\n    return {"evidence": evidence' + return_body)
    module('data_acquisition/apify_reviews/src/client.py', 'import hashlib, json, re\nimport urllib.error, urllib.parse, urllib.request\nfrom runtime_support.provider_errors.src.errors import ProviderError', select('providers.py', ['valid_id', 'NoRedirect', 'ApifyReader', 'fetch_reviews']))
    module('product_sourcing/result_parsing/src/parser.py', 'from runtime_support.provider_errors.src.errors import ProviderError', select('providers.py', ['parse_search']))
    module('product_sourcing/skill_adapter/src/client.py', 'import json, os, subprocess, sys\nfrom pathlib import Path\nfrom runtime_support.provider_errors.src.errors import ProviderError', select('providers.py', ['search_1688']))
    module('product_sourcing/query_planning/src/planner.py', 'import re\nfrom runtime_support.text_identity.src.identity import digest', select('matching.py', ['CATEGORIES', 'plan_searches']))
    module('product_matching/sku_comparison/src/comparison.py', 'from evidence_processing.garment_context.src.classifier import garment', select('matching.py', ['compare_product']))
    module('runtime_support/json_storage/src/storage.py', 'import json\nfrom datetime import datetime, timezone', select('pipeline.py', ['now', 'write_json', 'load_json']))
    module('quality_assurance/record_validation/src/validator.py', 'from runtime_support.json_storage.src.storage import now', select('pipeline.py', ['validate_run']))
    module('report_delivery/markdown_report/src/render.py', '', select('pipeline.py', ['cell', 'render_report']))
    pipeline = select('pipeline.py', ['run_pipeline'])
    pipeline = pipeline.replace('p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob("*.py")',
                                'str(p.relative_to(PROJECT_ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in active_source_files()')
    queue_start = pipeline.index('        searched_ids = ')
    queue_end = pipeline.index('        write_json(out / "manual_review.json", queue)')
    queue = pipeline[queue_start:queue_end]
    queue = '\n'.join(line[4:] for line in queue.splitlines())
    module('human_review/review_queue/src/builder.py', '', 'def build_review_queue(analysis, matches, searches):\n' + queue + '\n    return queue\n')
    pipeline = pipeline[:queue_start] + '        queue = build_review_queue(analysis, matches, searches)\n' + pipeline[queue_end:]
    imports = '''from datetime import datetime, timezone
import hashlib
from pathlib import Path
from uuid import uuid4
from runtime_support.project_paths.src.paths import PROJECT_ROOT, active_source_files
from runtime_support.json_storage.src.storage import now, write_json, load_json
from runtime_support.provider_errors.src.errors import ProviderError
from workflow_execution.run_configuration.src.validation import validate_config
from demand_discovery.analysis_workflow.src.analyze import analyze
from data_acquisition.apify_reviews.src.client import fetch_reviews
from product_sourcing.query_planning.src.planner import plan_searches
from product_sourcing.result_parsing.src.parser import parse_search
from product_matching.sku_comparison.src.comparison import compare_product
from quality_assurance.record_validation.src.validator import validate_run
from human_review.review_queue.src.builder import build_review_queue
from report_delivery.markdown_report.src.render import render_report
__version__ = '0.1.0-migrated'
'''
    module('workflow_execution/pipeline/src/orchestrator.py', imports, pipeline)


def entrypoints():
    emit('runtime_support/project_paths/src/paths.py', '''from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_FILE = PROJECT_ROOT / 'workflow_execution/run_configuration/config/current_round.json'
RUNS = PROJECT_ROOT / 'workflow_execution/run_history/records'
TESTS = PROJECT_ROOT / 'quality_assurance/regression/tests'

def project_path(value):
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path

def active_source_files():
    return sorted(p for p in PROJECT_ROOT.glob('*/*/src/*.py') if p.is_file())
''')
    main = source_text('__main__.py')
    main = main.replace('from .pipeline import load_json, run_pipeline', 'from runtime_support.json_storage.src.storage import load_json\nfrom workflow_execution.pipeline.src.orchestrator import run_pipeline\nfrom runtime_support.project_paths.src.paths import PROJECT_ROOT, CONFIG_FILE, RUNS, project_path')
    main = main.replace('from .providers import ProviderError, search_1688', 'from runtime_support.provider_errors.src.errors import ProviderError\nfrom product_sourcing.skill_adapter.src.client import search_1688')
    main = main.replace('str(Path(__file__).parent / "config/current_round.json")', 'str(CONFIG_FILE)')
    main = main.replace('Path(__file__).parent / "runs"', 'RUNS')
    main = main.replace('Path(__file__).resolve().parent.parent', 'PROJECT_ROOT')
    main = main.replace('config["1688_cli"])', 'project_path(config["1688_cli"]))')
    emit('workflow_execution/cli/src/main.py', main)
    emit('workflow_execution/launcher/scripts/launch.py', '''import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
if __name__ == '__main__':
    if '--test' in sys.argv:
        from quality_assurance.regression.src.runner import main
    elif '--verify-migration' in sys.argv:
        from quality_assurance.migration_validation.src.verify import main
    else:
        from workflow_execution.cli.src.main import main
    raise SystemExit(main())
''')
    emit('workflow_execution/launcher/scripts/run.ps1', '''param([switch]$Live, [string]$Reviews, [string]$ReplayRun, [switch]$Test, [switch]$VerifyMigration)
$ErrorActionPreference = 'Stop'
$projectRoot = (Get-Item -LiteralPath $PSScriptRoot).Parent.Parent.Parent.FullName
$pythonExe = Join-Path $projectRoot 'runtime_support/python_environment/venv/Scripts/python.exe'
$launchScript = Join-Path $projectRoot 'workflow_execution/launcher/scripts/launch.py'
if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Project Python environment is missing; see START_HERE.md.' }
if (($Live -and ($Reviews -or $ReplayRun)) -or ($Reviews -and $ReplayRun)) { throw 'Choose a single input mode.' }
$agentArgs = @('-B', $launchScript)
if ($Live) { $agentArgs += @('--live-read', '--live-search') }
if ($Reviews) { $agentArgs += @('--reviews', $Reviews) }
if ($ReplayRun) { $agentArgs += @('--replay-run', $ReplayRun) }
if ($Test) { $agentArgs += '--test' }
if ($VerifyMigration) { $agentArgs += '--verify-migration' }
$env:PYTHONIOENCODING = 'utf-8'
Push-Location -LiteralPath $projectRoot
try { & $pythonExe @agentArgs; $agentExit = $LASTEXITCODE } finally { Pop-Location }
exit $agentExit
''')
    config = json.loads(source_text('config/current_round.json'))
    config['local_review_file'] = 'data_acquisition/shop_reviews/records/user_run_20260906_144758/raw_reviews.json'
    config['1688_cli'] = 'product_sourcing/1688_skill/vendor/1688-product-find/cli.py'
    config['configuration_basis'] = 'project_governance/project_state/docs/TASK_STATE.md; preserved historical window'
    emit('workflow_execution/run_configuration/config/current_round.json', json.dumps(config, ensure_ascii=False, indent=2))
    tests = source_text('tests/test_pipeline.py')
    tests = tests.replace('from clothing_agent.analysis import analyze, validate_config', 'from demand_discovery.analysis_workflow.src.analyze import analyze\nfrom workflow_execution.run_configuration.src.validation import validate_config')
    tests = tests.replace('from clothing_agent.matching import compare_product, plan_searches', 'from product_matching.sku_comparison.src.comparison import compare_product\nfrom product_sourcing.query_planning.src.planner import plan_searches')
    tests = tests.replace('from clothing_agent.providers import ProviderError, fetch_reviews, parse_search', 'from runtime_support.provider_errors.src.errors import ProviderError\nfrom data_acquisition.apify_reviews.src.client import fetch_reviews\nfrom product_sourcing.result_parsing.src.parser import parse_search')
    tests = tests.replace('from clothing_agent.pipeline import run_pipeline', 'from workflow_execution.pipeline.src.orchestrator import run_pipeline')
    tests = tests.replace('from clothing_agent.__main__ import main', 'from workflow_execution.cli.src.main import main')
    emit('quality_assurance/regression/tests/test_pipeline.py', tests)
    emit('quality_assurance/regression/src/runner.py', '''import unittest
from runtime_support.project_paths.src.paths import TESTS
def main():
    suite = unittest.defaultTestLoader.discover(str(TESTS))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1
''')


def rewrite_markdown():
    # Run snapshots and vendor code stay byte-exact; mapped human docs get valid local links.
    for original, relative in MAP.items():
        if not relative.endswith('.md') or relative.startswith(('workflow_execution/run_history/', 'product_sourcing/1688_skill/')):
            continue
        old, new = Path(original), TARGET / relative
        content = new.read_text(encoding='utf-8-sig')
        def replace(match):
            target = match.group(1)
            if target.startswith(('https:', 'http:', '#', 'app:')):
                return match.group(0)
            resolved = str((old.parent / target).resolve())
            if resolved in MAP:
                import os
                mapped = os.path.relpath(TARGET / MAP[resolved], new.parent).replace('\\', '/')
                return '](' + mapped + ')'
            return match.group(0)
        content = re.sub(r'\]\(([^)]+)\)', replace, content)
        new.write_text(content, encoding='utf-8')


def main():
    if TARGET != Path('D:/clothscout').resolve() or TARGET == SOURCE or SOURCE in TARGET.parents:
        raise RuntimeError('Unexpected migration target')
    if TARGET.exists() and (TARGET.is_symlink() or any(TARGET.iterdir())):
        raise RuntimeError('Target must be an empty real directory; nothing overwritten')
    TARGET.mkdir(parents=True, exist_ok=True)
    sources = [SOURCE / 'CONTINUE_CLOTHING_AGENT.md']
    for directory in ('clothing_agent', PREFIX, 'docs/superpowers'):
        sources.extend(p for p in (SOURCE / directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    backup = TARGET / MIG / 'backup/original_project.zip'
    backup.parent.mkdir(parents=True, exist_ok=True)
    inventory = []
    with zipfile.ZipFile(backup, 'x', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(sources):
            relative = path.relative_to(SOURCE).as_posix()
            raw = path.read_bytes()
            archive.writestr(relative, raw)
            destination = choose_destination(path)
            if destination:
                copy_to(path, destination)
            inventory.append({'source': str(path), 'archive_member': relative, 'source_sha256': sha(raw),
                              'bytes': len(raw), 'destination': destination,
                              'preservation': 'mapped_file_and_recovery_archive' if destination else 'recovery_archive_original_and_modular_replacement'})
    for path in SKILL.rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
            copy_to(path, 'product_sourcing/1688_skill/vendor/1688-product-find/' + path.relative_to(SKILL).as_posix())
    split_code()
    entrypoints()
    rewrite_markdown()
    emit(MIG + '/plans/PLAN.md', (SOURCE / 'migration_2026-09-07/PLAN.md').read_text(encoding='utf-8'))
    emit(MIG + '/src/migrate.py', Path(__file__).read_text(encoding='utf-8'))
    emit('runtime_support/python_environment/config/requirements.txt', 'requests==2.33.0\nkeyring==25.7.0\nPillow==11.2.1')
    record = {'created_at': datetime.now(timezone.utc).isoformat(), 'source_root': str(SOURCE), 'target_root': str(TARGET),
              'archive': str(backup.relative_to(TARGET)).replace('\\', '/'), 'archive_sha256': sha(backup.read_bytes()),
              'source_files': inventory, 'original_sources_deleted': False,
              'source_to_destination': MAP, 'generated_files': CREATED,
              'excluded_and_retained_in_source': ['paimon_model', 'selection-agent-website (separate onboarding website)', '.selection-site-npm-cache', '.git (shared repository)', '.venv-1688-pilot (environment rebuilt)', 'optix7cache.db'],
              'credential_migration': 'No credential export; reuse same Windows user keyring and existing 1688 credential store'}
    emit(MIG + '/records/migration_manifest.json', json.dumps(record, ensure_ascii=False, indent=2))
    print(json.dumps({'target': str(TARGET), 'original_files_archived': len(inventory), 'mapped_files': len(MAP), 'generated_files': len(CREATED)}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', required=True)
    TARGET = Path(parser.parse_args().target).resolve()
    main()
