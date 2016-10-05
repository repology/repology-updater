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
import gzip
import bz2
import lzma

from repology.logger import NoopLogger
from repology.www import Get


class FileFetcher():
    def __init__(self, *sources, gz=False, bz2=False, xz=False):
        self.sources = sources
        self.gz = gz
        self.bz2 = bz2
        self.xz = xz

    def DoFetch(self, statepath, update, logger):
        with open(statepath, "wb") as statefile:
            for source in self.sources:
                logger.Log("fetching " + source)
                data = Get(source).content

                if self.gz:
                    logger.Log("  decompressing with gzip")
                    data = gzip.decompress(data)
                elif self.bz2:
                    logger.Log("  decompressing with bz2")
                    data = bz2.decompress(data)
                elif self.xz:
                    logger.Log("  decompressing with xz")
                    data = lzma.LZMADecompressor().decompress(data)

                logger.Log("  saving")
                statefile.write(data)

    def Fetch(self, statepath, update=True, logger=NoopLogger()):
        if os.path.isfile(statepath) and not update:
            return

        try:
            self.DoFetch(statepath, update, logger)
        except:
            if os.path.exists(statepath):
                os.remove(statepath)
            raise
