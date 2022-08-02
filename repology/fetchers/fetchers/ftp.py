# Copyright (C) 2018-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from urllib.parse import urlparse

from repology.atomic_fs import AtomicFile
from repology.fetchers import PersistentData, ScratchFileFetcher
from repology.logger import Logger


class FTPListFetcher(ScratchFileFetcher):
    def __init__(self, url: str, fetch_timeout: int = 60) -> None:
        super(FTPListFetcher, self).__init__()

        self.url = urlparse(url, scheme='ftp', allow_fragments=False)
        assert self.url.scheme == 'ftp'
        self.fetch_timeout = fetch_timeout

    def _do_fetch(self, statefile: AtomicFile, persdata: PersistentData, logger: Logger) -> bool:
        assert self.url.hostname is not None

        ftp = ftplib.FTP(
            host=self.url.hostname,
            user=self.url.username or '',
            passwd=self.url.password or '',
            timeout=self.fetch_timeout
        )

        ftp.login()

        ftp.cwd(self.url.path)

        ftp.retrlines('LIST', callback=lambda line: print(line, file=statefile.get_file()))

        ftp.quit()

        return True
