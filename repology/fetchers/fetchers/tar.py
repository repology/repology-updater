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

import os

from repology.atomic_fs import AtomicDir
from repology.fetchers import PersistentData, ScratchDirFetcher
from repology.fetchers.http import NotModifiedException, save_http_stream
from repology.logger import Logger
from repology.subprocess import run_subprocess


class TarFetcher(ScratchDirFetcher):
    def __init__(self, url: str, fetch_timeout: int = 60) -> None:
        self.url = url
        self.fetch_timeout = fetch_timeout

    def _do_fetch(self, statedir: AtomicDir, persdata: PersistentData, logger: Logger) -> bool:
        tarpath = os.path.join(statedir.get_path(), '.temporary.tar')

        headers = {}

        if persdata.get('last-modified'):
            headers['if-modified-since'] = persdata.get('last-modified')
            logger.log('using if-modified-since: {}'.format(headers['if-modified-since']))

        logger.log('fetching {}'.format(self.url))

        try:
            with open(tarpath, 'wb') as tarfile:
                response = save_http_stream(self.url, tarfile, headers=headers, timeout=self.fetch_timeout)
        except NotModifiedException:
            logger.log('got 403 not modified')
            return False

        # XXX: may be unportable, FreeBSD tar automatically handles compression type,
        # may not be the case on linuxes
        run_subprocess(['tar', '-x', '-z', '-f', tarpath, '-C', statedir.get_path()], logger)
        os.remove(tarpath)

        if response.headers.get('last-modified'):
            persdata['last-modified'] = response.headers['last-modified']
            logger.log('storing last-modified: {}'.format(persdata['last-modified']))

        return True
