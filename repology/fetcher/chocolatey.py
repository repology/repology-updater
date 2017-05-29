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
import shutil
import xml.etree.ElementTree

from repology.logger import NoopLogger
from repology.www import Get


class ChocolateyFetcher():
    def __init__(self, url):
        self.url = url

    def DoFetch(self, statepath, update, logger):
        numpage = 0
        nextpageurl = self.url + 'Packages()?$filter=IsLatestVersion'
        while True:
            logger.Log('getting ' + nextpageurl)

            text = Get(nextpageurl).text
            with open(os.path.join(statepath, '{}.xml'.format(numpage)), 'w', encoding='utf-8') as pagefile:
                pagefile.write(text)

            # parse next page
            logger.Log('parsing ' + nextpageurl)
            root = xml.etree.ElementTree.fromstring(text)

            next_link = root.find('{http://www.w3.org/2005/Atom}link[@rel="next"]')
            if next_link is None:
                break

            nextpageurl = next_link.attrib['href']
            numpage += 1

    def Fetch(self, statepath, update=True, logger=NoopLogger()):
        if os.path.isdir(statepath) and not update:
            logger.Log('no update requested, skipping')
            return

        if os.path.exists(statepath):
            shutil.rmtree(statepath)

        os.mkdir(statepath)

        try:
            self.DoFetch(statepath, update, logger)
        except:
            if os.path.exists(statepath):
                shutil.rmtree(statepath)
            raise
