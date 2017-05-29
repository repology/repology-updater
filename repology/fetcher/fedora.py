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

from repology.logger import NoopLogger
from repology.www import Get


class FedoraFetcher():
    def __init__(self, apiurl, giturl):
        self.apiurl = apiurl
        self.giturl = giturl
        pass

    def LoadSpec(self, package, statepath, logger):
        specurl = self.giturl + '/{0}.git/plain/{0}.spec'.format(package)

        logger.GetIndented().Log('getting spec from {}'.format(specurl))

        r = Get(specurl, check_status=False)
        if r.status_code != 200:
            deadurl = self.giturl + '/{0}.git/plain/dead.package'.format(package)
            dr = Get(deadurl, check_status=False)
            if dr.status_code == 200:
                logger.GetIndented(2).Log('dead: ' + ';'.join(dr.text.split('\n')))
            else:
                logger.GetIndented(2).Log('failed: {}'.format(r.status_code))  # XXX: check .dead.package, instead throw
            return

        with open(os.path.join(statepath, package + '.spec'), 'wb') as file:
            file.write(r.content)

    def ParsePackages(self, statepath, logger):
        page = 1

        while True:
            pageurl = self.apiurl + 'packages/?page={}'.format(page)
            logger.Log('getting page {} from {}'.format(page, pageurl))
            pagedata = json.loads(Get(pageurl).text)

            for package in pagedata['packages']:
                self.LoadSpec(package['name'], statepath, logger)

            page += 1

            if page > pagedata['page_total']:
                break

    def Fetch(self, statepath, update=True, logger=NoopLogger()):
        if os.path.isdir(statepath) and not update:
            logger.Log('no update requested, skipping')
            return

        if os.path.exists(statepath):
            shutil.rmtree(statepath)

        os.mkdir(statepath)

        try:
            self.ParsePackages(statepath, logger)
        except:
            if os.path.exists(statepath):
                shutil.rmtree(statepath)
            raise
