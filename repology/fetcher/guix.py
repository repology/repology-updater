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

from repology.logger import NoopLogger
from repology.www import Get


class GuixFetcher():
    def __init__(self, url):
        self.url = url

    def DoFetch(self, statepath, update, logger):
        pages = [chr(x) for x in range(ord('a'), ord('z') + 1)]  # a..z
        pages.append('0-9')

        for page in pages:
            logger.Log('fetching page ' + page)
            pageurl = self.url + '/' + page + '.html'
            with open(os.path.join(statepath, page + '.html'), 'w', encoding='utf-8') as pagefile:
                pagefile.write(Get(pageurl).text)

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
