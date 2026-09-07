"""Prepare traceable JPEG inputs before search; replay never fetches images."""
import copy
import hashlib
import http.client
import io
import ipaddress
import json
from pathlib import Path
import re
import socket
import ssl
import time
from urllib.parse import urljoin, urlsplit
import warnings

from PIL import Image, ImageOps

from product_sourcing.query_planning.src.image_planner import valid_image_url
from runtime_support.json_storage.src.storage import now, write_json
from runtime_support.provider_errors.src.errors import ProviderError

MAX_BYTES = 5 * 1024 * 1024
MAX_PIXELS = 20_000_000
MAX_SIZE = (800, 800)


def _open_response(url, timeout):
    """Pin the connection to a checked public address; TLS uses the URL host."""
    if not valid_image_url(url):
        raise ProviderError('source_image_invalid_url')
    parts = urlsplit(url)
    host = parts.hostname
    port = parts.port or (443 if parts.scheme == 'https' else 80)
    addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(row[4][0]).is_global for row in addresses):
        raise ProviderError('source_image_non_public_address')
    conn = http.client.HTTPConnection(host, port, timeout=timeout)
    try:
        conn.sock = socket.create_connection((addresses[0][4][0], port), timeout=timeout)
        if parts.scheme == 'https':
            conn.sock = ssl.create_default_context().wrap_socket(conn.sock, server_hostname=host)
        target = parts.path or '/'
        if parts.query:
            target += '?' + parts.query
        # No browser cookies, proxy credentials, automatic redirects or retries.
        conn.request('GET', target, headers={'Accept': 'image/*', 'Accept-Encoding': 'identity',
                                            'User-Agent': 'ClothScout/0.2', 'Connection': 'close'})
        return conn, conn.getresponse()
    except Exception:
        conn.close()
        raise


def download_image(url):
    deadline = time.monotonic() + 30
    current = url
    try:
        for hop in range(4):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ProviderError('source_image_download_timeout')
            conn, response = _open_response(current, min(10, remaining))
            try:
                if response.status in (301, 302, 303, 307, 308):
                    location = response.getheader('Location')
                    if not location or hop == 3:
                        raise ProviderError('source_image_redirect_limit')
                    target = urljoin(current, location)
                    if urlsplit(current).scheme == 'https' and urlsplit(target).scheme != 'https':
                        raise ProviderError('source_image_insecure_redirect')
                    current = target
                    continue  # Each new destination is validated before connecting.
                if response.status != 200:
                    raise ProviderError('source_image_http_' + str(response.status))
                length = response.getheader('Content-Length')
                if length is not None and (int(length) < 0 or int(length) > MAX_BYTES):
                    raise ProviderError('source_image_too_large')
                content = bytearray()
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise ProviderError('source_image_download_timeout')
                    if conn.sock is not None:
                        conn.sock.settimeout(min(10, remaining))
                    chunk = response.read1(65536)
                    if not chunk:
                        break
                    content.extend(chunk)
                    if len(content) > MAX_BYTES:
                        raise ProviderError('source_image_too_large')
                if not content or (length is not None and len(content) != int(length)):
                    raise ProviderError('source_image_incomplete_download')
                return bytes(content), current, response.getheader('Content-Type')
            finally:
                response.close()
                conn.close()
    except ProviderError:
        raise
    except (OSError, ValueError, http.client.HTTPException):
        raise ProviderError('source_image_download_failed') from None


def _file_info(path, root, content):
    return {'file': path.relative_to(root).as_posix(), 'sha256': hashlib.sha256(content).hexdigest(),
            'bytes': len(content)}


