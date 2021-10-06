# Copyright (C) 2020 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from typing import Iterable

from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.json import iter_json_dict
from repology.parsers.versions import VersionStripper


class MportsJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        normalize_version = VersionStripper().strip_right(',').strip_right('_')

        for pkgname, pkgdata in iter_json_dict(path, ('packages', None)):
            with factory.begin() as pkg:
                pkg.add_name(pkgname, NameType.BSD_PKGNAME)
                pkg.add_name(pkgdata['port'], NameType.BSD_ORIGIN)
                pkg.set_version(pkgdata['version'], normalize_version)
                pkg.set_summary(pkgdata['summary'])

                pkg.add_categories(item['category'] for item in pkgdata['categories'])
                pkg.add_licenses(pkgdata['licenses'])
                pkg.add_homepages(pkgdata['homepages'])
                yield pkg
