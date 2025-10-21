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

import os
import xml.etree.ElementTree

from repology.atomic_fs import AtomicDir
from repology.fetchers import PersistentData, ScratchDirFetcher
from repology.fetchers.http import PoliteHTTP
from repology.logger import Logger


class ChocolateyFetcher(ScratchDirFetcher):
    def __init__(self, url: str, fetch_timeout: int = 5, fetch_delay: int | None = None) -> None:
        self.url = url
        self.do_http = PoliteHTTP(timeout=fetch_timeout, delay=fetch_delay)

    def _do_fetch(self, statedir: AtomicDir, persdata: PersistentData, logger: Logger) -> bool:
        numpage = 0
        nextpageurl = self.url + 'Packages()?$filter=IsLatestVersion&$orderby=Id'
        while True:
            logger.log('getting ' + nextpageurl)

            text = self.do_http(nextpageurl).text
            with open(os.path.join(statedir.get_path(), '{}.xml'.format(numpage)), 'w', encoding='utf-8') as pagefile:
                pagefile.write(text)
                pagefile.flush()
                os.fsync(pagefile.fileno())

            # parse next page
            logger.log('parsing ' + nextpageurl)
            root = xml.etree.ElementTree.fromstring(text)

            next_link = root.find('{http://www.w3.org/2005/Atom}link[@rel="next"]')
            if next_link is None:
                break

            nextpageurl = next_link.attrib['href']
            numpage += 1

        return True
