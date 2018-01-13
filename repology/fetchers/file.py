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

import bz2
import gzip
import lzma
import os

from repology.fetchers.helpers.fetch import Fetch
from repology.fetchers.helpers.state import StateFile
from repology.logger import NoopLogger


class FileFetcher():
    def __init__(self, url, compression=None, post=None, headers=None):
        self.url = url
        self.compression = compression
        self.post = post
        self.headers = headers

    def Fetch(self, statepath, update=True, logger=NoopLogger()):
        if os.path.isfile(statepath) and not update:
            logger.Log('no update requested, skipping')
            return

        fetching_what = [self.url]
        if isinstance(self.post, dict):
            fetching_what.append('{} fields of form data'.format(len(self.post)))
        elif self.post:
            fetching_what.append('{} bytes of post data'.format(len(self.post)))

        if self.headers:
            fetching_what.append('{} extra headers'.format(len(self.headers)))

        logger.Log('fetching ' + ', with '.join(fetching_what))

        data = Fetch(self.url, post=self.post, headers=self.headers).content

        logger.GetIndented().Log('size is {} byte(s)'.format(len(data)))

        if self.compression == 'gz':
            logger.GetIndented().Log('decompressing with gzip')
            data = gzip.decompress(data)
        elif self.compression == 'bz2':
            logger.GetIndented().Log('decompressing with bz2')
            data = bz2.decompress(data)
        elif self.compression == 'xz':
            logger.GetIndented().Log('decompressing with xz')
            data = lzma.LZMADecompressor().decompress(data)

        if self.compression:
            logger.GetIndented().Log('size after decompression is {} byte(s)'.format(len(data)))

        logger.GetIndented().Log('saving')

        with StateFile(statepath, 'wb') as statefile:
            statefile.write(data)
