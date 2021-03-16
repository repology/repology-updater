# Copyright (C) 2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import fnmatch
import os
from typing import Optional

from repology.packagemaker import PackageMaker


__all__ = ['add_patch_files']


def add_patch_files(pkg: PackageMaker, path: str, pattern: Optional[str] = None) -> None:
    # skip symlinked directory - in most cases we can't construct links out of these
    if not os.path.isdir(path) or os.path.islink(path):
        return

    filenames = os.listdir(path)
    if pattern is not None:
        filenames = [fn for fn in filenames if fnmatch.fnmatch(fn, pattern)]

    if filenames:
        pkg.set_extra_field('patch', sorted(filenames))
