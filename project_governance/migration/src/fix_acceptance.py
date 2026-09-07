"""Apply two bounded migration fixes to the user-selected destination."""
from pathlib import Path
import shutil

root = Path('D:/clothscout').resolve()
assert root == Path('D:/clothscout') and root.is_dir()
cli = root / 'workflow_execution/cli/src/main.py'
old = '''if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ProviderError, ValueError, OSError, KeyError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc) if isinstance(exc, ProviderError) else type(exc).__name__}))
        sys.exit(1)
'''
new = '''def entrypoint():
    """Keep the same redacted failure contract for every command-line launcher."""
    try:
        return main()
    except (ProviderError, ValueError, OSError, KeyError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc) if isinstance(exc, ProviderError) else type(exc).__name__}))
        return 1


if __name__ == "__main__":
    sys.exit(entrypoint())
'''
text = cli.read_text(encoding='utf-8')
assert old in text
cli.write_text(text.replace(old, new), encoding='utf-8')
launcher = root / 'workflow_execution/launcher/scripts/launch.py'
text = launcher.read_text(encoding='utf-8')
old_import = 'from workflow_execution.cli.src.main import main'
assert old_import in text
launcher.write_text(text.replace(old_import, 'from workflow_execution.cli.src.main import entrypoint as main'), encoding='utf-8')
shutil.copyfile(Path(__file__).with_name('verify.py'), root / 'quality_assurance/migration_validation/src/verify.py')
shutil.copyfile(Path(__file__).with_name('test_entrypoint.py'), root / 'quality_assurance/regression/tests/test_entrypoint.py')
print('CLI error contract and Windows acceptance cleanup fixed; regression cases installed.')
