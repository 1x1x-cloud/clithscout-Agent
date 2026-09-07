"""Store a token received through stdin in the current user's Windows vault."""
import sys, keyring

secret = sys.stdin.read().strip()
if not secret or any(ord(c) < 33 or ord(c) > 126 for c in secret):
    print("Token must be nonempty text without spaces or control characters.")
    raise SystemExit(2)
if secret.startswith(("https://", "http://", "Bearer ", "bearer ")) or secret in ("APIFY_TOKEN", "APIFY_API_TOKEN"):
    print("Paste only the API token, not a URL, header or variable name.")
    raise SystemExit(2)
backend = keyring.get_keyring()
if type(backend).__module__ != "keyring.backends.Windows":
    print("Windows Credential Manager backend is required.")
    raise SystemExit(3)
try:
    keyring.set_password("clothing-agent-apify", "APIFY_TOKEN", secret)
    print("SAVED")
except Exception:
    print("Could not save to Windows Credential Manager.")
    raise SystemExit(4)
finally:
    secret = None

