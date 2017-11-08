# Copyright (C) 2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from contextlib import contextmanager


@contextmanager
def StateDir(path):
    new_path = path + '.new'
    old_path = path + '.old'

    def Cleanup():
        if os.path.exists(new_path):
            shutil.rmtree(new_path)
        if os.path.exists(old_path):
            shutil.rmtree(old_path)

    Cleanup()

    os.mkdir(new_path)

    try:
        yield new_path
        if os.path.exists(path):
            os.rename(path, old_path)
        os.rename(new_path, path)
    finally:
        Cleanup()


@contextmanager
def StateFile(path, *args, **kwargs):
    new_path = path + '.new'

    def Cleanup():
        if os.path.exists(new_path):
            os.remove(new_path)

    Cleanup()

    statefile = open(new_path, *args, **kwargs)

    try:
        with open(new_path, *args, **kwargs) as statefile:
            yield statefile
        os.replace(new_path, path)
    finally:
        Cleanup()
