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
import time
from typing import Dict, Optional

from repology.atomic_fs import AtomicFile
from repology.fetchers import PersistentData, ScratchFileFetcher
from repology.fetchers.http import NotModifiedException, save_http_stream
from repology.logger import Logger


class FileFetcher(ScratchFileFetcher):
    def __init__(self,
                 url: str,
                 compression: Optional[str] = None,
                 post: Optional[Dict[str, str]] = None,
                 headers: Optional[Dict[str, str]] = None,
                 nocache: bool = False,
                 fetch_timeout: Optional[int] = 60,
                 allow_zero_size: bool = True) -> None:
        super(FileFetcher, self).__init__(binary=True)

        self.url = url
        self.compression = compression
        self.post = post
        self.headers = headers
        self.fetch_timeout = fetch_timeout
        self.allow_zero_size = allow_zero_size

        # cache bypass
        if nocache:
            if '?' in self.url:
                self.url += '&nocache=' + str(int(time.time()))
            else:
                self.url += '?nocache=' + str(int(time.time()))

    def _do_fetch(self, statefile: AtomicFile, persdata: PersistentData, logger: Logger) -> bool:
        fetching_what = [self.url]
        headers = self.headers.copy() if self.headers else {}

        if isinstance(self.post, dict):
            fetching_what.append('{} fields of form data'.format(len(self.post)))

        if headers:
            fetching_what.append('{} extra headers'.format(len(headers)))

        logger.log('fetching ' + ', with '.join(fetching_what))

        if 'last-modified' in persdata:
            headers['if-modified-since'] = persdata['last-modified']
            logger.log('using if-modified-since: {}'.format(headers['if-modified-since']))

        try:
            response = save_http_stream(self.url, statefile.get_file(), compression=self.compression, data=self.post, headers=headers, timeout=self.fetch_timeout)
        except NotModifiedException:
            logger.log('got 403 not modified')
            return False

        size = os.path.getsize(statefile.get_path())

        logger.log('size is {} byte(s)'.format(size))

        if size == 0 and not self.allow_zero_size:
            raise RuntimeError('refusing zero size file')

        if response.headers.get('last-modified'):
            persdata['last-modified'] = response.headers['last-modified']
            logger.log('storing last-modified: {}'.format(persdata['last-modified']))

        return True
