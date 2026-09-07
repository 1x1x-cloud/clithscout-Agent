"""Self-contained migration acceptance; all evidence comes from this project."""
from contextlib import redirect_stdout
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from runtime_support.project_paths.src.paths import PROJECT_ROOT, CONFIG_FILE, TESTS
from workflow_execution.cli.src.main import main as cli_main


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    root = PROJECT_ROOT
    out = root / 'quality_assurance/migration_validation/records' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out.mkdir(parents=True, exist_ok=False)
    manifest = read(root / 'project_governance/migration/records/migration_manifest.json')
    errors, checks = [], {}
    archive_path = root / manifest['archive']
    checks['archive_hash'] = sha(archive_path.read_bytes()) == manifest['archive_sha256']
    with zipfile.ZipFile(archive_path) as archive:
        checks['all_original_files_preserved'] = set(archive.namelist()) == {item['archive_member'] for item in manifest['source_files']}
        for item in manifest['source_files']:
            data = archive.read(item['archive_member'])
            if len(data) != item['bytes'] or sha(data) != item['source_sha256']:
                errors.append('backup_mismatch:' + item['archive_member'])
            if item['destination']:
                dest = root / item['destination']
                if not dest.exists():
                    errors.append('missing_mapped_file:' + item['destination'])
                elif dest.suffix != '.md' and sha(dest.read_bytes()) != item['source_sha256']:
                    errors.append('changed_original_record:' + item['destination'])
            else:
                replacement = manifest['modular_replacements'].get(item['archive_member'], [])
                if not replacement or any(not (root / name).exists() for name in replacement):
                    errors.append('missing_modular_replacement:' + item['archive_member'])
    for item in manifest.get('vendor_files', []):
        if sha((root / item['destination']).read_bytes()) != item['sha256']:
            errors.append('vendor_copy_changed:' + item['destination'])
    checks['vendor_inventory_present'] = bool(manifest.get('vendor_files'))
    registry = read(root / 'project_governance/workspace_registry/config/modules.json')
    actual_cores = {p.name for p in root.iterdir() if p.is_dir()}
    checks['root_contains_only_core_directories'] = not any(p.is_file() for p in root.iterdir()) and actual_cores == {m['core_module'] for m in registry}
    checks['core_levels_have_only_submodule_directories'] = all(all(p.is_dir() for p in (root / m['core_module']).iterdir()) for m in registry)
    checks['submodule_registry_matches'] = all(set(m['submodules']) == {p.name for p in (root / m['core_module']).iterdir() if p.is_dir()} for m in registry)
    config = read(CONFIG_FILE)
    checks['active_paths_are_project_relative_and_exist'] = all(not Path(config[key]).is_absolute() and (root / config[key]).is_file() for key in ('local_review_file', '1688_cli'))
    stream = io.StringIO()
    tests = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.discover(str(TESTS)))
    (out / 'tests.txt').write_text(stream.getvalue(), encoding='utf-8')
    checks['regression_tests'] = tests.wasSuccessful()
    live = root / 'workflow_execution/run_history/records/20260906T154237Z_38cd565c'
    for folder in [p for p in live.parent.iterdir() if p.is_dir() and p.name.startswith('20260906T15')]:
        old_manifest = read(folder / 'manifest.json')
        for name, expected in old_manifest['artifact_sha256'].items():
            if sha((folder / name).read_bytes()) != expected:
                errors.append('historical_run_hash_mismatch:' + folder.name + '/' + name)
    old_cwd = Path.cwd()
    runs = []
    with tempfile.TemporaryDirectory() as outside:
        try:
            os.chdir(outside)
            for options in ([], ['--replay-run', str(live)]):
                output = io.StringIO()
                with patch('sys.argv', ['clothscout', *options]), redirect_stdout(output):
                    code = cli_main()
                result = json.loads(output.getvalue())
                if code or result['status'] != 'completed':
                    errors.append('new_project_execution_failed')
                runs.append(Path(result['output_directory']))
        finally:
            os.chdir(old_cwd)
    source_reviews = read(root / config['local_review_file'])
    checks['reviews_preserved_in_both_modes'] = all(read(p / 'raw_reviews.json') == source_reviews for p in runs)
    checks['demand_cards_unchanged'] = all(read(p / 'demand_cards.json') == read(live / 'demand_cards.json') for p in runs)
    replay_matches = read(runs[-1] / 'product_matches.json')
    prior_matches = read(live / 'product_matches.json')
    checks['matching_decisions_unchanged'] = [{k: m[k] for k in m if k != 'source_mode'} for m in replay_matches] == [{k: m[k] for k in m if k != 'source_mode'} for m in prior_matches]
    checks['procurement_candidates_unchanged'] = all(not m['eligible_for_test'] and m['verified_stock'] is None for m in replay_matches)
    imported = [m for name, m in sys.modules.items() if name.split('.')[0] in actual_cores and getattr(m, '__file__', None)]
    checks['active_imports_from_new_root'] = all(root in Path(m.__file__).resolve().parents for m in imported)
    missing_links = []
    for relative in ['project_governance/project_state/docs/TASK_STATE.md', 'project_governance/user_guide/docs/START_HERE.md', 'project_governance/workspace_registry/docs/MODULE_INDEX.md']:
        file = root / relative
        for link in re.findall(r'\]\(([^)]+)\)', file.read_text(encoding='utf-8')):
            if link.startswith(('http:', 'https:', '#')):
                continue
            if not (file.parent / link).exists():
                missing_links.append({'file': relative, 'link': link})
    checks['current_entry_links_resolve'] = not missing_links
    errors.extend('failed_check:' + key for key, passed in checks.items() if not passed)
    result = {'checked_at': datetime.now(timezone.utc).isoformat(), 'passed': not errors, 'checks': checks,
              'original_files': len(manifest['source_files']), 'vendor_files': len(manifest.get('vendor_files', [])),
              'core_modules': len(registry), 'submodules': sum(len(m['submodules']) for m in registry),
              'functional_tests': tests.testsRun, 'test_failures': len(tests.failures), 'test_errors': len(tests.errors),
              'runs': [str(p.relative_to(root)) for p in runs], 'missing_links': missing_links, 'errors': errors,
              'limits': 'Offline migration and snapshot checks; no new collection, sourcing, inventory or semantic accuracy validation.'}
    (out / 'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'output_directory': str(out), **result}, ensure_ascii=False, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
