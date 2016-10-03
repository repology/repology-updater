# Copyright (C) 2016 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
import json
import shutil

from repology.logger import NoopLogger
from repology.www import Get

def LoadSpec(package, statepath, logger):
    specurl = "http://pkgs.fedoraproject.org/cgit/rpms/%s.git/plain/%s.spec" % (package, package)

    logger.Log("  getting spec from {}".format(specurl))

    r = Get(specurl, check_status = False)
    if r.status_code != 200:
        logger.Log("    failed: {}".format(r.status_code)) # XXX: check .dead.package, instead throw
        return

    with open(os.path.join(statepath, package + ".spec"), "wb") as file:
        file.write(r.content)

def ParsePackages(statepath, logger):
    page = 1

    while True:
        pageurl = "https://admin.fedoraproject.org/pkgdb/api/packages/?page={}".format(page)
        logger.Log("getting page {} from {}".format(page, pageurl))
        pagedata = json.loads(Get(pageurl).text)

        for package in pagedata['packages']:
            LoadSpec(package['name'], statepath, logger)

        page += 1

        if page > pagedata['page_total']:
            break

class FedoraFetcher():
    def __init__(self):
        pass

    def Fetch(self, statepath, update = True, logger = NoopLogger()):
        if os.path.isdir(statepath) and not update:
            return

        if os.path.isdir(statepath):
            shutil.rmtree(statepath)

        os.mkdir(statepath)

        try:
            ParsePackages(statepath, logger)
        except:
            # don't leave partial state
            shutil.rmtree(statepath)
            raise
