import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
if __name__ == '__main__':
    if '--test' in sys.argv:
        from quality_assurance.regression.src.runner import main
    elif '--verify-migration' in sys.argv:
        from quality_assurance.migration_validation.src.verify import main
    else:
        from workflow_execution.cli.src.main import entrypoint as main
    raise SystemExit(main())
