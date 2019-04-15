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
import pickle
from abc import ABC, abstractmethod
from typing import Any, Dict

from repology.atomic_fs import AtomicDir, AtomicFile
from repology.logger import Logger, NoopLogger


PersistentData = Dict[str, str]


class Fetcher(ABC):
    @abstractmethod
    def fetch(self, statepath: str, update: bool = True, logger: Logger = NoopLogger()) -> bool:
        pass


class PersistentDirFetcher(Fetcher):
    @abstractmethod
    def _do_fetch(self, statepath: str, logger: Logger) -> bool:
        pass

    @abstractmethod
    def _do_update(self, statepath: str, logger: Logger) -> bool:
        pass

    def fetch(self, statepath: str, update: bool = True, logger: Logger = NoopLogger()) -> bool:
        if not os.path.isdir(statepath):
            with AtomicDir(statepath) as statedir:
                return self._do_fetch(statedir.get_path(), logger)
        elif update:
            return self._do_update(statepath, logger)
        else:
            logger.log('no update requested, skipping')
            return False


class ScratchDirFetcher(Fetcher):
    @abstractmethod
    def _do_fetch(self, statedir: AtomicDir, persdata: PersistentData, logger: Logger) -> bool:
        pass

    def fetch(self, statepath: str, update: bool = True, logger: Logger = NoopLogger()) -> bool:
        if os.path.isdir(statepath) and not update:
            logger.log('no update requested, skipping')
            return False

        persdata: Dict[str, Any] = {}

        perspath = statepath + '.persdata'

        try:
            with open(perspath, 'rb') as rpersfile:
                persdata = pickle.load(rpersfile)
        except (EOFError, FileNotFoundError, pickle.UnpicklingError):
            pass

        with AtomicDir(statepath) as statedir:
            have_changes = self._do_fetch(statedir, persdata, logger)

            if persdata:
                with AtomicFile(perspath, 'wb') as wpersfile:
                    pickle.dump(persdata, wpersfile.get_file())
                    wpersfile.get_file().flush()
                    os.fsync(wpersfile.get_file().fileno())

            if not have_changes:
                statedir.cancel()

            return have_changes


class ScratchFileFetcher(Fetcher):
    def __init__(self, binary: bool = False):
        self.binary = binary

    @abstractmethod
    def _do_fetch(self, statefile: AtomicFile, persdata: PersistentData, logger: Logger) -> bool:
        pass

    def fetch(self, statepath: str, update: bool = True, logger: Logger = NoopLogger()) -> bool:
        if os.path.isfile(statepath) and not update:
            logger.log('no update requested, skipping')
            return False

        args = {'mode': 'wb'} if self.binary else {'mode': 'w', 'encoding': 'utf-8'}

        persdata: Dict[str, Any] = {}

        perspath = statepath + '.persdata'

        try:
            with open(perspath, 'rb') as rpersfile:
                persdata = pickle.load(rpersfile)
        except (EOFError, FileNotFoundError, pickle.UnpicklingError):
            pass

        with AtomicFile(statepath, **args) as statefile:
            have_changes = self._do_fetch(statefile, persdata, logger)

            if persdata:
                with AtomicFile(perspath, 'wb') as wpersfile:
                    pickle.dump(persdata, wpersfile.get_file())
                    wpersfile.get_file().flush()
                    os.fsync(wpersfile.get_file().fileno())

            if not have_changes:
                statefile.cancel()

            statefile.get_file().flush()
            os.fsync(statefile.get_file().fileno())

            return have_changes
