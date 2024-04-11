# Copyright (C) 2017-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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


class CratesIOFetcher(ScratchDirFetcher):
    def __init__(self, url: str, per_page: int = 100, fetch_timeout: int = 5, fetch_delay: int | None = None, max_tries: int = 5, retry_delay: int = 5):
        self.url = url
        self.per_page = per_page
        self.do_http = PoliteHTTP(timeout=fetch_timeout, delay=fetch_delay)
        self.max_tries = max_tries
        self.retry_delay = retry_delay

    def _do_fetch_retry(self, url: str, logger: Logger) -> str:
        num_try = 1
        while True:
            logger.log(f'getting {url}' if num_try == 1 else f'getting {url} (try #{num_try})')

            try:
                return self.do_http(url).text
            except ConnectionError as e:
                if num_try >= self.max_tries:
                    raise
                else:
                    logger.log(f'failed to fetch {url}: {str(e)}, retrying after delay...', Logger.ERROR)
                    time.sleep(self.retry_delay)
                    num_try += 1

    def _do_fetch(self, statedir: AtomicDir, persdata: PersistentData, logger: Logger) -> bool:
        page_counter = count()
        query = '?per_page={}&sort=alpha'.format(self.per_page)
        while query:
            url = self.url + query
            #logger.log('getting ' + url)

            text = self._do_fetch_retry(url, logger)
            with open(os.path.join(statedir.get_path(), '{}.json'.format(next(page_counter))), 'w', encoding='utf-8') as pagefile:
                pagefile.write(text)
                pagefile.flush()
                os.fsync(pagefile.fileno())

            # parse next page
            query = json.loads(text)['meta']['next_page']

        logger.log('last page detected')
        return True
