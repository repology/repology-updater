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

from repology.fetchers.helpers.fetch import Fetch
from repology.fetchers.helpers.state import StateDir
from repology.logger import NoopLogger


class CratesIOFetcher():
    def __init__(self, url, per_page=100):
        self.url = url
        self.per_page = per_page

    def Fetch(self, statepath, update=True, logger=NoopLogger()):
        if os.path.isdir(statepath) and not update:
            logger.Log('no update requested, skipping')
            return

        with StateDir(statepath) as statedir:
            numpage = 1
            while True:
                url = self.url + '?page={}&per_page={}&sort=alpha'.format(numpage, self.per_page)
                logger.Log('getting ' + url)

                text = Fetch(url, timeout=5).text
                with open(os.path.join(statedir, '{}.json'.format(numpage)), 'w', encoding='utf-8') as pagefile:
                    pagefile.write(text)

                # parse next page
                if not json.loads(text)['crates']:
                    logger.Log('last page detected')
                    return

                numpage += 1
