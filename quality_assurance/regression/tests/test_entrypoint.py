"""Migration acceptance for actual launcher failures and redacted error output."""
from contextlib import redirect_stdout
import io
import json
import subprocess
import sys
import unittest
from unittest.mock import patch

from runtime_support.project_paths.src.paths import PROJECT_ROOT
from workflow_execution.cli.src.main import entrypoint


class EntrypointCases(unittest.TestCase):
    def test_missing_config_is_json_failure_without_traceback(self):
        completed = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / 'workflow_execution/launcher/scripts/launch.py'),
             '--config', str(PROJECT_ROOT / 'quality_assurance/regression/tests/missing-config.json')],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(json.loads(completed.stdout), {'status': 'failed', 'error': 'FileNotFoundError'})
        self.assertEqual(completed.stderr, '')

    def test_value_error_does_not_expose_input_or_credentials(self):
        output = io.StringIO()
        with patch('workflow_execution.cli.src.main.main', side_effect=ValueError('SYNTHETIC_SECRET_VALUE')), redirect_stdout(output):
            code = entrypoint()
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(output.getvalue()), {'status': 'failed', 'error': 'ValueError'})
        self.assertNotIn('SYNTHETIC_SECRET_VALUE', output.getvalue())
