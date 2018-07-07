# Copyright (C) 2016-2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.fetchers import ScratchDirFetcher
from repology.fetchers.fetch import fetch


class ChocolateyFetcher(ScratchDirFetcher):
    def __init__(self, url, fetch_timeout=5):
        self.url = url
        self.fetch_timeout = fetch_timeout

    def do_fetch(self, statedir, logger):
        numpage = 0
        nextpageurl = self.url + 'Packages()?$filter=IsLatestVersion'
        while True:
            logger.Log('getting ' + nextpageurl)

            text = fetch(nextpageurl, timeout=self.fetch_timeout).text
            with open(os.path.join(statedir, '{}.xml'.format(numpage)), 'w', encoding='utf-8') as pagefile:
                pagefile.write(text)

            # parse next page
            logger.Log('parsing ' + nextpageurl)
            root = xml.etree.ElementTree.fromstring(text)

            next_link = root.find('{http://www.w3.org/2005/Atom}link[@rel="next"]')
            if next_link is None:
                break

            nextpageurl = next_link.attrib['href']
            numpage += 1
