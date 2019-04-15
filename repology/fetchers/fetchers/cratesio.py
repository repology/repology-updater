# Copyright (C) 2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.atomic_fs import AtomicDir
from repology.fetchers import PersistentData, ScratchDirFetcher
from repology.fetchers.http import PoliteHTTP
from repology.logger import Logger


class CratesIOFetcher(ScratchDirFetcher):
    def __init__(self, url, per_page=100, fetch_timeout=5, fetch_delay=None):
        self.url = url
        self.per_page = per_page
        self.do_http = PoliteHTTP(timeout=fetch_timeout, delay=fetch_delay)

    def _do_fetch(self, statedir: AtomicDir, persdata: PersistentData, logger: Logger) -> bool:
        numpage = 1
        while True:
            url = self.url + '?page={}&per_page={}&sort=alpha'.format(numpage, self.per_page)
            logger.log('getting ' + url)

            text = self.do_http(url).text
            with open(os.path.join(statedir.get_path(), '{}.json'.format(numpage)), 'w', encoding='utf-8') as pagefile:
                pagefile.write(text)
                pagefile.flush()
                os.fsync(pagefile.fileno())

            # parse next page
            if not json.loads(text)['crates']:
                logger.log('last page detected')
                return True

            numpage += 1
