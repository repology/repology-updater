# Copyright (C) 2017-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
import shutil
from typing import Any, Dict, IO, Tuple


__all__ = ['AtomicDir', 'AtomicFile']


class _AtomicFSObject:
    def __init__(self, path: str) -> None:
        self.path = path
        self.canceled = False

    def _get_new_path(self) -> str:
        return self.path + '.new'

    def _get_old_path(self) -> str:
        return self.path + '.old'

    def _cleanup(self) -> None:
        for path in [self._get_new_path(), self._get_old_path()]:
            if os.path.isdir(path):
                shutil.rmtree(path)
            elif os.path.exists(path):
                os.remove(path)

    def _replace(self) -> None:
        if not os.path.exists(self._get_new_path()):
            raise RuntimeError('no now state')

        # assuming old path was already cleaned up
        if os.path.exists(self.path):
            os.rename(self.path, self._get_old_path())

        os.rename(self._get_new_path(), self.path)

    def get_path(self) -> str:
        return self._get_new_path()

    def cancel(self) -> None:
        self.canceled = True


class AtomicDir(_AtomicFSObject):
    def __init__(self, path: str) -> None:
        super(AtomicDir, self).__init__(path)

    def __enter__(self) -> 'AtomicDir':
        self._cleanup()
        os.mkdir(self._get_new_path())
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        if not exc_type and not self.canceled:
            self._replace()

        self._cleanup()


class AtomicFile(_AtomicFSObject):
    _args: Tuple[Any, ...]
    _kwargs: Dict[str, Any]
    _file: IO[Any]

    def __init__(self, path: str, *args: Any, **kwargs: Any) -> None:
        super(AtomicFile, self).__init__(path)
        self._args = args
        self._kwargs = kwargs

    def __enter__(self) -> 'AtomicFile':
        self._cleanup()
        self._file = open(self._get_new_path(), *self._args, **self._kwargs)
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self._file.close()

        if not exc_type and not self.canceled:
            self._replace()

        self._cleanup()

    def get_file(self) -> IO[Any]:
        return self._file
