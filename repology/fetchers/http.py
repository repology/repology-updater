# Copyright (C) 2016-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
#
# This file is part of repology
#
# repology is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# repology is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with repology.  If not, see <http://www.gnu.org/licenses/>.

import bz2
import contextlib
import functools
import gzip
import lzma
import tempfile
import time
from json import dumps
from typing import Any, AnyStr, Callable, IO, cast

import brotli

import requests

import zstandard

from repology.config import config

USER_AGENT = 'repology-fetcher/0 (+{}/docs/bots)'.format(config['REPOLOGY_HOME'])
STREAM_CHUNK_SIZE = 10240


class PoliteHTTP:
    def __init__(self, timeout: int = 5, delay: int | None = None):
        self.do_http = functools.partial(do_http, timeout=timeout)
        self.delay = delay
        self.had_requests = False

    def __call__(self, *args: Any, **kwargs: Any) -> requests.Response:
        if self.had_requests and self.delay:
            time.sleep(self.delay)

        self.had_requests = True
        return self.do_http(*args, **kwargs)


def do_http(url: str,
            method: str | None = None,
            check_status: bool = True,
            timeout: int | None = 5,
            data: str | bytes | None = None,
            json: Any = None,
            post: str | bytes | None = None,  # XXX: compatibility shim
            headers: dict[str, str] | None = None,
            stream: bool = False) -> requests.Response:
    headers = headers.copy() if headers else {}
    headers['User-Agent'] = USER_AGENT

    if post and not data:
        data = post
    if json and not data:
        data = dumps(json)

    request: Callable[..., requests.Response] = requests.get

    if method == 'POST' or (method is None and data):
        request = requests.post
    elif method == 'DELETE':
        request = requests.delete
    elif method == 'PUT':
        request = requests.put

    response = request(url, headers=headers, timeout=timeout, data=data, stream=stream)

    if check_status:
        response.raise_for_status()

    return response


class NotModifiedException(requests.RequestException):
    pass


def save_http_stream(url: str, outfile: IO[AnyStr], compression: str | None = None, **kwargs: Any) -> requests.Response:
    # TODO: we should really decompress stream on the fly or
    # (better) store it as is and decompress when reading.

    kwargs = kwargs.copy()
    kwargs.update(stream=True)

    response = do_http(url, **kwargs)

    if response.status_code == 304:
        raise NotModifiedException(response=response)

    # no compression, just save to output
    if compression is None:
        for chunk in response.iter_content(STREAM_CHUNK_SIZE):
            outfile.write(chunk)
        return response

    # read into temp file, then decompress into output
    with tempfile.NamedTemporaryFile() as temp:
        for chunk in response.iter_content(STREAM_CHUNK_SIZE):
            temp.write(chunk)

        temp.seek(0)

        with contextlib.ExitStack() as stack:
            class _BrotliDecompress:
                def read(self, size: int) -> bytes:
                    return cast(bytes, brotli.process(temp.read(size)))

            decompressor: gzip.GzipFile | lzma.LZMAFile | bz2.BZ2File | '_BrotliDecompress' | zstandard.ZstdDecompressionReader

            if compression == 'gz':
                decompressor = stack.enter_context(gzip.open(temp))
            elif compression == 'xz':
                decompressor = stack.enter_context(lzma.open(temp))
            elif compression == 'bz2':
                decompressor = stack.enter_context(bz2.open(temp))
            elif compression == 'br':
                decompressor = _BrotliDecompress()
            elif compression == 'zstd':
                decompressor = stack.enter_context(zstandard.ZstdDecompressor().stream_reader(temp))
            else:
                raise ValueError('Unsupported compression {}'.format(compression))

            while True:
                chunk = decompressor.read(STREAM_CHUNK_SIZE)
                if not chunk:
                    break
                outfile.write(chunk)  # type: ignore

    return response
