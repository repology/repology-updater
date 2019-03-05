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
from abc import ABC, abstractmethod


__all__ = ['AtomicDir', 'AtomicFile']


class _AtomicFSObject(ABC):
    def __init__(self, path):
        self.path = path
        self.canceled = False

    def _get_new_path(self):
        return self.path + '.new'

    def _get_old_path(self):
        return self.path + '.old'

    def _cleanup(self):
        for path in [self._get_new_path(), self._get_old_path()]:
            if os.path.isdir(path):
                shutil.rmtree(path)
            elif os.path.exists(path):
                os.remove(path)

    def _replace(self):
        if not os.path.exists(self._get_new_path()):
            raise RuntimeError('no now state')

        # assuming old path was already cleaned up
        if os.path.exists(self.path):
            os.rename(self.path, self._get_old_path())

        os.rename(self._get_new_path(), self.path)

    def cancel(self):
        self.canceled = True

    @abstractmethod
    def _open(self):
        pass

    def _close(self):
        pass

    def __enter__(self):
        self._cleanup()

        return self._open()

    def __exit__(self, exc_type, exc_value, traceback):
        self._close()

        if not exc_type and not self.canceled:
            self._replace()

        self._cleanup()


class AtomicDir(_AtomicFSObject):
    def __init__(self, path):
        super(AtomicDir, self).__init__(path)

    def _open(self):
        os.mkdir(self._get_new_path())

        class _StrWrapper(str):
            def cancel(self_):
                self.cancel()

        return _StrWrapper(self._get_new_path())


class AtomicFile(_AtomicFSObject):
    def __init__(self, path, *args, **kwargs):
        super(AtomicFile, self).__init__(path)
        self.args = args
        self.kwargs = kwargs

    def _open(self):
        self.file = open(self._get_new_path(), *self.args, **self.kwargs)
        self.file.cancel = self.cancel
        return self.file

    def _close(self):
        self.file.close()
