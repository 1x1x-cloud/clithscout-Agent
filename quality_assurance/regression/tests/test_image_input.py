"""Image input regression checks; network boundaries use synthetic responses."""
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from unittest.mock import MagicMock

from PIL import Image
from product_sourcing.skill_adapter.src.client import search_1688
from runtime_support.project_paths.src.paths import PROJECT_ROOT
from runtime_support.provider_errors.src.errors import ProviderError
from quality_assurance.regression.tests.test_image_sku import IMAGE, image_config, payload
from quality_assurance.regression.tests.test_pipeline import review
from quality_assurance.regression.fixtures.qualified_reviews import write_qualified
from workflow_execution.pipeline.src.orchestrator import run_pipeline
from workflow_execution.cli.src.main import main

CLI = PROJECT_ROOT / 'product_sourcing/1688_skill/vendor/1688-product-find/cli.py'


def pixels(fmt='WEBP', mode='RGB', size=(1200, 600)):
    buffer = io.BytesIO()
    Image.new(mode, size).save(buffer, format=fmt)
    return buffer.getvalue()


class DefaultImageInputCases(unittest.TestCase):
    def test_adapter_refuses_unprepared_url_before_starting_cli(self):
        plan = dict(search_type='image', image=IMAGE, limit=3, status='ready')
        with patch('product_sourcing.skill_adapter.src.client.subprocess.run', return_value=subprocess.CompletedProcess([], 0, json.dumps(payload()), '')) as execute:
            with self.assertRaises(ProviderError):
                search_1688(plan, CLI)
            execute.assert_not_called()

    def test_prepared_webp_is_jpeg_resized_and_original_bytes_preserved(self):
        from product_sourcing.skill_adapter.src.image_input import prepare_image, verified_jpeg
        content = pixels()
        with tempfile.TemporaryDirectory() as folder, patch('product_sourcing.skill_adapter.src.image_input.download_image', return_value=(content, IMAGE, 'image/webp')):
            root = Path(folder)
            info = prepare_image(IMAGE, root, 'QI-fixture')
            self.assertEqual((root / info['original']['file']).read_bytes(), content)
            self.assertEqual(info['source_url'], IMAGE)
            self.assertEqual(info['original']['sha256'], hashlib.sha256(content).hexdigest())
            with Image.open(verified_jpeg(info, IMAGE)) as img:
                self.assertEqual((img.format, img.mode, img.size), ('JPEG', 'RGB', (800, 400)))
            self.assertIn('downloaded_at', info)

    def test_transparency_becomes_white_and_tampering_is_rejected(self):
        from product_sourcing.skill_adapter.src.image_input import prepare_image, verified_jpeg
        with tempfile.TemporaryDirectory() as folder, patch('product_sourcing.skill_adapter.src.image_input.download_image', return_value=(pixels('PNG', 'RGBA', (2, 2)), IMAGE, 'image/png')):
            info = prepare_image(IMAGE, Path(folder), 'QI-fixture')
            path = Path(verified_jpeg(info, IMAGE))
            with Image.open(path) as img:
                self.assertEqual(img.getpixel((0, 0)), (255, 255, 255))
            with self.assertRaises(ProviderError):
                verified_jpeg(info, 'https://example.invalid/other.jpg')
            path.write_bytes(b'changed')
            with self.assertRaises(ProviderError):
                verified_jpeg(info, IMAGE)

    def test_png_transparent_color_is_composited_for_rgb_and_grayscale(self):
        from product_sourcing.skill_adapter.src.image_input import prepare_image, verified_jpeg
        for mode, transparency in [('RGB', (0, 0, 0)), ('L', 0)]:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as folder:
                content = io.BytesIO()
                Image.new(mode, (2, 2), 0).save(content, format='PNG', transparency=transparency)
                with patch('product_sourcing.skill_adapter.src.image_input.download_image', return_value=(content.getvalue(), IMAGE, 'image/png')):
                    info = prepare_image(IMAGE, Path(folder), 'QI-transparent')
                with Image.open(verified_jpeg(info, IMAGE)) as image:
                    self.assertEqual(image.getpixel((0, 0)), (255, 255, 255))

    def test_bad_image_stops_before_search_and_keeps_failure_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'reviews.json'
            review_info = write_qualified(source, [review(productMainImage=IMAGE)], image_config())
            with patch('product_sourcing.skill_adapter.src.image_input.download_image', return_value=(b'<html>not an image</html>', IMAGE, 'text/html')), patch('product_sourcing.skill_adapter.src.client.subprocess.run') as execute:
                out = run_pipeline(image_config(), root / 'runs', reviews_path=source, review_evidence_path=review_info,
                                   search_fn=lambda p: search_1688(p, CLI), search_mode='live')
            manifest = json.loads((out / 'manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['status'], 'partial')
            self.assertEqual(manifest['counts']['search_calls'], 0)
            self.assertFalse(manifest['supply_absent'])
            self.assertTrue(list((out / 'images').glob('*/metadata.json')))
            execute.assert_not_called()

    def test_default_live_pipeline_uploads_jpeg_and_replays_after_run_is_moved(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'reviews.json'
            review_info = write_qualified(source, [review(productMainImage=IMAGE)], image_config())
            commands = []
            def execute(command, **kwargs):
                commands.append(command)
                path = Path(command[command.index('--image') + 1])
                self.assertTrue(path.is_absolute())
                self.assertEqual(path.suffix, '.jpg')
                with Image.open(path) as img:
                    self.assertEqual(img.format, 'JPEG')
                response = payload()
                response['data']['data']['source_image'] = str(path)
                return subprocess.CompletedProcess(command, 0, json.dumps(response), '')
            with patch('product_sourcing.skill_adapter.src.image_input.download_image', return_value=(pixels(), IMAGE, 'image/webp')), patch('product_sourcing.skill_adapter.src.client.subprocess.run', side_effect=execute):
                out = run_pipeline(image_config(), root / 'runs', reviews_path=source, review_evidence_path=review_info,
                                   search_fn=lambda p: search_1688(p, CLI), search_mode='live')
            self.assertEqual(len(commands), 1)
            manifest = json.loads((out / 'manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['status'], 'completed', manifest['errors'])
            self.assertEqual(manifest['counts']['product_matches'], 1)
            record = json.loads(next((out / 'searches').glob('*.json')).read_text(encoding='utf-8'))
            self.assertEqual(record['plan']['image'], IMAGE)
            self.assertNotIn('image_input', record['plan'])
            # Move only this test's verified temporary run, preserving old CLI path.
            moved = root / 'moved-run'
            out.rename(moved)
            stdout = io.StringIO()
            with patch('product_sourcing.skill_adapter.src.image_input.download_image', side_effect=AssertionError('replay downloaded')), patch('product_sourcing.skill_adapter.src.client.subprocess.run', side_effect=AssertionError('replay searched')), patch('sys.argv', ['clothscout', '--replay-run', str(moved), '--output-root', str(root / 'replays')]), contextlib.redirect_stdout(stdout):
                self.assertEqual(main(), 0)
            replay = Path(json.loads(stdout.getvalue())['output_directory'])
            replay_record = json.loads(next((replay / 'searches').glob('*.json')).read_text(encoding='utf-8'))
            self.assertEqual(replay_record['checked_at'], record['checked_at'])
            self.assertEqual(replay_record['payload'], record['payload'])
            self.assertEqual(replay_record['image_input'], record['image_input'])
            for kind in ('original', 'jpeg'):
                name = record['image_input'][kind]['file']
                self.assertEqual((replay / name).read_bytes(), (moved / name).read_bytes())
            self.assertIn('JPEG', (replay / 'REPORT.md').read_text(encoding='utf-8'))

    def test_offline_plan_does_not_prepare_images(self):
        with tempfile.TemporaryDirectory() as folder, patch('product_sourcing.skill_adapter.src.image_input.download_image', side_effect=AssertionError('offline download')):
            source = Path(folder) / 'reviews.json'
            review_info = write_qualified(source, [review(productMainImage=IMAGE)], image_config())
            out = run_pipeline(image_config(), Path(folder) / 'runs', reviews_path=source, review_evidence_path=review_info)
            self.assertFalse((out / 'images').exists())
            self.assertEqual(json.loads((out / 'manifest.json').read_text())['counts']['search_calls'], 0)

    def test_query_limit_still_bounds_downloads_and_searches(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'reviews.json'
            review_info = write_qualified(source, [review(productMainImage=IMAGE), review(productId='other', reviewId='other-review', productMainImage=IMAGE)], image_config())
            def search(plan):
                result = payload()
                result['data']['data']['source_image'] = plan['image_input']['cli_image_path']
                return result
            with patch('product_sourcing.skill_adapter.src.image_input.download_image', return_value=(pixels(), IMAGE, 'image/webp')) as fetch:
                out = run_pipeline(image_config(), Path(folder) / 'runs', reviews_path=source, review_evidence_path=review_info, search_fn=search, search_mode='live')
            self.assertEqual(fetch.call_count, 1)
            self.assertEqual(len(list((out / 'searches').glob('*.json'))), 1)
            self.assertEqual(json.loads((out / 'manifest.json').read_text())['counts']['search_calls'], 1)


class DownloadBoundaryCases(unittest.TestCase):
    def response(self, body=b'picture', headers=None, status=200):
        response = MagicMock(status=status)
        response.getheader.side_effect = lambda key: (headers or {}).get(key)
        response.read1.side_effect = [body, b'']
        return MagicMock(), response

    def test_dns_to_private_address_never_opens_a_socket(self):
        from product_sourcing.skill_adapter.src.image_input import _open_response
        with patch('socket.getaddrinfo', return_value=[(2, 1, 6, '', ('127.0.0.1', 443))]), patch('socket.create_connection') as connect:
            with self.assertRaisesRegex(ProviderError, 'non_public'):
                _open_response(IMAGE, 5)
            connect.assert_not_called()

    def test_tls_connects_to_validated_ip_and_verifies_original_hostname(self):
        from product_sourcing.skill_adapter.src.image_input import _open_response
        with patch('socket.getaddrinfo', return_value=[(2, 1, 6, '', ('1.1.1.1', 443))]), patch('socket.create_connection') as connect, patch('ssl.create_default_context') as tls, patch('http.client.HTTPConnection') as http:
            conn, response = _open_response(IMAGE, 5)
            connect.assert_called_once_with(('1.1.1.1', 443), timeout=5)
            tls.return_value.wrap_socket.assert_called_once_with(connect.return_value, server_hostname='example.invalid')
            self.assertIs(conn, http.return_value)

    def test_redirect_to_private_host_is_blocked_before_second_request(self):
        from product_sourcing.skill_adapter.src.image_input import download_image, _open_response
        conn, response = self.response(headers={'Location': 'https://127.0.0.1/private'}, status=302)
        with patch('product_sourcing.skill_adapter.src.image_input._open_response', side_effect=[(conn, response), ProviderError('source_image_invalid_url')]) as opened:
            with self.assertRaises(ProviderError):
                download_image(IMAGE)
            self.assertEqual(opened.call_args.args[0], 'https://127.0.0.1/private')
        with patch('socket.create_connection') as connect:
            with self.assertRaises(ProviderError):
                _open_response('https://127.0.0.1/private', 5)
            connect.assert_not_called()

    def test_oversized_stream_is_rejected_even_without_content_length(self):
        from product_sourcing.skill_adapter.src.image_input import download_image
        conn, response = self.response(body=b'x' * 9)
        with patch('product_sourcing.skill_adapter.src.image_input.MAX_BYTES', 8), patch('product_sourcing.skill_adapter.src.image_input._open_response', return_value=(conn, response)):
            with self.assertRaisesRegex(ProviderError, 'too_large'):
                download_image(IMAGE)
        response.close.assert_called_once()

    def test_http_failure_is_not_retried(self):
        from product_sourcing.skill_adapter.src.image_input import download_image
        conn, response = self.response(status=503)
        with patch('product_sourcing.skill_adapter.src.image_input._open_response', return_value=(conn, response)) as opened:
            with self.assertRaisesRegex(ProviderError, 'http_503'):
                download_image(IMAGE)
            self.assertEqual(opened.call_count, 1)

    def test_pixel_limit_fails_before_loading_image(self):
        from product_sourcing.skill_adapter.src.image_input import prepare_image
        with tempfile.TemporaryDirectory() as folder, patch('product_sourcing.skill_adapter.src.image_input.MAX_PIXELS', 1), patch('product_sourcing.skill_adapter.src.image_input.download_image', return_value=(pixels(size=(2, 2)), IMAGE, 'image/webp')):
            with self.assertRaisesRegex(ProviderError, 'pixel_limit'):
                prepare_image(IMAGE, Path(folder), 'QI-limit')


if __name__ == '__main__':
    unittest.main()
