"""Audit final document pointers and original-file retention without rerunning analysis."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil

root = Path('D:/clothscout')
manifest = json.loads((root / 'project_governance/migration/records/migration_manifest.json').read_text(encoding='utf-8'))
updated = {r['source']: r['after_sha256'] for r in manifest['source_pointer_updates']}
errors = []
for item in manifest['source_files']:
    expected = updated.get(item['archive_member'], item['source_sha256'])
    file = Path(item['source'])
    if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != expected:
        errors.append('original_retention:' + item['archive_member'])
docs = [root / p for p in ['project_governance/project_state/docs/TASK_STATE.md',
                           'project_governance/user_guide/docs/START_HERE.md',
                           'project_governance/workspace_registry/docs/MODULE_INDEX.md',
                           'project_governance/migration/docs/COMPLETION.md']]
docs.extend(Path(manifest['source_root']) / name for name in updated)
links = 0
for file in docs:
    for target in re.findall(r'\]\(([^)]+)\)', file.read_text(encoding='utf-8')):
        if target.startswith(('http:', 'https:', '#')):
            continue
        links += 1
        if not (file.parent / target).exists():
            errors.append('broken_link:' + str(file) + '->' + target)
registry = json.loads((root / 'project_governance/workspace_registry/config/modules.json').read_text(encoding='utf-8'))
if {p.name for p in root.iterdir()} != {m['core_module'] for m in registry}:
    errors.append('root_structure_changed')
for module in registry:
    if set(module['submodules']) != {p.name for p in (root / module['core_module']).iterdir() if p.is_dir()}:
        errors.append('submodule_structure_changed:' + module['core_module'])
verification = json.loads((root / manifest['verification_record']).read_text(encoding='utf-8'))
assert verification['passed']
shutil.copyfile(Path(__file__), root / 'project_governance/migration/src/final_audit.py')
report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'passed': not errors,
          'original_files_retained': len(manifest['source_files']), 'unchanged_original_files': len(manifest['source_files']) - len(updated),
          'backed_up_documents_replaced_with_pointers': len(updated), 'checked_document_links': links,
          'core_modules': len(registry), 'submodules': sum(len(m['submodules']) for m in registry),
          'functional_verification': manifest['verification_record'], 'errors': errors}
out = root / 'quality_assurance/migration_validation/records/final_audit.json'
out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
raise SystemExit(0 if report['passed'] else 1)
