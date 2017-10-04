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
import urllib

from repology.fetchers.helpers.fetch import Fetch
from repology.fetchers.helpers.state import StateDir
from repology.logger import NoopLogger


class AURFetcher():
    def __init__(self, url):
        self.url = url

    def Fetch(self, statepath, update=True, logger=NoopLogger()):
        if os.path.isdir(statepath) and not update:
            logger.Log('no update requested, skipping')
            return

        with StateDir(statepath) as statedir:
            packages_url = self.url + 'packages.gz'
            logger.GetIndented().Log('fetching package list from ' + packages_url)
            data = Fetch(packages_url).text  # autogunzipped?

            package_names = []

            for line in data.split('\n'):
                line = line.strip()
                if line.startswith('#') or line == '':
                    continue
                package_names.append(line)

            logger.GetIndented().Log('{} package name(s) parsed'.format(len(package_names)))

            pagesize = 100

            for page in range(0, len(package_names) // pagesize + 1):
                ifrom = page * pagesize
                ito = (page + 1) * pagesize
                url = '&'.join(['arg[]=' + urllib.parse.quote(name) for name in package_names[ifrom:ito]])
                url = self.url + '/rpc/?v=5&type=info&' + url

                logger.GetIndented().Log('fetching page {}/{}'.format(page + 1, len(package_names) // pagesize + 1))

                with open(os.path.join(statedir, '{}.json'.format(page)), 'wb') as statefile:
                    statefile.write(Fetch(url, timeout=5).content)
