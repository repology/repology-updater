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

import ftplib
import os
import urllib

from repology.fetchers.helpers.state import StateFile
from repology.logger import NoopLogger


class FTPListFetcher():
    def __init__(self, url, fetch_timeout=60):
        self.url = urllib.parse.urlparse(url, scheme='ftp', allow_fragments=False)
        assert(self.url.scheme == 'ftp')
        self.fetch_timeout = fetch_timeout

    def Fetch(self, statepath, update=True, logger=NoopLogger()):
        if os.path.isfile(statepath) and not update:
            logger.Log('no update requested, skipping')
            return

        ftp = ftplib.FTP(
            host=self.url.hostname,
            user=self.url.username or '',
            passwd=self.url.password or '',
            timeout=self.fetch_timeout
        )

        ftp.login()

        ftp.cwd(self.url.path)

        with StateFile(statepath, 'w') as statefile:
            ftp.retrlines('LIST', callback=lambda line: print(line, file=statefile))

        ftp.quit()
