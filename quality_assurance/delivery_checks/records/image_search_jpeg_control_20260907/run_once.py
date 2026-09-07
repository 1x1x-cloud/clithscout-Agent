"""Run the explicitly approved JPEG control through the vendor CLI once.

Records the search response body, never authentication headers. A persisted
attempt marker and an in-process guard prevent repeat search requests.
"""
import base64
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import sys
from datetime import datetime, timezone

import requests

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
IMAGE = ROOT / 'quality_assurance/delivery_checks/records/image_search_diagnosis_20260907/jpeg_input.jpg'
CLI = ROOT / 'product_sourcing/1688_skill/vendor/1688-product-find/cli.py'
EXPECTED_HASH = 'fb0cdee3aee5533dac14baa6fd76a485a945eaba8d5ccfd70f5d83cbf0653de6'
ENDPOINT = 'https://skills-gateway.1688.com/api/find_product/1.0.0'


def now():
    return datetime.now(timezone.utc).isoformat()


def save(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    assert hashlib.sha256(IMAGE.read_bytes()).hexdigest() == EXPECTED_HASH
    assert CLI.is_file()
    if (OUT / 'search_attempt.json').exists():
        raise RuntimeError('Recorded attempt exists; this script must not run a second search.')
    arguments = ['image_search', '--image', str(IMAGE), '--limit', '3',
                 '--score-level', 'high', '--purchase-amount', '1', '--tags', '4306497']
    manifest = {'started_at': now(), 'authorization': 'User approved one additional same-image JPEG control query.',
                'cli': str(CLI), 'arguments': arguments, 'image_sha256': EXPECTED_HASH,
                'search_http_attempts': 0, 'automatic_search_retry_allowed': False}
    save('manifest.json', manifest)
    original_post = requests.post

    def recorded_post(url, *args, **kwargs):
        if url != ENDPOINT:
            return original_post(url, *args, **kwargs)
        if manifest['search_http_attempts']:
            raise RuntimeError('Diagnostic one-request cap reached; automatic retry stopped.')
        body = json.loads(kwargs['data'])
        image_bytes = base64.b64decode(body['imgBase64'], validate=True)
        assert hashlib.sha256(image_bytes).hexdigest() == EXPECTED_HASH
        assert body['imageUrl'] is None
        assert {key: body[key] for key in ('pageSize', 'scoreLevel', 'purchaseAmount', 'tags')} == {
            'pageSize': 3, 'scoreLevel': 'high', 'purchaseAmount': 1, 'tags': '4306497'}
        safe_request = {key: value for key, value in body.items() if key != 'imgBase64'}
        safe_request.update(image_bytes=len(image_bytes), image_sha256=EXPECTED_HASH)
        with (OUT / 'search_attempt.json').open('x', encoding='utf-8') as handle:
            json.dump({'at': now(), 'endpoint': url, 'request_without_image_base64': safe_request}, handle, indent=2)
        manifest['search_http_attempts'] = 1
        save('manifest.json', manifest)
        response = original_post(url, *args, **kwargs)
        (OUT / 'gateway_response.json').write_bytes(response.content)
        save('http_metadata.json', {'received_at': now(), 'status_code': response.status_code,
                                   'content_type': response.headers.get('Content-Type'),
                                   'response_sha256': hashlib.sha256(response.content).hexdigest()})
        return response

    requests.post = recorded_post
    sys.argv = [str(CLI), *arguments]
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    output = io.StringIO()
    errors = io.StringIO()
    exit_code = 0
    try:
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            try:
                runpy.run_path(str(CLI), run_name='__main__')
            except SystemExit as exc:
                exit_code = exc.code or 0
    except Exception as exc:
        exit_code = 1
        manifest['runner_error_type'] = type(exc).__name__
    finally:
        requests.post = original_post
        (OUT / 'cli_stdout.json').write_text(output.getvalue(), encoding='utf-8')
        manifest.update(finished_at=now(), exit_code=exit_code,
                        stderr_captured_but_not_saved=bool(errors.getvalue()))
        save('manifest.json', manifest)
    try:
        payload = json.loads(output.getvalue())
        print(json.dumps(payload, ensure_ascii=False))
    except json.JSONDecodeError:
        print(json.dumps({'runner_status': 'CLI output unavailable; inspect manifest.',
                          'search_http_attempts': manifest['search_http_attempts']}))


if __name__ == '__main__':
    main()
