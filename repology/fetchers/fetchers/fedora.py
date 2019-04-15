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

import json
import os

from repology.atomic_fs import AtomicDir
from repology.fetchers import PersistentData, ScratchDirFetcher
from repology.fetchers.http import do_http
from repology.logger import Logger


class FedoraFetcher(ScratchDirFetcher):
    def __init__(self, apiurl: str, giturl: str) -> None:
        self.apiurl = apiurl
        self.giturl = giturl

    def _load_spec(self, package: str, statedir: AtomicDir, logger: Logger) -> None:
        specurl = self.giturl + '/{0}.git/plain/{0}.spec'.format(package)

        logger.get_indented().log('getting spec from {}'.format(specurl))

        r = do_http(specurl, check_status=False)
        if r.status_code != 200:
            deadurl = self.giturl + '/{0}.git/plain/dead.package'.format(package)
            dr = do_http(deadurl, check_status=False)
            if dr.status_code == 200:
                logger.get_indented(2).log('dead: ' + ';'.join(dr.text.split('\n')))
            else:
                logger.get_indented(2).log('failed: {}'.format(r.status_code))  # XXX: check .dead.package, instead throw
            return

        with open(os.path.join(statedir.get_path(), package + '.spec'), 'wb') as specfile:
            specfile.write(r.content)
            specfile.flush()
            os.fsync(specfile.fileno())

    def _do_fetch(self, statedir: AtomicDir, persdata: PersistentData, logger: Logger) -> bool:
        page = 1

        while True:
            pageurl = self.apiurl + 'packages/?page={}'.format(page)
            logger.log('getting page {} from {}'.format(page, pageurl))
            pagedata = json.loads(do_http(pageurl).text)

            for package in pagedata['packages']:
                self._load_spec(package['name'], statedir, logger)

            page += 1

            if page > pagedata['page_total']:
                break

        return True
