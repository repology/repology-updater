# Copyright (C) 2019-2026 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from functools import cmp_to_key
from typing import Iterable

from libversion import version_compare

from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.json import iter_json_dict
from repology.parsers.versions import VersionStripper


class LuaRocksParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        normalize_version = VersionStripper().strip_right('-')

        for pkgname, pkgversions in iter_json_dict(path, ('repository', None)):
            with factory.begin(pkgname) as pkg:
                pkg.add_name(pkgname, NameType.LUAROCKS_NAME)
                # there are also a few cases of `scm`, `main`, `master` versions which
                # we could include in addition to normal versions as ROLLING, but I
                # don't see much gain from it
                version = max(pkgversions.keys(), key=cmp_to_key(version_compare))
                pkg.set_version(version, normalize_version)
                yield pkg
