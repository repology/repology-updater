# Copyright (C) 2024 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import json
import os
import time
from itertools import count

from repology.atomic_fs import AtomicDir
from repology.fetchers import PersistentData, ScratchDirFetcher
from repology.fetchers.http import PoliteHTTP
from repology.logger import Logger


class OpenVSXFetcher(ScratchDirFetcher):
    def __init__(self, url: str, page_size: int = 1000, fetch_timeout: int = 60, fetch_delay: int | None = None, max_tries: int = 5, retry_delay: int = 5) -> None:
        self.url = url
        self.page_size = page_size
        self.do_http = PoliteHTTP(timeout=fetch_timeout, delay=fetch_delay)
        self.max_tries = max_tries
        self.retry_delay = retry_delay

    def _do_fetch_retry(self, url: str, logger: Logger) -> str:
        num_try = 1
        while True:
            try:
                return self.do_http(url).text
            except ConnectionError as e:
                if num_try >= self.max_tries:
                    raise
                logger.log(f'failed to fetch {url}: {e}, retrying after delay...', Logger.ERROR)
                time.sleep(self.retry_delay)
                num_try += 1

    def _do_fetch(self, statedir: AtomicDir, persdata: PersistentData, logger: Logger) -> bool:
        page_counter = count()
        total_size: int | None = None
        num_fetched = 0
        offset = 0

        while True:
            url = f'{self.url}?offset={offset}&size={self.page_size}&sortBy=timestamp&sortOrder=asc'
            logger.log(f'fetching {url}')

            text = self._do_fetch_retry(url, logger)
            data = json.loads(text)

            if total_size is None:
                total_size = data['totalSize']
                logger.log(f'{total_size} extension(s) to fetch')

            extensions = data.get('extensions', [])
            if not extensions:
                break

            with open(os.path.join(statedir.get_path(), f'{next(page_counter)}.json'), 'w', encoding='utf-8') as pagefile:
                pagefile.write(text)
                pagefile.flush()
                os.fsync(pagefile.fileno())

            num_fetched += len(extensions)
            offset += self.page_size

            if offset >= total_size:
                break

        if total_size is not None and num_fetched != total_size:
            logger.log(f'fetched {num_fetched} extension(s), but API reported {total_size}', Logger.WARNING)

        logger.log(f'fetched {num_fetched} extension(s)')
        return True
