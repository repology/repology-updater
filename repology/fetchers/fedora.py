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

import json
import os
import shutil

from repology.fetchers.helpers.fetch import Fetch
from repology.fetchers.helpers.state import StateDir
from repology.logger import NoopLogger


class FedoraFetcher():
    def __init__(self, apiurl, giturl):
        self.apiurl = apiurl
        self.giturl = giturl
        pass

    def LoadSpec(self, package, statedir, logger):
        specurl = self.giturl + '/{0}.git/plain/{0}.spec'.format(package)

        logger.GetIndented().Log('getting spec from {}'.format(specurl))

        r = Fetch(specurl, check_status=False)
        if r.status_code != 200:
            deadurl = self.giturl + '/{0}.git/plain/dead.package'.format(package)
            dr = Fetch(deadurl, check_status=False)
            if dr.status_code == 200:
                logger.GetIndented(2).Log('dead: ' + ';'.join(dr.text.split('\n')))
            else:
                logger.GetIndented(2).Log('failed: {}'.format(r.status_code))  # XXX: check .dead.package, instead throw
            return

        with open(os.path.join(statedir, package + '.spec'), 'wb') as file:
            file.write(r.content)

    def Fetch(self, statepath, update=True, logger=NoopLogger()):
        if os.path.isdir(statepath) and not update:
            logger.Log('no update requested, skipping')
            return

        with StateDir(statepath) as statedir:
            page = 1

            while True:
                pageurl = self.apiurl + 'packages/?page={}'.format(page)
                logger.Log('getting page {} from {}'.format(page, pageurl))
                pagedata = json.loads(Fetch(pageurl).text)

                for package in pagedata['packages']:
                    self.LoadSpec(package['name'], statedir, logger)

                page += 1

                if page > pagedata['page_total']:
                    break
