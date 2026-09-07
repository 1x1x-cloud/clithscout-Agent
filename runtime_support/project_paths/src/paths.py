from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_FILE = PROJECT_ROOT / 'workflow_execution/run_configuration/config/current_round.json'
RUNS = PROJECT_ROOT / 'workflow_execution/run_history/records'
TESTS = PROJECT_ROOT / 'quality_assurance/regression/tests'

def project_path(value):
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path

def active_source_files():
    return sorted(p for p in PROJECT_ROOT.glob('*/*/src/*.py') if p.is_file())
