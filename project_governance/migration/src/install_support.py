from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys

ROOT = Path('D:/clothscout').resolve()
STAGE = Path(__file__).resolve().parent
if ROOT != Path('D:/clothscout').resolve() or not (ROOT / 'project_governance/migration/records/migration_manifest.json').exists():
    raise RuntimeError('Unexpected target')
target = ROOT / 'quality_assurance/migration_validation/src/verify.py'
target.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(STAGE / 'verify.py', target)
subprocess.run([sys.executable, '-B', str(STAGE / 'finalize.py')], check=True)
record_path = ROOT / 'project_governance/migration/records/migration_manifest.json'
record = json.loads(record_path.read_text(encoding='utf-8'))
record['vendor_files'] = []
for original, destination in record['source_to_destination'].items():
    if destination.startswith('product_sourcing/1688_skill/vendor/'):
        data = Path(original).read_bytes()
        if data != (ROOT / destination).read_bytes():
            raise RuntimeError('Vendor copy mismatch')
        record['vendor_files'].append({'destination': destination, 'sha256': hashlib.sha256(data).hexdigest()})
record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
print('Migration support files installed')