def prepare_image(url, run_dir, query_id):
    if not valid_image_url(url) or not re.fullmatch(r'QI-[A-Za-z0-9_-]+', query_id):
        raise ProviderError('source_image_invalid_plan')
    root = Path(run_dir).resolve()
    directory = (root / 'images' / query_id).resolve()
    if root not in directory.parents:
        raise ProviderError('source_image_archive_path_invalid')
    directory.mkdir(parents=True, exist_ok=False)
    receipt = directory / 'metadata.json'
    info = {'method': 'download_jpeg_v1', 'source_url': url, 'archive_root': str(root),
            'metadata_file': receipt.relative_to(root).as_posix(), 'status': 'preparing'}
    try:
        content, final_url, content_type = download_image(url)
        if len(content) > MAX_BYTES:
            raise ProviderError('source_image_too_large')
        original = directory / 'source.bin'
        original.write_bytes(content)
        info.update(downloaded_at=now(), final_url=final_url, content_type=content_type,
                    original=_file_info(original, root, content))
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content)) as image:
                if image.width * image.height > MAX_PIXELS:
                    raise ProviderError('source_image_pixel_limit')
                if getattr(image, 'n_frames', 1) != 1:
                    raise ProviderError('source_image_animated_not_supported')
                info['original'].update(format=image.format, dimensions=list(image.size))
                image.load()
                converted = ImageOps.exif_transpose(image)
                if 'A' in converted.getbands() or 'transparency' in converted.info:
                    rgba = converted.convert('RGBA')
                    converted = Image.new('RGB', rgba.size, 'white')
                    converted.paste(rgba, mask=rgba.getchannel('A'))
                else:
                    converted = converted.convert('RGB')
                converted.thumbnail(MAX_SIZE, Image.Resampling.LANCZOS)
                output = io.BytesIO()
                converted.save(output, format='JPEG', quality=90)
                jpeg_bytes = output.getvalue()
                if len(jpeg_bytes) > MAX_BYTES:
                    raise ProviderError('source_image_jpeg_too_large')
                jpeg = directory / 'input.jpg'
                jpeg.write_bytes(jpeg_bytes)
                info['jpeg'] = dict(_file_info(jpeg, root, jpeg_bytes), format='JPEG',
                                    dimensions=list(converted.size), quality=90)
                info.update(cli_image_path=str(jpeg), status='ready')
        return info
    except ProviderError as exc:
        info.update(status='failed', error=str(exc))
        raise
    except (OSError, ValueError, Image.DecompressionBombWarning, Image.DecompressionBombError):
        info.update(status='failed', error='source_image_decode_or_archive_failed')
        raise ProviderError(info['error']) from None
    finally:
        write_json(receipt, info)


def _archived_path(root, name):
    if not isinstance(name, str) or Path(name).is_absolute():
        raise ProviderError('source_image_archive_path_invalid')
    root = Path(root).resolve()
    path = (root / name).resolve()
    if root not in path.parents:
        raise ProviderError('source_image_archive_path_invalid')
    return path


def verified_jpeg(info, source_url):
    try:
        if not info or info['status'] != 'ready' or info['source_url'] != source_url:
            raise ProviderError('source_image_not_prepared')
        path = _archived_path(info['archive_root'], info['jpeg']['file'])
        if str(path) != info['cli_image_path'] or hashlib.sha256(path.read_bytes()).hexdigest() != info['jpeg']['sha256']:
            raise ProviderError('source_image_integrity_failed')
        with Image.open(path) as image:
            if image.format != 'JPEG' or image.width > 800 or image.height > 800:
                raise ProviderError('source_image_not_prepared')
            image.verify()
        return str(path)
    except (KeyError, TypeError, ValueError, OSError):
        raise ProviderError('source_image_not_prepared') from None


def copy_image_input(info, source_run, target_run):
    """Copy verified bytes by relative path; keep the historical CLI echo intact."""
    try:
        for kind in ('original', 'jpeg'):
            entry = info[kind]
            content = _archived_path(source_run, entry['file']).read_bytes()
            if hashlib.sha256(content).hexdigest() != entry['sha256']:
                raise ProviderError('replay_image_integrity_failed')
            target = _archived_path(target_run, entry['file'])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        receipt = _archived_path(source_run, info['metadata_file']).read_bytes()
        if json.loads(receipt) != info:
            raise ProviderError('replay_image_metadata_mismatch')
        _archived_path(target_run, info['metadata_file']).write_bytes(receipt)
        return copy.deepcopy(info)
    except (KeyError, TypeError, ValueError, OSError):
        raise ProviderError('replay_image_integrity_failed') from None
