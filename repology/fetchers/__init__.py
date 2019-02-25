# Copyright (C) 2016-2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.atomic_fs import AtomicDir, AtomicFile
from repology.logger import NoopLogger


class Fetcher:
    pass


class PersistentDirFetcher(Fetcher):
    def do_fetch(self, statedir, logger):
        raise RuntimeError('pure virtual method called')

    def do_update(self, statedir, logger):
        raise RuntimeError('pure virtual method called')

    def fetch(self, statepath, update=True, logger=NoopLogger()):
        if not os.path.isdir(statepath):
            with AtomicDir(statepath) as statedir:
                self.do_fetch(statedir, logger)
        elif update:
            self.do_update(statepath, logger)
        else:
            logger.Log('no update requested, skipping')


class ScratchDirFetcher(Fetcher):
    def do_fetch(self, statedir, logger):
        raise RuntimeError('pure virtual method called')

    def fetch(self, statepath, update=True, logger=NoopLogger()):
        if os.path.isdir(statepath) and not update:
            logger.Log('no update requested, skipping')
            return

        with AtomicDir(statepath) as statedir:
            self.do_fetch(statedir, logger)


class ScratchFileFetcher(Fetcher):
    def __init__(self, binary=False):
        self.binary = binary

    def do_fetch(self, statefile, logger):
        raise RuntimeError('pure virtual method called')

    def fetch(self, statepath, update=True, logger=NoopLogger()):
        if os.path.isfile(statepath) and not update:
            logger.Log('no update requested, skipping')
            return

        args = {'mode': 'wb'} if self.binary else {'mode': 'w', 'encoding': 'utf-8'}

        with AtomicFile(statepath, **args) as statefile:
            self.do_fetch(statefile, logger)
