# Copyright (C) 2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.fetchers.helpers.state import StateDir
from repology.logger import NoopLogger
from repology.subprocess import RunSubprocess


class SVNFetcher():
    def __init__(self, url, fetch_timeout=600):
        self.url = url
        self.fetch_timeout = fetch_timeout

    def Fetch(self, statepath, update=True, logger=NoopLogger()):
        if not os.path.isdir(statepath):
            with StateDir(statepath) as statedir:
                RunSubprocess(['timeout', str(self.fetch_timeout), 'svn', 'checkout', self.url, statedir], logger=logger)
        elif update:
            RunSubprocess(['timeout', str(self.fetch_timeout), 'svn', 'up', statepath], logger=logger)
        else:
            logger.Log('no update requested, skipping')
